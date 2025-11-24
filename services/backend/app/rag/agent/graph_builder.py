"""
LangGraph builder for the Agentic RAG system.
"""

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from typing import AsyncGenerator
from .rag_state import AgenticRAGState
from ..core.rag_manager import MultiModalRAGSystem
from .agent_tools import get_agent_tools
from .react_node import create_agent_executor, agent_node


def build_agentic_rag_graph(
    llm: ChatOpenAI,
    rag_system: MultiModalRAGSystem
):
    """
    Build the LangGraph workflow for Agentic RAG.

    Args:
        llm: The language model to use for the agent
        rag_system: The initialized MultiModalRAGSystem

    Returns:
        Compiled graph ready for invocation
    """
    # Create tools
    tools = get_agent_tools(rag_system)

    # Create agent executor
    agent_executor = create_agent_executor(llm, tools)

    # Define the graph
    workflow = StateGraph(AgenticRAGState)

    # Define the agent node function
    def run_agent(state: AgenticRAGState) -> AgenticRAGState:
        """Run the agent and update state."""
        return agent_node(state, agent_executor)

    # Add nodes
    workflow.add_node("agent", run_agent)

    # Set entry point
    workflow.set_entry_point("agent")

    # Add edge to end
    workflow.add_edge("agent", END)

    # Compile the graph
    graph = workflow.compile()

    return graph


def run_agentic_rag(
    question: str,
    llm: ChatOpenAI,
    rag_system: MultiModalRAGSystem
) -> dict:
    """
    Run the agentic RAG workflow with a question.

    Args:
        question: The user's question
        llm: The language model to use
        rag_system: The initialized MultiModalRAGSystem

    Returns:
        Dict containing answer and metadata
    """
    # Build the graph
    graph = build_agentic_rag_graph(llm, rag_system)

    # Create initial state
    initial_state = {
        "messages": [HumanMessage(content=question)],
        "retrieved_docs": [],
        "answer": "",
        "sources": [],
        "num_images": 0,
        "num_text_chunks": 0
    }

    # Run the graph
    result = graph.invoke(initial_state)

    return {
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "num_images": result.get("num_images", 0),
        "num_text_chunks": result.get("num_text_chunks", 0)
    }


async def stream_agentic_rag(
    question: str,
    llm: ChatOpenAI,
    rag_system: MultiModalRAGSystem
) -> AsyncGenerator[str, None]:
    """
    Stream tokens from the agentic RAG workflow.

    Args:
        question: The user's question
        llm: The language model to use
        rag_system: The initialized MultiModalRAGSystem

    Yields:
        String tokens as they are generated
    """
    graph = build_agentic_rag_graph(llm, rag_system)

    initial_state = {
        "messages": [HumanMessage(content=question)],
        "retrieved_docs": [],
        "answer": "",
        "sources": [],
        "num_images": 0,
        "num_text_chunks": 0
    }

    async for chunk, metadata in graph.astream(
        initial_state,
        stream_mode="messages",
    ):
        if chunk.content:
            yield chunk.content
