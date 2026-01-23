#!/usr/bin/env python3
"""Confluence Assistant - Streamlined POC for querying Confluence via CData Connect AI."""

import os
import json
import base64
import sys
import asyncio
import requests
from dotenv import load_dotenv
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool, create_sdk_mcp_server
from functools import partial

load_dotenv()

# Custom system prompt for Confluence assistant
SYSTEM_PROMPT = """You are an internal assistant with **read-only access to Confluence documentation**.

* Always summarize content instead of returning large raw text blocks
* Always indicate that information comes from Confluence
* Structure responses with headings and bullet points
* If information is missing or unclear, explicitly state that
* Do not output sensitive or personal data
* You can only READ from Confluence - you cannot write or modify anything"""


class MCPClient:
    """Client for interacting with CData Connect AI MCP server over HTTP."""
    
    def __init__(self, server_url: str, email: str = None, access_token: str = None):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        
        # Set default headers for MCP JSON-RPC
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'User-Agent': f'CDataConnectAI-ClaudeAgent (Python/{sys.version_info.major}.{sys.version_info.minor})',
        })
        
        if email and access_token:
            # Basic authentication: email:personal_access_token
            credentials = f"{email}:{access_token}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            self.session.headers.update({
                'Authorization': f'Basic {encoded_credentials}'
            })
    
    def _parse_sse_response(self, response_text: str) -> dict:
        """Parse Server-Sent Events (SSE) response."""
        for line in response_text.split('\n'):
            if line.startswith('data: '):
                return json.loads(line[6:])
        raise ValueError("No data found in SSE response")
    
    def list_tools(self) -> list:
        """Get available tools from the MCP server."""
        response = self.session.post(
            self.server_url,
            json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}
        )
        response.raise_for_status()
        result = self._parse_sse_response(response.text)
        return result.get("result", {}).get("tools", [])
    
    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Call a tool on the MCP server."""
        response = self.session.post(
            self.server_url,
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
                "id": 2
            }
        )
        response.raise_for_status()
        result = self._parse_sse_response(response.text)
        return result.get("result", {})


class ConfluenceAgentChatbot:
    """Confluence-focused AI agent chatbot using CData Connect AI."""
    
    def __init__(self, mcp_server_url: str, email: str = None, access_token: str = None):
        self.mcp_client = MCPClient(mcp_server_url, email, access_token)
        
        # Load available tools from MCP server
        print("🔌 Connecting to CData Connect AI MCP server...")
        self.mcp_tools_list = self.mcp_client.list_tools()
        print(f"✅ Loaded {len(self.mcp_tools_list)} tools from MCP server")
        
        # Show available tools
        print("\n📋 Available tools:")
        for tool_info in self.mcp_tools_list[:10]:  # Show first 10
            print(f"   - {tool_info.get('name')}")
        if len(self.mcp_tools_list) > 10:
            print(f"   ... and {len(self.mcp_tools_list) - 10} more")
        
        # Create Agent SDK tool wrappers
        self.agent_tools = self._create_agent_tools()
        
        # Create MCP server for Agent SDK
        self.mcp_server = create_sdk_mcp_server(
            name="cdata_connect",
            tools=self.agent_tools
        )
    
    async def _tool_handler(self, tool_name: str, args: dict) -> dict:
        """Call the MCP tool and return results."""
        result = self.mcp_client.call_tool(tool_name, args)
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, indent=2)
            }]
        }
    
    def _create_agent_tools(self) -> list:
        """Create Agent SDK tool wrappers for MCP tools."""
        agent_tools = []
        for tool_info in self.mcp_tools_list:
            tool_name = tool_info.get("name")
            tool_description = tool_info.get("description", "")
            tool_schema = tool_info.get("inputSchema", {})
            
            agent_tool = tool(
                name=tool_name,
                description=tool_description,
                input_schema=tool_schema
            )(partial(self._tool_handler, tool_name))
            
            agent_tools.append(agent_tool)
        return agent_tools
    
    def create_session(self) -> ClaudeSDKClient:
        """Create a stateful conversation session."""
        options = ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            mcp_servers={"cdata_connect": self.mcp_server},
            permission_mode="bypassPermissions"  # Auto-approve for CLI
        )
        return ClaudeSDKClient(options=options)
    
    async def chat_session(self, client: ClaudeSDKClient, user_message: str) -> str:
        """Send a message in a stateful session."""
        await client.query(user_message)
        async for message in client.receive_response():
            if hasattr(message, 'result'):
                return str(message.result)
        return ""


async def interactive_mode(chatbot):
    """Run the chatbot in interactive mode with stateful sessions."""
    print("\n🤖 Confluence Assistant Ready!")
    print("💡 Try: 'What Confluence spaces are available to me?'")
    print("💡 Type 'quit' to exit.\n")
    
    # Create a stateful session
    client = chatbot.create_session()
    
    # Use async context manager for proper resource cleanup
    async with client:
        while True:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            print("\n🤔 Thinking...")
            response = await chatbot.chat_session(client, user_input)
            print(f"\n📄 Assistant:\n{response}\n")


async def main():
    """Run the chatbot in interactive mode."""
    MCP_SERVER_URL = "https://mcp.cloud.cdata.com/mcp/"
    CDATA_EMAIL = os.environ.get("CDATA_EMAIL")
    CDATA_ACCESS_TOKEN = os.environ.get("CDATA_ACCESS_TOKEN")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    
    # Validate environment variables
    if not CDATA_EMAIL:
        print("❌ Error: CDATA_EMAIL not set in .env file")
        return
    if not CDATA_ACCESS_TOKEN:
        print("❌ Error: CDATA_ACCESS_TOKEN not set in .env file")
        return
    if not ANTHROPIC_API_KEY:
        print("❌ Error: ANTHROPIC_API_KEY not set in .env file")
        return
    
    print("=" * 60)
    print("🚀 Claude Confluence Assistant")
    print("=" * 60)
    print(f"📡 MCP Server: {MCP_SERVER_URL}\n")
    
    chatbot = ConfluenceAgentChatbot(MCP_SERVER_URL, CDATA_EMAIL, CDATA_ACCESS_TOKEN)
    await interactive_mode(chatbot)


if __name__ == "__main__":
    asyncio.run(main())