"""
Shared utilities for RAG core components.
"""
from typing import Dict, List, Tuple
from langchain_core.messages import HumanMessage
from langchain_core.documents import Document


def filter_documents_by_type(documents: List[Document]) -> Tuple[List[Document], List[Document]]:
    """
    Separate documents into text and image documents.

    Args:
        documents: List of documents to filter

    Returns:
        Tuple of (text_docs, image_docs)
    """
    text_docs = [doc for doc in documents if doc.metadata.get("type") == "text"]
    image_docs = [doc for doc in documents if doc.metadata.get("type") == "image"]
    return text_docs, image_docs


def create_multimodal_message(
    query: str,
    retrieved_docs: List[Document],
    image_data_store: Dict[str, str]
) -> HumanMessage:
    """
    Create a message with both text and images for GPT-4V.

    Args:
        query: The user's query
        retrieved_docs: List of retrieved documents
        image_data_store: Dictionary mapping image_id to base64 image data

    Returns:
        HumanMessage: Formatted message for the LLM
    """
    content = []

    # Add the query
    content.append({
        "type": "text",
        "text": f"Question: {query}\n\nContext:\n"
    })

    # Separate text and image documents
    text_docs, image_docs = filter_documents_by_type(retrieved_docs)

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
        "text": "\nAnswer the question based on the provided context. If the context does not contain the answer, say 'I don't know'."
    })

    return HumanMessage(content=content)
