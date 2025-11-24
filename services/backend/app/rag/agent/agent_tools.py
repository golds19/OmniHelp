"""
Agent tools for the Agentic RAG system.
"""

from langchain.tools import Tool
from ..core.rag_manager import MultiModalRAGSystem
import asyncio
from typing import Optional
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


def get_agent_tools(rag_system: MultiModalRAGSystem) -> list:
    """
    Get all tools for the agent.

    Args:
        rag_system: The MultiModalRAGSystem instance

    Returns:
        List of tools
    """
    return [create_rag_retriever_tool(rag_system)]
