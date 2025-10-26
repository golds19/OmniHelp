from langchain_community.vectorstores import FAISS
from data_ingestion import DataEmbedding
import numpy as np

def create_vectorestore(embeddings_array, all_docs):
    vectore_store = FAISS.from_embeddings(
        text_embeddings=[(doc.page_content, emb) for doc, emb in zip(all_docs, embeddings_array)],
        embedding=None,
        metadatas=[doc.metadata for doc in all_docs]
    )
    return vectore_store

if __name__ == "__main__":
    path = "C:/Research Folder/AI Projects/Lifeforge/services/backend/app/rag/data/multimodal_sample.pdf"
    data_embedder = DataEmbedding(path)
    docs, embeddings = data_embedder.process_and_embedd_docs()

    embeddings_array = np.array(embeddings)
    # create and store embeddings in vectorestore
    try:
        vector_store = create_vectorestore(
        embeddings_array=embeddings_array,
        all_docs=docs)
        print(vector_store)
    except Exception as e:
        print(f"Failed creating and storing embedding in vectorstore with error {e}")