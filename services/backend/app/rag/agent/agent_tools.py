"""
Agent tools for the Agentic RAG system.
"""

from langchain.tools import Tool
from langchain_core.language_models import BaseChatModel
from ..core.rag_manager import MultiModalRAGSystem
from ..core.config import HybridSearchConfig
from .query_enhancer import enhance_query, decompose_query, generate_hypothetical_answer
import asyncio
from typing import Optional, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack


def create_rag_retriever_tool(rag_system: MultiModalRAGSystem) -> Tool:
    """
    Create a LangChain tool for the multimodal RAG retriever.

    Args:
        rag_system: The MultiModalRAGSystem instance

    Returns:
        Tool: LangChain tool for document retrieval
    """

    def search_document(query: str) -> str:
        """
        Search the loaded PDF document for information. This tool can understand both
        text and images in the document. Use this when the question requires information
        from the loaded document.

        Args:
            query: The question to search for in the document

        Returns:
            Retrieved context with citations
        """
        try:
            # Query the RAG system
            result = rag_system.query(query, k=5)

            # Format the response
            retrieved_docs = result["retrieved_docs"]
            sources = result["sources"]

            if not retrieved_docs:
                return "No relevant information found in the document."

            # Build context string
            context_parts = []

            # Add text chunks
            text_docs = [doc for doc in retrieved_docs if doc.metadata.get("type") == "text"]
            if text_docs:
                context_parts.append("Text Content:")
                for doc in text_docs:
                    page = doc.metadata.get("page", "N/A")
                    content = doc.page_content.strip()
                    context_parts.append(f"\n[Page {page}]: {content}")

            # Add image references
            image_docs = [doc for doc in retrieved_docs if doc.metadata.get("type") == "image"]
            if image_docs:
                context_parts.append("\n\nImages Found:")
                for doc in image_docs:
                    page = doc.metadata.get("page", "N/A")
                    image_id = doc.metadata.get("image_id", "N/A")
                    context_parts.append(f"\n[Page {page}]: Image {image_id}")

            # Add metadata
            context_parts.append(
                f"\n\n[Retrieved {result['num_text_chunks']} text chunks and "
                f"{result['num_images']} images from pages: "
                f"{', '.join(set(str(s['page']) for s in sources))}]"
            )

            return "\n".join(context_parts)

        except Exception as e:
            return f"Error searching document: {str(e)}"

    return Tool(
        name="search_document",
        func=search_document,
        description=(
            "Useful for answering questions about the loaded PDF document. "
            "This tool can find information from both text and images in the document. "
            "Input should be a clear question about the document content. "
            "Use this tool when you need specific information, diagrams, "
            "charts, or any content that might be in the document."
        )
    )

# basic initialization of notion mcp server
# async def connect_to_notion_server(command, args, notion_api_key):
#     """
#     This is a Notion tool for
#     """
#     # initialize the server
#     server_params = StdioServerParameters(
#         command=command,
#         args=[args],
#         env=notion_api_key
#     )

#     stdio_transport = await AsyncExitStack().enter_async_context(stdio_client(server_params))
#     stdio, write = stdio_transport
#     Optional[ClientSession] = await AsyncExitStack().enter_async_context(ClientSession(stdio, write))

#     await Optional[ClientSession].initialize()

#     # List the available tools
#     response = await Optional[ClientSession].list_tools()
#     tools = response.tools
#     print(f"\nConnected to server with tools:", [tool.name for tool in tools])


