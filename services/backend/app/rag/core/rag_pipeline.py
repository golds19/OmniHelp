from dataclasses import dataclass
from typing import Dict, Optional
from .retriever import MultiModalRetrieval
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from dotenv import load_dotenv

import os

load_dotenv()


@dataclass
class MultiModalRAG:
    """
    Main pipeline for multimodal RAG (Retrieval-Augmented Generation).
    Supports both dense-only and hybrid (BM25 + Dense) search modes.
    """
    query: str
    vectorStore: FAISS
    image_data_store: Dict
    llm: ChatOpenAI
    k: int = 5
    bm25_retriever: Optional[BM25Retriever] = None
    use_hybrid: bool = True

    def generate(self):
        """
        Main pipeline for multimodal RAG.
        Supports both hybrid (BM25 + Dense) and dense-only search.

        Returns:
            Dict: Contains answer, sources, and metadata
        """
        # Retrieve relevant documents
        retriever = MultiModalRetrieval(
            query=self.query,
            vectorStore=self.vectorStore,
            image_data_store=self.image_data_store,
            k=self.k,
            bm25_retriever=self.bm25_retriever,
            use_hybrid=self.use_hybrid
        )
        context_docs = retriever.retrieve_multimodal()

        # Create multimodal message
        message = retriever.create_multimodal_message(context_docs)

        # Get response from LLM
        response = self.llm.invoke([message])

        # Print retrieved context info
        print(f"\nRetrieved {len(context_docs)} documents for context")
        for doc in context_docs:
            doc_type = doc.metadata.get("type", "unknown")
            page = doc.metadata.get("page", "N/A")
            if doc_type == "text":
                preview = doc.page_content[:100].replace("\n", " ") + ("..." if len(doc.page_content) > 100 else doc.page_content)
                print(f"- [Text] Page {page}: {preview}")
            else:
                image_id = doc.metadata.get("image_id", "N/A")
                print(f"- [Image] Page {page}, ID: {image_id}")
        print("\n")

        # Return both response and metadata
        return {
            "answer": response.content,
            "sources": [{"page": doc.metadata["page"], "type": doc.metadata["type"]}
                       for doc in context_docs],
            "num_images": len([doc for doc in context_docs if doc.metadata.get("type") == "image"]),
            "num_text_chunks": len([doc for doc in context_docs if doc.metadata.get("type") == "text"])
        }



if __name__ == "__main__":
    print("test")