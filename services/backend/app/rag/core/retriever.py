from dataclasses import dataclass
from typing import Dict
from .data_ingestion import CLIPEmbedder
from langchain.schema.messages import HumanMessage
from langchain_community.vectorstores import FAISS


@dataclass
class MultiModalRetrieval:
    """
    Class for unified retrieval of text and images using CLIP embeddings.
    """
    query: str
    vectorStore: FAISS
    image_data_store: Dict
    k: int = 5

    def __post_init__(self):
        """Initialize the CLIPEmbedder instance after dataclass initialization."""
        self.embedder = CLIPEmbedder()

    def retrieve_multimodal(self):
        """
        Unified retrieval for text and images.

        Returns:
            List of retrieved documents
        """
        # Embed query using CLIP
        query_embedding = self.embedder.embed_text(self.query)

        # Search in unified vector store
        results = self.vectorStore.similarity_search_by_vector(
            embedding=query_embedding,
            k=self.k
        )
        return results

    def create_multimodal_message(self, retrieved_docs):
        """
        Create a message with both text and images for GPT-4V.

        Args:
            retrieved_docs: List of retrieved documents

        Returns:
            HumanMessage: Formatted message for the LLM
        """
        content = []

        # Add the query
        content.append({
            "type": "text",
            "text": f"Question: {self.query}\n\nContext:\n"
        })

        # Separate text and image documents
        text_docs = [doc for doc in retrieved_docs if doc.metadata.get("type") == "text"]
        image_docs = [doc for doc in retrieved_docs if doc.metadata.get("type") == "image"]

        # Add text context
        if text_docs:
            text_context = "\n\n".join([
                f"[Page {doc.metadata['page']}]: {doc.page_content}"
                for doc in text_docs
            ])
            content.append({
                "type": "text",
                "text": f"Text excerpts:\n{text_context}\n"
            })

        # Add images context
        for doc in image_docs:
            image_id = doc.metadata.get("image_id")
            if image_id and image_id in self.image_data_store:
                content.append({
                    "type": "text",
                    "text": f"\n[Image from page {doc.metadata['page']}]\n"
                })
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{self.image_data_store[image_id]}",
                        "alt_text": f"Image from page {doc.metadata['page']}"
                    }
                })

        # Add instruction
        content.append({
            "type": "text",
            "text": "\nAnswer the question based on the provided context. If the context does not contain the answer, say 'I don't know'."
        })

        return HumanMessage(content=content)


