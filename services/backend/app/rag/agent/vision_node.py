"""
Vision synthesis node for the Agentic RAG system.

Runs after the agent node when images were retrieved. Passes the actual
base64 image data to the LLM so it can visually reason about figures,
charts, and diagrams — something the text-only agent executor cannot do.
"""
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from ..core.rag_manager import MultiModalRAGSystem
from .rag_state import AgenticRAGState


def create_vision_synthesis_node(rag_system: MultiModalRAGSystem, llm: ChatOpenAI):
    """
    Create a LangGraph node that performs multimodal synthesis.

    Only runs when the agent node found image_ids in retrieved results.
    Builds a multimodal HumanMessage (text + base64 images) and calls the
    LLM to produce a vision-aware final answer.
    """
    def vision_synthesis(state: AgenticRAGState) -> AgenticRAGState:
        image_ids = state.get("image_ids", [])
        if not image_ids:
            return state

        # Resolve base64 images from the session store
        images_b64 = [
            (iid, rag_system.image_data_store[iid])
            for iid in image_ids
            if iid in rag_system.image_data_store
        ]
        if not images_b64:
            return state

        question = state["messages"][-1].content if state["messages"] else ""
        draft_answer = state.get("answer", "")

        content = [
            {
                "type": "text",
                "text": (
                    f"Question: {question}\n\n"
                    f"Text analysis from the document:\n{draft_answer}\n\n"
                    "Now examine the following images from the document. "
                    "Provide a complete answer that incorporates both the "
                    "text context above and what you observe in the images:"
                ),
            }
        ]
        for image_id, b64 in images_b64:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64}"},
            })
        content.append({
            "type": "text",
            "text": "Provide a comprehensive, well-cited answer to the original question.",
        })

        response = llm.invoke([HumanMessage(content=content)])
        return {**state, "answer": response.content}

    return vision_synthesis
