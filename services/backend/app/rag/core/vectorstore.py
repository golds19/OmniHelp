from dataclasses import dataclass
from typing import List, Dict
from langchain_community.vectorstores import FAISS
import numpy as np


@dataclass
class VectorStore:
    """
    Class for creating and managing FAISS vector stores with CLIP embeddings.
    """
    all_docs: List
    all_embeddings: List
    image_data_store: Dict

    def create_vectorstore(self):
        """
        Create unified FAISS vector store with CLIP embeddings.

        Returns:
            FAISS: Vector store instance
        """
        embedding_array = np.array(self.all_embeddings)
        vector_store = FAISS.from_embeddings(
            text_embeddings=[(doc.page_content, emb) for doc, emb in zip(self.all_docs, embedding_array)],
            embedding=None,
            metadatas=[doc.metadata for doc in self.all_docs]
        )
        return vector_store


if __name__ == "__main__":
    print("Testing")