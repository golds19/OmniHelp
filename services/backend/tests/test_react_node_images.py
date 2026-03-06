"""
Tests for image_id extraction logic in react_node.agent_node().

agent_node() parses tool observations for "Images Found:" sections and extracts
specific image IDs (e.g. "page_2_img_0") into the returned state's image_ids list.
These are used by the vision_synthesis node downstream.
"""
import os
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-placeholder")

import pytest
from unittest.mock import MagicMock
from langchain_core.messages import HumanMessage
from app.rag.agent.react_node import agent_node


def _make_executor(observations: list, answer: str = "Final answer."):
    """Return a mock AgentExecutor that yields the given tool observation strings."""
    mock_executor = MagicMock()
    intermediate_steps = [(MagicMock(), obs) for obs in observations]
    mock_executor.invoke.return_value = {
        "output": answer,
        "intermediate_steps": intermediate_steps,
    }
    return mock_executor


def _base_state(**overrides):
    state = {
        "messages": [HumanMessage(content="What does Figure 1 show?")],
        "retrieved_docs": [],
        "answer": "",
        "sources": [],
        "num_images": 0,
        "num_text_chunks": 0,
        "image_ids": [],
    }
    state.update(overrides)
    return state


class TestAgentNodeImageParsing:

    def test_parses_image_ids_from_observation(self):
        """image_ids are extracted from 'Images Found:' lines in tool observations."""
        obs = (
            "Text Content:\n[Page 1]: Some introductory text.\n\n"
            "Images Found:\n[Page 2]: Image page_2_img_0\n[Page 5]: Image page_5_img_1"
        )
        executor = _make_executor([obs])
        result = agent_node(_base_state(), executor)

        assert result["image_ids"] == ["page_2_img_0", "page_5_img_1"]

    def test_empty_image_ids_when_no_images_found(self):
        """image_ids is empty when tool output contains only text chunks."""
        obs = "Text Content:\n[Page 1]: Machine learning is a subset of AI."
        executor = _make_executor([obs])
        result = agent_node(_base_state(), executor)

        assert result["image_ids"] == []
        assert result["num_images"] == 0

    def test_num_images_matches_image_references(self):
        """num_images equals the count of [Page X]: Image lines parsed."""
        obs = (
            "Images Found:\n"
            "[Page 3]: Image page_3_img_0\n"
            "[Page 3]: Image page_3_img_1"
        )
        executor = _make_executor([obs])
        result = agent_node(_base_state(), executor)

        assert result["num_images"] == 2
        assert len(result["image_ids"]) == 2

    def test_image_ids_aggregated_across_multiple_tool_calls(self):
        """image_ids from multiple tool observations are merged into a single list."""
        obs1 = "Images Found:\n[Page 1]: Image page_1_img_0"
        obs2 = "Images Found:\n[Page 4]: Image page_4_img_0"
        executor = _make_executor([obs1, obs2])
        result = agent_node(_base_state(), executor)

        assert "page_1_img_0" in result["image_ids"]
        assert "page_4_img_0" in result["image_ids"]
        assert result["num_images"] == 2

    def test_answer_populated_from_executor_output(self):
        """The 'answer' field in state is set from agent_executor output."""
        executor = _make_executor([], answer="The chart shows revenue growth.")
        result = agent_node(_base_state(), executor)

        assert result["answer"] == "The chart shows revenue growth."
