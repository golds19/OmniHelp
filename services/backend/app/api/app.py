from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
from pathlib import Path
import shutil
from typing import Optional

from app.rag.data_ingestion import DataEmbedding
from app.rag.vectorstore import create_vectorestore
from app.rag.rag_pipeline import multimodal_pdf_rag_pipeline
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Lifeforge RAG API")

origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI Chat model
llm = ChatOpenAI(model="gpt-5-nano", temperature=0.2)

# Store vectorstore and image data store in memory
vectorstore = None
image_data_store = {}

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
    global vectorstore, image_data_store
    
    # Verify file is PDF
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Create temporary file to save the upload
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    temp_file = temp_dir / file.filename
    
    try:
        # Save uploaded file
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process and embed documents
        data_embedder = DataEmbedding(str(temp_file))
        docs, embeddings, image_data_store = data_embedder.process_and_embedd_docs()
                
        # Create vector store
        vectorstore = create_vectorestore(
            embeddings_array=embeddings,
            all_docs=docs
        )
        
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
    global vectorstore, image_data_store
    
    if not vectorstore:
        raise HTTPException(
            status_code=400, 
            detail="No documents have been ingested. Please ingest documents first."
        )
    
    try:
        response = multimodal_pdf_rag_pipeline(
            query=query.question,
            llm=llm,
            vectorstore=vectorstore,
            image_data_store=image_data_store
        )
        
        return JSONResponse(
            content={"answer": response},
            status_code=200
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)