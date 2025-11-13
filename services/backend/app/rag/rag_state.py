"""RAG state definition for LangGraph"""

from typing import Annotated, List, Dict, Union
from typing_extensions import TypedDict
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgenticRAGState(TypedDict):
    """State object for Agentic RAG workflow with ReAct agent"""

    # Core query and conversation
    messages: Annotated[List[BaseMessage], add_messages]

    # Retrieved documents from RAG
    retrieved_docs: List[Document]

    # Final answer
    answer: str

    # Metadata about retrieval
    sources: List[Dict]  # List of {"page": int, "type": str}
    num_images: int
    num_text_chunks: int