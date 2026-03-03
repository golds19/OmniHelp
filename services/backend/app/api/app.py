import asyncio
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Literal, Optional

from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
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
from app.rag.core.embedder import get_embedder, get_text_embedder

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


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


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class Query(BaseModel):
    question: str
    session_id: str
    messages: Optional[List[Message]] = None  # prior turns, not including current question

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

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=AppConfig.CORS_ORIGINS,
    allow_origin_regex=r"https://(.*\.up\.railway\.app|.*\.vercel\.app)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI Chat model from config
llm = ChatOpenAI(model=LLMConfig.LLM_MODEL, temperature=LLMConfig.LLM_TEMPERATURE)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

SESSION_TTL_SECONDS: int = 24 * 3600


@dataclass
class SessionState:
    text_vectorstore: Any
    image_vectorstore: Any
    bm25_retriever: Any
    image_data_store: dict
    doc_id: Optional[int]
    created_at: float = field(default_factory=time.time)


sessions: dict[str, SessionState] = {}        # standard sessions
agentic_sessions: dict[str, tuple] = {}       # (MultiModalRAGSystem, float)


# ---------------------------------------------------------------------------
# TTL eviction
# ---------------------------------------------------------------------------

async def _evict_expired_sessions():
    while True:
        await asyncio.sleep(30 * 60)
        now = time.time()
        for sid in [s for s, st in list(sessions.items()) if now - st.created_at > SESSION_TTL_SECONDS]:
            del sessions[sid]
        for sid in [s for s, (_, t) in list(agentic_sessions.items()) if now - t > SESSION_TTL_SECONDS]:
            del agentic_sessions[sid]


