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

logger = logging.getLogger(__name__)


def _log_query(query: str, result: dict, latency_ms: float):
    """Emit a structured JSON log line for every query."""
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "query": query,
        "answer_length": len(result.get("answer", "")),
        "num_text_chunks": result.get("num_text_chunks", 0),
        "num_images": result.get("num_images", 0),
        "top_similarity": result.get("top_similarity", 0.0),
        "confidence": result.get("confidence", 0.0),
        "source_pages": [s["page"] for s in result.get("sources", [])],
        "latency_ms": round(latency_ms, 1),
    }
    logger.info(f"QUERY_LOG {json.dumps(entry)}")


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

# Store vectorstore, BM25 retriever, and image data store in memory (for non-agentic RAG)
vectorstore = None
bm25_retriever = None
image_data_store = {}

# Initialize Agentic RAG System (singleton)
agentic_rag_system = MultiModalRAGSystem()

# Simple GET endpoint for testing
@app.get("/ping")
def ping():
    return {"message": "pong"}

# Compiled once at module load — patterns that indicate prompt injection attempts
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

@app.post("/ingest")
async def ingest_document(file: UploadFile = File(...)):
    """
    Endpoint for ingesting PDF documents into the RAG system.
    """
    global vectorstore, bm25_retriever, image_data_store
    
    # Verify file is PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Create temporary file to save the upload
    temp_dir = Path(AppConfig.TEMP_DIR)
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / file.filename

    try:
        # Save uploaded file
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process and embed documents
        data_embedder = DataEmbedding(str(temp_file))
        docs, embeddings, image_data_store, text_docs = data_embedder.process_and_embedd_docs()

        # Create hybrid retrievers (FAISS + BM25) using VectorStore class
        vs = VectorStore(
            all_docs=docs,
            all_embeddings=embeddings,
            image_data_store=image_data_store,
            text_docs=text_docs
        )
        hybrid_stores = vs.create_hybrid_retrievers()
        vectorstore = hybrid_stores["faiss_store"]
        bm25_retriever = hybrid_stores["bm25_retriever"]
        image_data_store = hybrid_stores["image_data_store"]
        
        return JSONResponse(
            content={"message": f"Successfully processed {file.filename}"},
            status_code=200
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup temporary file
        if temp_file.exists():
            temp_file.unlink()
        file.file.close()

@app.post("/query")
async def query_documents(query: Query):
    """
    Endpoint for querying the RAG system with questions.
    """
    global vectorstore, bm25_retriever, image_data_store
    
    if not vectorstore:
        raise HTTPException(
            status_code=400, 
            detail="No documents have been ingested. Please ingest documents first."
        )
    
    try:
        # Use the new MultiModalRAG class with hybrid search support
        rag = MultiModalRAG(
            query=query.question,
            vectorStore=vectorstore,
            image_data_store=image_data_store,
            llm=llm,
            k=5,
            bm25_retriever=bm25_retriever
        )
        t0 = time.perf_counter()
        result = rag.generate()
        latency_ms = (time.perf_counter() - t0) * 1000
        _log_query(query.question, result, latency_ms)

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
            status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Agentic RAG Endpoints ==========

@app.post("/ingest-agentic")
async def ingest_document_agentic(file: UploadFile = File(...)):
    """
    Endpoint for ingesting PDF documents into the Agentic RAG system.
    """
    global agentic_rag_system

    # Verify file is PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Create temporary file to save the upload
    temp_dir = Path(AppConfig.TEMP_DIR)
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / file.filename

    try:
        # Save uploaded file
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Initialize the agentic RAG system
        agentic_rag_system.initialize(pdf_path=str(temp_file), vision_llm=llm)

        return JSONResponse(
            content={
                "message": f"Successfully processed {file.filename} for Agentic RAG",
                "status": "initialized"
            },
            status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup temporary file
        if temp_file.exists():
            temp_file.unlink()
        file.file.close()


@app.post("/query-agentic")
async def query_documents_agentic(query: Query):
    """
    Endpoint for querying the Agentic RAG system with questions.
    Uses a ReAct agent that can reason and retrieve documents.
    """
    global agentic_rag_system

    if not agentic_rag_system.is_initialized():
        raise HTTPException(
            status_code=400,
            detail="Agentic RAG system not initialized. Please ingest a document first using /ingest-agentic."
        )

    try:
        # Run the agentic RAG workflow
        t0 = time.perf_counter()
        result = run_agentic_rag(
            question=query.question,
            llm=llm,
            rag_system=agentic_rag_system
        )
        latency_ms = (time.perf_counter() - t0) * 1000
        _log_query(query.question, result, latency_ms)

        return JSONResponse(
            content={
                "answer": result["answer"],
                "sources": result["sources"],
                "num_images": result["num_images"],
                "num_text_chunks": result["num_text_chunks"],
                "agent_type": "ReAct"
            },
            status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query-agentic-stream")
async def query_documents_agentic_stream(query: Query):
    """
    Streaming endpoint for querying the Agentic RAG system.
    Returns tokens as they are generated for real-time display.
    """
    global agentic_rag_system

    if not agentic_rag_system.is_initialized():
        raise HTTPException(
            status_code=400,
            detail="Agentic RAG system not initialized. Please ingest a document first using /ingest-agentic."
        )

    async def generate():
        try:
            async for token in stream_agentic_rag(
                question=query.question,
                llm=llm,
                rag_system=agentic_rag_system
            ):
                yield token
        except Exception as e:
            yield f"\n\nError: {str(e)}"

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)