"""
Simple ReAct Agent with MCP FileSystem Integration
"""
from langchain_openai import ChatOpenAI
from typing import List, Dict
import os
from dotenv import load_dotenv
import asyncio

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

class ReActMCPAgent:
    def __init__(self, command: str, mcp_args_path: List, workspace_dir: str):
        self.model = ChatOpenAI(model="gpt-4o-mini")
        self.command = command
        self.mcp_args_path = mcp_args_path
        self.workspace_dir = workspace_dir

    async def connect_mcp(self):
        """Connect to MCP filesystem"""
        server_params = StdioServerParameters(
            command=self.command,
            args=self.mcp_args_path,
            env=None
        )

        self._stdio_cm = stdio_client(server_params)
        read, write = await self._stdio_cm.__aenter__()

        self._session_cm = ClientSession(read, write)
        self.mcp_session = await self._session_cm.__aenter__()
        await self.mcp_session.initialize()

        self.mcp_tools = await self.mcp_session.list_tools()
        print(f"\nConnected to MCP. Available tools: {[t.name for t in self.mcp_tools.tools]}")

    async def close(self):
        """Clean up MCP connection"""
        if hasattr(self, '_session_cm'):
            await self._session_cm.__aexit__(None, None, None)
        if hasattr(self, '_stdio_cm'):
            await self._stdio_cm.__aexit__(None, None, None)

    def create_tools(self) -> List:
        """Create simple tool wrappers for MCP tools"""
        session = self.mcp_session

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

        return [read_text_file, write_file]

    async def run(self, user_query: str):
        tools = self.create_tools()

        system_prompt = """You are a filesystem assistant. Use the tools to read and write files.
Always execute operations immediately without asking for confirmation."""

        agent = create_react_agent(self.model, tools, prompt=system_prompt)

        result = await agent.ainvoke({
            "messages": [("user", user_query)]
        })

        return result["messages"][-1].content

async def main():
    WORKSPACE = r"C:\Research Folder\AI Projects\Lifeforge\services\backend\app\notebooks\mcp_workspace"
    os.makedirs(WORKSPACE, exist_ok=True)
    print(f"Workspace: {WORKSPACE}")

    agent = ReActMCPAgent(
        command="npx",
        mcp_args_path=["-y", "@modelcontextprotocol/server-filesystem", WORKSPACE],
        workspace_dir=WORKSPACE
    )

    try:
        await agent.connect_mcp()

        query = "Create a file called 'test.txt' with the content 'Hello There! From ReAct agent'"
        result = await agent.run(query)
        print(f"\nAgent response:\n{result}")

    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main())
