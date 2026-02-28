import json
import logging
import re
import time
from pathlib import Path
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, field_validator
from langchain_openai import ChatOpenAI

from app.rag.core.data_ingestion import DataEmbedding
from app.rag.core.vectorstore import VectorStore
from app.rag.core.rag_pipeline import MultiModalRAG
from app.rag.core.rag_manager import MultiModalRAGSystem
from app.rag.core.config import LLMConfig, AppConfig
from app.rag.agent.graph_builder import run_agentic_rag, stream_agentic_rag
from app.rag.core.database import (
    init_db,
    save_document,
    get_all_documents,
    save_query_log,
    get_eval_summary,
    get_recent_logs,
)
from app.rag.core.storage import save_index, load_index

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Prompt injection guard (compiled once at module load)
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS = re.compile(
    r"ignore\s+(previous|above|all)?\s*instructions?"
    r"|forget\s+(what|everything)"
    r"|disregard\s+(all|previous|above)?\s*instructions?"
    r"|you\s+are\s+now\b"
    r"|act\s+as\b"
    r"|pretend\s+(you\s+are|to\s+be)"
    r"|system\s+prompt"
    r"|your\s+(true|real|actual)\s+purpose"
    r"|\bDAN\b"
    r"|developer\s+mode"
    r"|jailbreak"
    r"|\[INST\]|\[SYS\]|<\||\|>"
    r"|-{5,}|={5,}",
    re.IGNORECASE,
)


class Query(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def no_injection(cls, v: str) -> str:
        if len(v) > 2000:
            raise ValueError("Question exceeds maximum length of 2000 characters")
        if _INJECTION_PATTERNS.search(v):
            raise ValueError("Question contains disallowed patterns")
        return v


# ---------------------------------------------------------------------------
# Query logging
# ---------------------------------------------------------------------------

def _log_query(query: str, result: dict, latency_ms: float, document_id=None):
    """Emit a structured JSON log line and persist to SQLite."""
    rejected = result.get("answer", "").startswith(
        "I don't have enough information"
    )
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "query": query,
        "answer_length": len(result.get("answer", "")),
        "num_text_chunks": result.get("num_text_chunks", 0),
        "num_images": result.get("num_images", 0),
        "top_similarity": result.get("top_similarity", 0.0),
        "confidence": result.get("confidence", 0.0),
        "answer_source_similarity": result.get("answer_source_similarity", 0.0),
        "is_hallucination": result.get("is_hallucination", False),
        "rejected": rejected,
        "source_pages": [s["page"] for s in result.get("sources", [])],
        "latency_ms": round(latency_ms, 1),
    }
    logger.info(f"QUERY_LOG {json.dumps(entry)}")
    try:
        save_query_log(document_id, entry)
    except Exception as e:
        logger.warning(f"Failed to persist query log: {e}")


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Lifeforge RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=AppConfig.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI Chat model from config
llm = ChatOpenAI(model=LLMConfig.LLM_MODEL, temperature=LLMConfig.LLM_TEMPERATURE)

# In-memory RAG state (standard / non-agentic path)
vectorstore = None
bm25_retriever = None
image_data_store = {}
current_doc_id = None          # SQLite document id for /query logs

# Agentic RAG System (singleton)
agentic_rag_system = MultiModalRAGSystem()
current_agentic_doc_id = None  # SQLite document id for /query-agentic logs


# ---------------------------------------------------------------------------
# Startup — restore persisted indices
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    global vectorstore, bm25_retriever, image_data_store, current_doc_id
    global current_agentic_doc_id

    init_db()

    # Restore standard index
    loaded = load_index("standard")
    if loaded:
        vectorstore      = loaded["faiss_store"]
        bm25_retriever   = loaded["bm25_retriever"]
        image_data_store = loaded["image_data_store"]
        logger.info("Restored standard index from disk.")

    # Restore agentic index into the singleton
    agentic_loaded = load_index("agentic")
    if agentic_loaded:
        ras = agentic_rag_system
        ras.vectorStore      = agentic_loaded["faiss_store"]
        ras.bm25_retriever   = agentic_loaded["bm25_retriever"]
        ras.image_data_store = agentic_loaded["image_data_store"]
        ras.vision_llm       = llm
        ras.all_docs         = list(ras.vectorStore.docstore._dict.values())
        ras.text_docs        = [d for d in ras.all_docs if d.metadata.get("type") == "text"]
        ras.all_embeddings   = []
        ras._initialized     = True
        logger.info("Restored agentic index from disk.")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/ping")
def ping():
    return {"message": "pong"}


