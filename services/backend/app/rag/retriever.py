from data_ingestion import embed_text
from langchain.schema.messages import HumanMessage

def retrieve_multimodal(vectorstore, query, k=3):
    """Unified using CLIP embeddings for both text and images"""
    query_embedding = embed_text(query)

    # search in unified vector store
    #vectorstore = create_vectorestore(embedding_arrays, all_docs)
    results = vectorstore.similarity_search_by_vector(
        embedding=query_embedding,
        k=k
    )

    return results

def create_multimodal_message(query, retrieved_docs, image_data_store):
    """Create a message with both text and images for the LLM model"""
    content = []

    # Add the query
    content.append({
        "type": "text",
        "text": f"Question: {query}\n\nContext:\n"
    })

    # separate text and image documents
    text_docs = [doc for doc in retrieved_docs if doc.metadata.get("type") == "text"]
    image_docs = [doc for doc in retrieved_docs if doc.metatada.get("type") == "image"]

    # Add text context
    if text_docs:
        text_context = "\n\n".join([
            f"[Page {doc.metadata['page']}]: {doc.page_content}"
            for doc in text_docs
        ])
        content.append({
            "type": "text",
            "text": f"Text exerpts:\n{text_context}\n"
        })

    # Add images context
    for doc in image_docs:
        image_id = doc.metadata.get("image_id")
        if image_id and image_id in image_data_store:
            content.append({
                "type": "text",
                "text": f"\n[Image from page {doc.metadata['page']}]\n"
            })
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_data_store[image_id]}",
                    "alt_text": f"Image from page {doc.metadata['page']}"
                }
            })

    # Add instruction
    content.append({
        "type": "text",
        "text": "\nAnswer the question based on the provided context. If the context does not contain the answer, say i don't know."
    })

    return HumanMessage(content=content)