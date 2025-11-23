"""
ReAct agent node for the Agentic RAG system.
"""

from typing import List
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain_core.messages import HumanMessage
from .rag_state import AgenticRAGState


def create_react_prompt() -> PromptTemplate:
    """
    Create the ReAct prompt template for the agent.

    Returns:
        PromptTemplate: Prompt template for ReAct agent
    """
    template = """You are an intelligent assistant helping users understand PDF documents.
You have access to tools that can search through document content including text and images.

Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Important guidelines:
- Always search the document first before answering
- Use specific quotes from the document when possible
- Cite page numbers in your answer
- If you find images, mention them in your answer
- Be concise but thorough

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

    return PromptTemplate.from_template(template)


def create_agent_executor(llm: ChatOpenAI, tools: List[Tool]) -> AgentExecutor:
    """
    Create the ReAct agent executor.

    Args:
        llm: The language model to use
        tools: List of tools available to the agent

    Returns:
        AgentExecutor: Configured agent executor
    """
    prompt = create_react_prompt()

    agent = create_react_agent(
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

    # Update state
    return {
        "messages": state["messages"],
        "answer": answer,
        "retrieved_docs": state.get("retrieved_docs", []),
        "sources": state.get("sources", []),
        "num_images": state.get("num_images", 0),
        "num_text_chunks": state.get("num_text_chunks", 0)
    }