def create_query_enhancer_tool(llm: BaseChatModel) -> Tool:
    """
    Create a LangChain tool for query expansion/enhancement.

    Args:
        llm: The language model to use for query expansion

    Returns:
        Tool: LangChain tool for query enhancement
    """

    def expand_query(query: str) -> str:
        """
        Expand a vague or ambiguous query into multiple specific variations.
        Use this when the initial query is too broad, vague, or might miss relevant information.

        This helps improve search recall by generating alternative phrasings of the same question.

        Args:
            query: The query to expand (should be a single question or search term)

        Returns:
            String containing the original query and its variations

        When to use:
        - Query is vague (e.g., "main points", "key findings")
        - Query uses general terms that could be phrased differently
        - You want to ensure comprehensive coverage of a topic

        When NOT to use:
        - Query is already very specific (e.g., "accuracy on ImageNet dataset")
        - Query contains exact identifiers (e.g., "Figure 3", "Table 2")
        """
        try:
            if not HybridSearchConfig.QUERY_EXPANSION_ENABLED:
                return f"Query expansion is disabled. Original query: {query}"

            # Generate query variations
            variations = enhance_query(query, llm)

            # Format the response
            response_parts = [
                f"Original Query: {query}",
                "",
                "Expanded Variations:",
            ]

            for i, var in enumerate(variations[1:], 1):  # Skip original
                response_parts.append(f"{i}. {var}")

            response_parts.append("")
            response_parts.append("Suggestion: Use these variations with the search_document tool to find more comprehensive results.")

            return "\n".join(response_parts)

        except Exception as e:
            return f"Error expanding query: {str(e)}"

    return Tool(
        name="expand_query",
        func=expand_query,
        description=(
            "Useful for expanding vague or ambiguous queries into multiple specific variations. "
            "This improves search recall by generating alternative ways to phrase the same question. "
            "Use this BEFORE searching when the query is general or might be expressed in different ways. "
            "Input should be a single query string. "
            "Output will be multiple variations you can then use with search_document."
        )
    )


def create_query_decomposer_tool(llm: BaseChatModel) -> Tool:
    """
    Create a LangChain tool for query decomposition.

    Args:
        llm: The language model to use for query decomposition

    Returns:
        Tool: LangChain tool for query decomposition
    """

    def decompose_complex_query(query: str) -> str:
        """
        Break down a complex, multi-part query into simpler sub-queries.
        Use this when the query asks multiple things or requires comparison.

        Args:
            query: The complex query to decompose

        Returns:
            String containing the sub-queries

        When to use:
        - Query asks multiple questions (e.g., "What are X and Y?")
        - Query requires comparison (e.g., "Compare A and B")
        - Query has multiple aspects (e.g., "accuracy and speed")

        When NOT to use:
        - Query is simple and focused
        - Query asks only one thing
        """
        try:
            if not HybridSearchConfig.QUERY_EXPANSION_ENABLED:
                return f"Query expansion is disabled. Original query: {query}"

            # Decompose the query
            sub_queries = decompose_query(query, llm)

            # Format the response
            response_parts = [
                f"Original Complex Query: {query}",
                "",
                "Decomposed Sub-Queries:",
            ]

            for i, sub_q in enumerate(sub_queries, 1):
                response_parts.append(f"{i}. {sub_q}")

            response_parts.append("")
            response_parts.append("Suggestion: Search each sub-query separately with search_document, then synthesize the results.")

            return "\n".join(response_parts)

        except Exception as e:
            return f"Error decomposing query: {str(e)}"

    return Tool(
        name="decompose_query",
        func=decompose_complex_query,
        description=(
            "Useful for breaking down complex, multi-part queries into simpler sub-queries. "
            "Use this when the question asks multiple things, requires comparison, or has multiple aspects. "
            "Input should be a complex query string. "
            "Output will be simpler sub-queries you can search individually."
        )
    )


def get_agent_tools(rag_system: MultiModalRAGSystem, llm: Optional[BaseChatModel] = None) -> list:
    """
    Get all tools for the agent.

    Args:
        rag_system: The MultiModalRAGSystem instance
        llm: Optional language model for query enhancement tools

    Returns:
        List of tools
    """
    tools = [create_rag_retriever_tool(rag_system)]

    # Add query enhancement tools if LLM is provided and expansion is enabled
    if llm is not None and HybridSearchConfig.QUERY_EXPANSION_ENABLED:
        tools.append(create_query_enhancer_tool(llm))
        tools.append(create_query_decomposer_tool(llm))

    return tools
