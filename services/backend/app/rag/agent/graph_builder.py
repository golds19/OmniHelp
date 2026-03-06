"""
LangGraph builder for the Agentic RAG system.
"""

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import AsyncGenerator, List, Optional
from .rag_state import AgenticRAGState
from ..core.rag_manager import MultiModalRAGSystem
from .agent_tools import get_agent_tools
from .react_node import create_agent_executor, agent_node
from .vision_node import create_vision_synthesis_node


def _build_messages(question: str, history: Optional[List[dict]]) -> List[BaseMessage]:
    """Convert history dicts + current question into LangChain message objects."""
    result: List[BaseMessage] = []
    if history:
        for m in history:
            if m["role"] == "user":
                result.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                result.append(AIMessage(content=m["content"]))
    result.append(HumanMessage(content=question))
    return result


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
    # Create tools (pass LLM for query enhancement tools)
    tools = get_agent_tools(rag_system, llm)

    # Create agent executor
    agent_executor = create_agent_executor(llm, tools)

    # Define the graph
    workflow = StateGraph(AgenticRAGState)

    # Define the agent node function
    def run_agent(state: AgenticRAGState) -> AgenticRAGState:
        """Run the agent and update state."""
        return agent_node(state, agent_executor)

    def should_run_vision(state: AgenticRAGState) -> str:
        """Route to vision_synthesis if images were retrieved, else END."""
        return "vision_synthesis" if state.get("image_ids") else END

    # Add nodes
    workflow.add_node("agent", run_agent)
    workflow.add_node("vision_synthesis", create_vision_synthesis_node(rag_system, llm))

    # Set entry point
    workflow.set_entry_point("agent")

    # Agent → vision synthesis (if images found) or END
    workflow.add_conditional_edges("agent", should_run_vision, {
        "vision_synthesis": "vision_synthesis",
        END: END,
    })
    workflow.add_edge("vision_synthesis", END)

    # Compile the graph
    graph = workflow.compile()

    return graph


def run_agentic_rag(
    question: str,
    llm: ChatOpenAI,
    rag_system: MultiModalRAGSystem,
    messages: Optional[List[dict]] = None,
) -> dict:
    """
    Run the agentic RAG workflow with a question.

    Args:
        question: The user's question
        llm: The language model to use
        rag_system: The initialized MultiModalRAGSystem
        messages: Optional prior conversation turns as list of {role, content} dicts

    Returns:
        Dict containing answer and metadata
    """
    # Build the graph
    graph = build_agentic_rag_graph(llm, rag_system)

    # Create initial state
    initial_state = {
        "messages": _build_messages(question, messages),
        "retrieved_docs": [],
        "answer": "",
        "sources": [],
        "num_images": 0,
        "num_text_chunks": 0,
        "image_ids": [],
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
    rag_system: MultiModalRAGSystem,
    result_collector: Optional[dict] = None,
    messages: Optional[List[dict]] = None,
) -> AsyncGenerator[str, None]:
    """
    Stream tokens from the agentic RAG workflow.

    Args:
        question: The user's question
        llm: The language model to use
        rag_system: The initialized MultiModalRAGSystem
        result_collector: Optional mutable dict populated with the final graph state
                          (answer, sources, num_images, num_text_chunks) after all
                          tokens have been yielded. Used by the endpoint for logging.
        messages: Optional prior conversation turns as list of {role, content} dicts

    Yields:
        String tokens as they are generated
    """
    graph = build_agentic_rag_graph(llm, rag_system)

    initial_state = {
        "messages": _build_messages(question, messages),
        "retrieved_docs": [],
        "answer": "",
        "sources": [],
        "num_images": 0,
        "num_text_chunks": 0,
        "image_ids": [],
    }

    final_state: dict = {}
    agent_buffer: list = []
    vision_ran: bool = False

    async for mode, data in graph.astream(
        initial_state,
        stream_mode=["messages", "values"],
    ):
        if mode == "messages":
            chunk, metadata = data
            if getattr(chunk, "content", None):
                node = metadata.get("langgraph_node", "")
                if node == "vision_synthesis":
                    vision_ran = True
                    yield chunk.content   # stream vision tokens immediately
                else:
                    agent_buffer.append(chunk.content)   # buffer agent tokens
        elif mode == "values":
            final_state = data  # keep overwriting; last snapshot = final state

    # Text-only query: emit buffered agent tokens; vision query: discard buffer
    if not vision_ran:
        for token in agent_buffer:
            yield token

    # After all tokens are yielded, populate the collector with the final state
    if result_collector is not None:
        result_collector.update({
            "answer": final_state.get("answer", ""),
            "sources": final_state.get("sources", []),
            "num_images": final_state.get("num_images", 0),
            "num_text_chunks": final_state.get("num_text_chunks", 0),
        })
