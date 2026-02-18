import logging
from pathlib import Path
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI

from app.rag.core.data_ingestion import DataEmbedding
from app.rag.core.vectorstore import VectorStore
from app.rag.core.rag_pipeline import MultiModalRAG
from app.rag.core.rag_manager import MultiModalRAGSystem
from app.rag.core.config import LLMConfig, AppConfig
from app.rag.agent.graph_builder import run_agentic_rag, stream_agentic_rag

logger = logging.getLogger(__name__)

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

class Query(BaseModel):
    question: str

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
        result = rag.generate()

        return JSONResponse(
            content={
                "answer": result["answer"],
                "sources": result["sources"],
                "num_images": result["num_images"],
                "num_text_chunks": result["num_text_chunks"]
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
        result = run_agentic_rag(
            question=query.question,
            llm=llm,
            rag_system=agentic_rag_system
        )

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