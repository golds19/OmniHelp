"""
Tests for vision_node.py — multimodal synthesis after agent tool calls.
"""
import os
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-placeholder")

import pytest
from unittest.mock import MagicMock
from langchain_core.messages import HumanMessage, AIMessage
from app.rag.agent.vision_node import create_vision_synthesis_node

# Minimal valid 1×1 transparent PNG, base64-encoded
TINY_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@pytest.fixture
def mock_rag_system():
    ras = MagicMock()
    ras.image_data_store = {
        "page_2_img_0": TINY_B64,
        "page_5_img_1": TINY_B64,
    }
    return ras


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.invoke.return_value = AIMessage(content="Vision-aware answer describing the chart.")
    return llm


def _make_state(**overrides):
    base = {
        "messages": [HumanMessage(content="Describe Figure 1")],
        "answer": "Draft answer.",
        "image_ids": [],
        "sources": [],
        "num_images": 0,
        "num_text_chunks": 0,
        "retrieved_docs": [],
    }
    base.update(overrides)
    return base


class TestVisionSynthesisNode:

    def test_no_op_when_image_ids_empty(self, mock_rag_system, mock_llm):
        """Node does nothing when image_ids is empty — answer unchanged, llm not called."""
        node = create_vision_synthesis_node(mock_rag_system, mock_llm)
        state = _make_state(image_ids=[], answer="I found some text.")
        result = node(state)

        mock_llm.invoke.assert_not_called()
        assert result["answer"] == "I found some text."

    def test_calls_llm_with_text_and_image_url_blocks(self, mock_rag_system, mock_llm):
        """Node builds a multimodal HumanMessage with both text and image_url content blocks."""
        node = create_vision_synthesis_node(mock_rag_system, mock_llm)
        state = _make_state(
            image_ids=["page_2_img_0"],
            answer="An image was found on page 2.",
        )
        node(state)

        mock_llm.invoke.assert_called_once()
        args = mock_llm.invoke.call_args[0][0]
        assert len(args) == 1
        msg = args[0]
        assert isinstance(msg, HumanMessage)
        content_types = [block["type"] for block in msg.content]
        assert "text" in content_types
        assert "image_url" in content_types

    def test_updates_answer_with_llm_response(self, mock_rag_system, mock_llm):
        """State answer is replaced with the LLM's vision-aware response."""
        node = create_vision_synthesis_node(mock_rag_system, mock_llm)
        state = _make_state(
            image_ids=["page_2_img_0"],
            answer="Draft: an image was found.",
        )
        result = node(state)

        assert result["answer"] == "Vision-aware answer describing the chart."

    def test_no_op_when_image_ids_not_in_store(self, mock_rag_system, mock_llm):
        """Image IDs absent from image_data_store resolve to nothing — node skips LLM call."""
        node = create_vision_synthesis_node(mock_rag_system, mock_llm)
        state = _make_state(
            image_ids=["page_99_img_0"],  # not present in mock_rag_system.image_data_store
            answer="Original draft.",
        )
        result = node(state)

        mock_llm.invoke.assert_not_called()
        assert result["answer"] == "Original draft."

    def test_multiple_images_included_in_message(self, mock_rag_system, mock_llm):
        """All resolved image IDs appear as image_url blocks in the LLM message."""
        node = create_vision_synthesis_node(mock_rag_system, mock_llm)
        state = _make_state(
            image_ids=["page_2_img_0", "page_5_img_1"],
            answer="Two images found.",
        )
        node(state)

        msg = mock_llm.invoke.call_args[0][0][0]
        image_blocks = [b for b in msg.content if b["type"] == "image_url"]
        assert len(image_blocks) == 2
