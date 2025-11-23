# RAG Agent with MCP FileSystem Integration
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain.agents import Tool
from typing import List
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


class RAGAgent:
    def __init__(self, command: str, mcp_args: List, workspace_dir: str, pdf_path: str,
                 chunk_size: int = 500, chunk_overlap: int = 50):
        self.pdf_path = pdf_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.llm = ChatOpenAI(model="gpt-4o-mini")

        self.command = command
        self.mcp_args = mcp_args
        self.workspace = workspace_dir

        self.retriever = self._create_retriever()

    async def connect_to_mcp(self):
        """Connect to MCP filesystem"""
        server_params = StdioServerParameters(
            command=self.command,
            args=self.mcp_args,
            env=None
        )
        self._stdio_cm = stdio_client(server_params)
        read, write = await self._stdio_cm.__aenter__()

        self._session_cm = ClientSession(read, write)
        self.mcp_session = await self._session_cm.__aenter__()
        await self.mcp_session.initialize()

        tools_list = await self.mcp_session.list_tools()
        print(f"\nConnected to MCP. Available tools: {[t.name for t in tools_list.tools]}")

    async def close(self):
        """Clean up MCP connection"""
        if hasattr(self, '_session_cm'):
            await self._session_cm.__aexit__(None, None, None)
        if hasattr(self, '_stdio_cm'):
            await self._stdio_cm.__aexit__(None, None, None)

    def _create_retriever(self):
        """Load PDF and create vector store retriever"""
        docs = PyPDFLoader(self.pdf_path).load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        chunks = splitter.split_documents(docs)

        embedding = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = FAISS.from_documents(chunks, embedding)

        return vectorstore.as_retriever()

    def _create_tools(self):
        """Create all tools for the agent"""
        session = self.mcp_session
        retriever = self.retriever

        @tool
        async def read_text_file(path: str) -> str:
            """Read complete file contents as text"""
            result = await session.call_tool("read_text_file", {"path": path})
            return result.content[0].text if result.content else ""

        @tool
        async def write_file(path: str, content: str) -> str:
            """Create new or overwrite existing files"""
            result = await session.call_tool("write_file", {"path": path, "content": content})
            return result.content[0].text if result.content else "File written successfully"

        @tool
        def retrieve_knowledge(query: str) -> str:
            """Search the knowledge base for relevant information"""
            docs = retriever.invoke(query)
            return "\n".join([doc.page_content for doc in docs])

        return [retrieve_knowledge, read_text_file, write_file]

    async def run(self, query: str) -> str:
        """Run a query through the agent"""
        tools = self._create_tools()

        system_prompt = """You are a helpful assistant with access to a knowledge base and filesystem.

For questions requiring information:
1. Use retrieve_knowledge to search the knowledge base
2. Generate a comprehensive answer based on the retrieved information
3. Save the answer to a file using write_file

Always save your final answer to a .txt file in the workspace."""

        agent = create_react_agent(self.llm, tools, prompt=system_prompt)

        result = await agent.ainvoke({
            "messages": [("user", query)]
        })

        return result["messages"][-1].content


async def main():
    WORKSPACE = r"C:\Research Folder\AI Projects\Lifeforge\services\backend\app\notebooks\rag_mcp"
    os.makedirs(WORKSPACE, exist_ok=True)
    print(f"Workspace: {WORKSPACE}")

    agent = RAGAgent(
        command="npx",
        mcp_args=["-y", "@modelcontextprotocol/server-filesystem", WORKSPACE],
        workspace_dir=WORKSPACE,
        pdf_path="data/AI2Agent.pdf"
    )

    try:
        await agent.connect_to_mcp()

        query = "What is the AI2Agent framework about? Save your answer to answer.txt"
        result = await agent.run(query)
        print(f"\nAgent response:\n{result}")

    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