# ---------------------------------------------------------------------------
# Startup — restore persisted indices
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event():
    logger.info("Pre-loading CLIP model...")
    get_embedder()
    logger.info("CLIP model ready.")

    logger.info("Pre-loading text embedding model...")
    get_text_embedder()
    logger.info("Text embedding model ready.")

    init_db()

    # Restore standard sessions from data/standard/*/
    standard_root = Path(AppConfig.DATA_DIR) / "standard"
    if standard_root.exists():
        for session_dir in standard_root.iterdir():
            if not session_dir.is_dir():
                continue
            loaded = load_index("standard", session_id=session_dir.name)
            if loaded:
                sessions[session_dir.name] = SessionState(
                    text_vectorstore=loaded["text_faiss_store"],
                    image_vectorstore=loaded["image_faiss_store"],
                    bm25_retriever=loaded["bm25_retriever"],
                    image_data_store=loaded["image_data_store"],
                    doc_id=None,
                )
                logger.info(f"Restored standard session {session_dir.name} from disk.")

    # Restore agentic sessions from data/agentic/*/
    agentic_root = Path(AppConfig.DATA_DIR) / "agentic"
    if agentic_root.exists():
        for session_dir in agentic_root.iterdir():
            if not session_dir.is_dir():
                continue
            agentic_loaded = load_index("agentic", session_id=session_dir.name)
            if agentic_loaded:
                ras = MultiModalRAGSystem()
                ras.text_vectorStore = agentic_loaded["text_faiss_store"]
                ras.image_vectorStore = agentic_loaded["image_faiss_store"]
                ras.bm25_retriever = agentic_loaded["bm25_retriever"]
                ras.image_data_store = agentic_loaded["image_data_store"]
                ras.vision_llm = llm
                ras.all_docs = list(ras.text_vectorStore.docstore._dict.values())
                ras.text_docs = ras.all_docs
                ras.all_embeddings = []
                ras._initialized = True
                agentic_sessions[session_dir.name] = (ras, time.time())
                logger.info(f"Restored agentic session {session_dir.name} from disk.")

    # Start TTL eviction
    try:
        asyncio.create_task(_evict_expired_sessions())
    except RuntimeError:
        pass  # no event loop in test mode


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
# @limiter.limit("3/day")
async def ingest_document(request: Request, file: UploadFile = File(...)):
    """Ingest a PDF into the standard (non-agentic) RAG system."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    temp_dir = Path(AppConfig.TEMP_DIR)
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / Path(file.filename).name

    try:
        size = 0
        chunks = []
        while chunk := await file.read(1024 * 1024):  # 1 MB chunks
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")
            chunks.append(chunk)

        with temp_file.open("wb") as buffer:
            for chunk in chunks:
                buffer.write(chunk)
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
        text_vectorstore  = hybrid_stores["text_faiss_store"]
        image_vectorstore = hybrid_stores["image_faiss_store"]
        bm25_retriever    = hybrid_stores["bm25_retriever"]
        image_data_store  = hybrid_stores["image_data_store"]
        logger.info("[ingest] Vector store created successfully")

        # Generate session and persist to disk
        session_id = str(uuid.uuid4())
        logger.info("[ingest] Saving index to disk...")
        save_index(text_vectorstore, image_vectorstore, image_data_store, "standard", session_id=session_id)
        logger.info("[ingest] Saving document record to SQLite...")
        doc_id = save_document(
            "standard", file.filename, len(text_docs), len(image_data_store)
        )
        logger.info(f"[ingest] Document saved with id={doc_id}")

        sessions[session_id] = SessionState(
            text_vectorstore=text_vectorstore,
            image_vectorstore=image_vectorstore,
            bm25_retriever=bm25_retriever,
            image_data_store=image_data_store,
            doc_id=doc_id,
        )

        return JSONResponse(
            content={"session_id": session_id, "message": f"Successfully processed {file.filename}"},
            status_code=200,
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"[ingest] Failed to ingest {file.filename}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_file.exists():
            temp_file.unlink()
        file.file.close()


@app.post("/query")
# @limiter.limit("3/day")
async def query_documents(request: Request, query: Query):
    """Query the standard RAG system."""
    state = sessions.get(query.session_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please ingest a document first.",
        )

    try:
        rag = MultiModalRAG(
            query=query.question,
            text_vectorStore=state.text_vectorstore,
            image_vectorStore=state.image_vectorstore,
            image_data_store=state.image_data_store,
            llm=llm,
            k=5,
            bm25_retriever=state.bm25_retriever,
        )
        t0 = time.perf_counter()
        result = rag.generate()
        latency_ms = (time.perf_counter() - t0) * 1000
        _log_query(query.question, result, latency_ms, document_id=state.doc_id)

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
# @limiter.limit("3/day")
async def ingest_document_agentic(request: Request, file: UploadFile = File(...)):
    """Ingest a PDF into the agentic RAG system."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    temp_dir = Path(AppConfig.TEMP_DIR)
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / Path(file.filename).name

    try:
        size = 0
        chunks = []
        while chunk := await file.read(1024 * 1024):  # 1 MB chunks
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")
            chunks.append(chunk)

        with temp_file.open("wb") as buffer:
            for chunk in chunks:
                buffer.write(chunk)
        logger.info(f"[ingest-agentic] Saved upload to {temp_file} ({temp_file.stat().st_size} bytes)")

        logger.info("[ingest-agentic] Initializing agentic RAG system...")
        ras = MultiModalRAGSystem()
        ras.initialize(pdf_path=str(temp_file), vision_llm=llm)
        logger.info("[ingest-agentic] Agentic RAG initialized successfully")

        # Generate session and persist to disk
        session_id = str(uuid.uuid4())
        logger.info("[ingest-agentic] Saving index to disk...")
        save_index(
            ras.text_vectorStore,
            ras.image_vectorStore,
            ras.image_data_store,
            "agentic",
            session_id=session_id,
        )
        logger.info("[ingest-agentic] Saving document record to SQLite...")
        save_document(
            "agentic",
            file.filename,
            len(ras.text_docs),
            len(ras.image_data_store),
        )
        agentic_sessions[session_id] = (ras, time.time())

        return JSONResponse(
            content={
                "session_id": session_id,
                "message": f"Successfully processed {file.filename} for Agentic RAG",
                "status": "initialized",
            },
            status_code=200,
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception(f"[ingest-agentic] Failed to ingest {file.filename}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_file.exists():
            temp_file.unlink()
        file.file.close()


@app.post("/query-agentic")
# @limiter.limit("3/day")
async def query_documents_agentic(request: Request, query: Query):
    """Query the agentic RAG system."""
    entry = agentic_sessions.get(query.session_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please ingest a document first using /ingest-agentic.",
        )
    ras, _ = entry

    try:
        t0 = time.perf_counter()
        result = run_agentic_rag(
            question=query.question,
            llm=llm,
            rag_system=ras,
            messages=[m.model_dump() for m in query.messages] if query.messages else None,
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        _log_query(query.question, result, latency_ms, document_id=None)

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
# @limiter.limit("3/day")
async def query_documents_agentic_stream(request: Request, query: Query):
    """Streaming endpoint for the agentic RAG system."""
    entry = agentic_sessions.get(query.session_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please ingest a document first using /ingest-agentic.",
        )
    ras, _ = entry

    t0 = time.perf_counter()
    result_collector: dict = {}

    async def generate():
        full_result: dict = {}
        try:
            async for token in stream_agentic_rag(
                question=query.question,
                llm=llm,
                rag_system=ras,
                result_collector=result_collector,
                messages=[m.model_dump() for m in query.messages] if query.messages else None,
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
                text_emb = get_text_embedder().encode(
                    query.question, normalize_embeddings=True
                ).tolist()
                scored = ras.text_vectorStore.similarity_search_with_score_by_vector(
                    text_emb, k=1
                )
                if scored:
                    top_similarity = round(float(1 / (1 + scored[0][1])), 3)
            except Exception:
                pass

            from app.rag.core.metrics import compute_confidence, compute_answer_source_similarity
            from app.rag.core.config import HybridSearchConfig

            source_pages = {s["page"] for s in sources}
            relevant_docs = (
                [d for d in ras.text_docs if d.metadata.get("page") in source_pages]
                or ras.text_docs[:10]
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
                        document_id=None,
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
