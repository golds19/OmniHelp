from retriever import retrieve_multimodal, create_multimodal_message
from data_ingestion import DataEmbedding
import numpy as np
from vectorstore import create_vectorestore
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

import os

load_dotenv()

def multimodal_pdf_rag_pipeline(query,
                                llm,
                                vectorstore,
                                image_data_store,
                                k=5):
    """Main Pipeline for multimodal RAG"""

    # Retrieve relevant documents
    context_docs = retrieve_multimodal(vectorstore=vectorstore, 
                                       query=query,
                                       k=k)
    print(f"Context_docs: {context_docs}")
    # create multimodal message
    message = create_multimodal_message(query=query,
                                        image_data_store=image_data_store, 
                                        retrieved_docs=context_docs)

    # Get response from LLM
    response = llm.invoke([message])

    # print retrieved context info
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

    return response.content

if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(model="gpt-5-nano", temperature=0.2)

    path = "C:/Research Folder/AI Projects/Lifeforge/services/backend/app/rag/data/multimodal_sample.pdf"
    try:
        # 1. load the data and create embeddings
        data_embedder = DataEmbedding(path)
        docs, embeddings, image_data_store = data_embedder.process_and_embedd_docs()

        embeddings_array = np.array(embeddings)

        # 2. create the vectore store and store the embeddings
        vector_store = create_vectorestore(
        embeddings_array=embeddings_array,
        all_docs=docs)

        print(f"Vector store created: {vector_store}")

        # 3. example queries and response
        queries = [
            "what does the chart on page 2 show about revenue trends?",
            "Summarize the main findings from the document",
            "what visual elements are present in the document?"
        ]
        for q in queries:
            print(f"\nQuery: {q}")
            print("-"*50)
            answer = multimodal_pdf_rag_pipeline(query=q,
                                                 llm=llm,
                                                 vectorstore= vector_store,
                                                 image_data_store=image_data_store)
            print(f"Answer: {answer}\n{'-'*50}\n")
    except Exception as e:
        print(f"Failed creating and storing embedding in vectorstore with error {e}")