# ---------------------------------------------------------------------------
# Standard ingest + query
# ---------------------------------------------------------------------------

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """Ingest a PDF into the standard (non-agentic) RAG system."""
    global vectorstore, bm25_retriever, image_data_store, current_doc_id

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    temp_dir = Path(AppConfig.TEMP_DIR)
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / file.filename

    try:
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"[ingest] Saved upload to {temp_file} ({temp_file.stat().st_size} bytes)")

        logger.info("[ingest] Starting PDF processing and embedding...")
        data_embedder = DataEmbedding(str(temp_file))
        docs, embeddings, img_store, text_docs = data_embedder.process_and_embedd_docs()
        logger.info(
            f"[ingest] Embedding complete: {len(docs)} docs, "
            f"{len(embeddings)} embeddings, {len(img_store)} images, "
            f"{len(text_docs)} text chunks"
        )

        logger.info("[ingest] Creating vector store and BM25 retriever...")
        vs = VectorStore(
            all_docs=docs,
            all_embeddings=embeddings,
            image_data_store=img_store,
            text_docs=text_docs,
        )
        hybrid_stores = vs.create_hybrid_retrievers()
        vectorstore      = hybrid_stores["faiss_store"]
        bm25_retriever   = hybrid_stores["bm25_retriever"]
        image_data_store = hybrid_stores["image_data_store"]
        logger.info("[ingest] Vector store created successfully")

        # Persist to disk
        logger.info("[ingest] Saving index to disk...")
        save_index(vectorstore, image_data_store, "standard")
        logger.info("[ingest] Saving document record to SQLite...")
        current_doc_id = save_document(
            "standard", file.filename, len(text_docs), len(image_data_store)
        )
        logger.info(f"[ingest] Document saved with id={current_doc_id}")

        return JSONResponse(
            content={"message": f"Successfully processed {file.filename}"},
            status_code=200,
        )

    except Exception as e:
        logger.exception(f"[ingest] Failed to ingest {file.filename}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_file.exists():
            temp_file.unlink()
        file.file.close()


@app.post("/query")
async def query_documents(query: Query):
    """Query the standard RAG system."""
    global vectorstore, bm25_retriever, image_data_store, current_doc_id

    if not vectorstore:
        raise HTTPException(
            status_code=400,
            detail="No documents have been ingested. Please ingest documents first.",
        )

    try:
        rag = MultiModalRAG(
            query=query.question,
            vectorStore=vectorstore,
            image_data_store=image_data_store,
            llm=llm,
            k=5,
            bm25_retriever=bm25_retriever,
        )
        t0 = time.perf_counter()
        result = rag.generate()
        latency_ms = (time.perf_counter() - t0) * 1000
        _log_query(query.question, result, latency_ms, document_id=current_doc_id)

        return JSONResponse(
            content={
                "answer": result["answer"],
                "sources": result["sources"],
                "num_images": result["num_images"],
                "num_text_chunks": result["num_text_chunks"],
                "confidence": result.get("confidence", 0.0),
                "top_similarity": result.get("top_similarity", 0.0),
                "answer_source_similarity": result.get("answer_source_similarity", 0.0),
                "is_hallucination": result.get("is_hallucination", False),
            },
            status_code=200,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Agentic ingest + query
# ---------------------------------------------------------------------------

@app.post("/ingest-agentic")
async def ingest_document_agentic(file: UploadFile = File(...)):
    """Ingest a PDF into the agentic RAG system."""
    global current_agentic_doc_id

    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    temp_dir = Path(AppConfig.TEMP_DIR)
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / file.filename

    try:
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"[ingest-agentic] Saved upload to {temp_file} ({temp_file.stat().st_size} bytes)")

        logger.info("[ingest-agentic] Initializing agentic RAG system...")
        agentic_rag_system.initialize(pdf_path=str(temp_file), vision_llm=llm)
        logger.info("[ingest-agentic] Agentic RAG initialized successfully")

        # Persist to disk
        logger.info("[ingest-agentic] Saving index to disk...")
        save_index(
            agentic_rag_system.vectorStore,
            agentic_rag_system.image_data_store,
            "agentic",
        )
        logger.info("[ingest-agentic] Saving document record to SQLite...")
        current_agentic_doc_id = save_document(
            "agentic",
            file.filename,
            len(agentic_rag_system.text_docs),
            len(agentic_rag_system.image_data_store),
        )
        logger.info(f"[ingest-agentic] Document saved with id={current_agentic_doc_id}")

        return JSONResponse(
            content={
                "message": f"Successfully processed {file.filename} for Agentic RAG",
                "status": "initialized",
            },
            status_code=200,
        )

    except Exception as e:
        logger.exception(f"[ingest-agentic] Failed to ingest {file.filename}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_file.exists():
            temp_file.unlink()
        file.file.close()


@app.post("/query-agentic")
async def query_documents_agentic(query: Query):
    """Query the agentic RAG system."""
    if not agentic_rag_system.is_initialized():
        raise HTTPException(
            status_code=400,
            detail="Agentic RAG system not initialized. Please ingest a document first using /ingest-agentic.",
        )

    try:
        t0 = time.perf_counter()
        result = run_agentic_rag(
            question=query.question,
            llm=llm,
            rag_system=agentic_rag_system,
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        _log_query(query.question, result, latency_ms, document_id=current_agentic_doc_id)

        return JSONResponse(
            content={
                "answer": result["answer"],
                "sources": result["sources"],
                "num_images": result["num_images"],
                "num_text_chunks": result["num_text_chunks"],
                "agent_type": "ReAct",
            },
            status_code=200,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query-agentic-stream")
async def query_documents_agentic_stream(query: Query):
    """Streaming endpoint for the agentic RAG system."""
    if not agentic_rag_system.is_initialized():
        raise HTTPException(
            status_code=400,
            detail="Agentic RAG system not initialized. Please ingest a document first using /ingest-agentic.",
        )

    t0 = time.perf_counter()
    result_collector: dict = {}

    async def generate():
        full_result: dict = {}
        try:
            async for token in stream_agentic_rag(
                question=query.question,
                llm=llm,
                rag_system=agentic_rag_system,
                result_collector=result_collector,
            ):
                yield token

            # --- Compute metrics and yield as final chunk ---
            latency_ms = (time.perf_counter() - t0) * 1000
            answer     = result_collector.get("answer", "")
            sources    = result_collector.get("sources", [])
            num_chunks = result_collector.get("num_text_chunks", 0)
            num_images = result_collector.get("num_images", 0)

            top_similarity = 0.0
            try:
                from app.rag.core.embedder import get_embedder
                emb = get_embedder().embed_text(query.question).tolist()
                scored = agentic_rag_system.vectorStore.similarity_search_with_score_by_vector(
                    emb, k=1
                )
                if scored:
                    top_similarity = round(float(1 / (1 + scored[0][1])), 3)
            except Exception:
                pass

            from app.rag.core.metrics import compute_confidence, compute_answer_source_similarity
            from app.rag.core.config import HybridSearchConfig

            source_pages = {s["page"] for s in sources}
            relevant_docs = (
                [d for d in agentic_rag_system.text_docs if d.metadata.get("page") in source_pages]
                or agentic_rag_system.text_docs[:10]
            )
            answer_source_sim = compute_answer_source_similarity(answer, relevant_docs)
            confidence        = compute_confidence(top_similarity, num_chunks)
            is_hallucination  = answer_source_sim < HybridSearchConfig.HALLUCINATION_THRESHOLD

            full_result = {
                "answer": answer,
                "sources": sources,
                "num_images": num_images,
                "num_text_chunks": num_chunks,
                "top_similarity": top_similarity,
                "confidence": confidence,
                "answer_source_similarity": answer_source_sim,
                "is_hallucination": is_hallucination,
                "source_pages": sorted(source_pages),
                "agent_type": "ReAct",
                "latency_ms": round(latency_ms, 1),
            }

            yield f"\n\n__METADATA__{json.dumps(full_result)}"

        except Exception as e:
            yield f"\n\nError: {str(e)}"
        finally:
            if full_result:
                try:
                    _log_query(
                        query.question, full_result,
                        full_result.get("latency_ms", (time.perf_counter() - t0) * 1000),
                        document_id=current_agentic_doc_id,
                    )
                except Exception as e:
                    logger.warning(f"Failed to log streaming query: {e}")

    return StreamingResponse(generate(), media_type="text/plain")


# ---------------------------------------------------------------------------
# Document registry + evaluation endpoints
# ---------------------------------------------------------------------------

@app.get("/documents")
def list_documents():
    """List all ingested documents from the SQLite registry."""
    return JSONResponse(content={"documents": get_all_documents()})


@app.get("/eval/summary")
def eval_summary():
    """Return aggregate evaluation metrics computed from stored query logs."""
    return JSONResponse(content=get_eval_summary())


@app.get("/eval/logs")
def eval_logs(limit: int = 50):
    """Return the most recent query log entries."""
    return JSONResponse(content={"logs": get_recent_logs(limit)})


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
