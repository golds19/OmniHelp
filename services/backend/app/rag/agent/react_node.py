"""
Tool-calling agent node for the Agentic RAG system.
Uses LangChain's tool-calling agent for better compatibility with modern LLMs.
"""

import re
from typing import List
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from .rag_state import AgenticRAGState


def create_agent_prompt() -> ChatPromptTemplate:
    """
    Create the prompt template for the tool-calling agent.

    Returns:
        ChatPromptTemplate: Prompt template for the agent
    """
    return ChatPromptTemplate.from_messages([
        ("system", """You are an intelligent assistant helping users understand PDF documents.
You have access to tools that can search through document content including text and images.

Important guidelines:
- Always search the document first before answering questions
- Use specific quotes from the document when possible
- Cite page numbers in your answer (e.g., "According to page 3...")
- If you find relevant images, mention them in your answer
- Be concise but thorough
- If the document doesn't contain the answer, say so clearly"""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])


def create_agent_executor(llm: ChatOpenAI, tools: List[BaseTool]) -> AgentExecutor:
    """
    Create the tool-calling agent executor.

    Args:
        llm: The language model to use
        tools: List of tools available to the agent

    Returns:
        AgentExecutor: Configured agent executor
    """
    prompt = create_agent_prompt()

    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )

    return agent_executor


def agent_node(state: AgenticRAGState, agent_executor: AgentExecutor) -> AgenticRAGState:
    """
    Execute the agent and update the state.

    Args:
        state: Current state of the workflow
        agent_executor: The agent executor to run

    Returns:
        Updated state
    """
    # Get the user's question from messages
    messages = state.get("messages", [])
    if not messages:
        raise ValueError("No messages in state")

    last_message = messages[-1]
    question = last_message.content if hasattr(last_message, "content") else str(last_message)

    # Run the agent
    result = agent_executor.invoke({"input": question})

    # Extract the answer and intermediate steps
    answer = result.get("output", "")
    intermediate_steps = result.get("intermediate_steps", [])

    # Extract sources from intermediate steps (tool outputs)
    sources = []
    num_images = 0
    num_text_chunks = 0

    for action, observation in intermediate_steps:
        # Parse the observation for page references
        if isinstance(observation, str):
            # Count text chunks and images from the observation
            if "Text Content:" in observation:
                # Count page references in text content
                page_matches = re.findall(r'\[Page (\d+)\]:', observation)
                for page in page_matches:
                    sources.append({"page": int(page), "type": "text"})
                    num_text_chunks += 1

            if "Images Found:" in observation:
                # Count image references
                image_matches = re.findall(r'\[Page (\d+)\]: Image', observation)
                for page in image_matches:
                    sources.append({"page": int(page), "type": "image"})
                    num_images += 1

    # Update state
    return {
        "messages": state["messages"],
        "answer": answer,
        "retrieved_docs": state.get("retrieved_docs", []),
        "sources": sources if sources else state.get("sources", []),
        "num_images": num_images if num_images else state.get("num_images", 0),
        "num_text_chunks": num_text_chunks if num_text_chunks else state.get("num_text_chunks", 0)
    }
