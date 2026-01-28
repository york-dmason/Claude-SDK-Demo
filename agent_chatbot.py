#!/usr/bin/env python3
"""
Confluence Assistant - AI agent for querying Confluence, Jira, and GitHub via CData Connect AI.
Integrates with TSG Capacity Management Tool for active projects filtering.
"""

import os
import json
import base64
import sys
import asyncio
import requests
from dotenv import load_dotenv
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, tool, create_sdk_mcp_server
from functools import partial

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.active_projects_cache import active_projects_cache
from scripts.active_projects_tools import (
    get_active_projects_tool_definitions,
    get_active_projects_tool_handlers,
)
from scripts.system_prompts import build_scalable_system_prompt, LEGACY_SYSTEM_PROMPT

load_dotenv()


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
    """
    AI agent chatbot using CData Connect AI for Confluence, Jira, and GitHub.
    Integrates active projects filtering from TSG Capacity Management Tool.
    """
    
    def __init__(self, mcp_server_url: str, email: str = None, access_token: str = None):
        self.mcp_client = MCPClient(mcp_server_url, email, access_token)
        
        # Load available tools from MCP server (CData)
        print("Connecting to CData Connect AI MCP server...")
        self.mcp_tools_list = self.mcp_client.list_tools()
        print(f"Loaded {len(self.mcp_tools_list)} tools from CData MCP server")
        
        # Get active projects tool definitions
        self.active_projects_tool_defs = get_active_projects_tool_definitions()
        self.active_projects_handlers = get_active_projects_tool_handlers()
        
        # Show available tools
        print("\nAvailable tools:")
        print("  [CData Connect AI]")
        for tool_info in self.mcp_tools_list[:8]:  # Show first 8 CData tools
            print(f"    - {tool_info.get('name')}")
        if len(self.mcp_tools_list) > 8:
            print(f"    ... and {len(self.mcp_tools_list) - 8} more")
        
        print("  [Active Projects (TCM)]")
        for tool_def in self.active_projects_tool_defs:
            print(f"    - {tool_def.get('name')}")
        
        # Create Agent SDK tool wrappers (CData + Active Projects)
        self.agent_tools = self._create_agent_tools()
        
        # Create MCP server for Agent SDK
        self.mcp_server = create_sdk_mcp_server(
            name="cdata_connect",
            tools=self.agent_tools
        )
    
    async def _cdata_tool_handler(self, tool_name: str, args: dict) -> dict:
        """Call a CData MCP tool and return results."""
        result = self.mcp_client.call_tool(tool_name, args)
        return {
            "content": [{
                "type": "text",
                "text": json.dumps(result, indent=2)
            }]
        }
    
    async def _active_projects_tool_handler(self, tool_name: str, args: dict) -> dict:
        """Call an active projects tool and return results."""
        handler = self.active_projects_handlers.get(tool_name)
        if handler:
            return await handler(args)
        return {
            "content": [{
                "type": "text",
                "text": f"Unknown tool: {tool_name}"
            }]
        }
    
    def _create_agent_tools(self) -> list:
        """Create Agent SDK tool wrappers for all tools (CData + Active Projects)."""
        agent_tools = []
        
        # Wrap CData MCP tools
        for tool_info in self.mcp_tools_list:
            tool_name = tool_info.get("name")
            tool_description = tool_info.get("description", "")
            tool_schema = tool_info.get("inputSchema", {})
            
            agent_tool = tool(
                name=tool_name,
                description=tool_description,
                input_schema=tool_schema
            )(partial(self._cdata_tool_handler, tool_name))
            
            agent_tools.append(agent_tool)
        
        # Wrap Active Projects tools
        for tool_def in self.active_projects_tool_defs:
            tool_name = tool_def.get("name")
            tool_description = tool_def.get("description", "")
            tool_schema = tool_def.get("inputSchema", {})
            
            agent_tool = tool(
                name=tool_name,
                description=tool_description,
                input_schema=tool_schema
            )(partial(self._active_projects_tool_handler, tool_name))
            
            agent_tools.append(agent_tool)
        
        return agent_tools
    
    def create_session(self, system_prompt: str = None) -> ClaudeSDKClient:
        """
        Create a stateful conversation session.
        
        Args:
            system_prompt: Custom system prompt (uses default if not provided)
        """
        prompt = system_prompt or LEGACY_SYSTEM_PROMPT
        options = ClaudeAgentOptions(
            system_prompt=prompt,
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


async def interactive_mode(chatbot, system_prompt: str = None):
    """
    Run the chatbot in interactive mode with stateful sessions.
    
    Args:
        chatbot: The ConfluenceAgentChatbot instance
        system_prompt: Custom system prompt to use for the session
    """
    print("\n" + "=" * 60)
    print("Assistant Ready!")
    print("=" * 60)
    print("\nExample queries:")
    print("  - 'What active projects do we have?'")
    print("  - 'Tell me about the Thrivent project'")
    print("  - 'What Confluence pages exist for Medtronic?'")
    print("  - 'Is Acme Corp an active project?'")
    print("\nType 'quit' to exit.\n")
    
    # Create a stateful session with the dynamic system prompt
    client = chatbot.create_session(system_prompt=system_prompt)
    
    # Use async context manager for proper resource cleanup
    async with client:
        while True:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            print("\nThinking...")
            response = await chatbot.chat_session(client, user_input)
            print(f"\nAssistant:\n{response}\n")


async def main():
    """Run the chatbot in interactive mode with active projects integration."""
    MCP_SERVER_URL = "https://mcp.cloud.cdata.com/mcp/"
    CDATA_EMAIL = os.environ.get("CDATA_EMAIL")
    CDATA_ACCESS_TOKEN = os.environ.get("CDATA_ACCESS_TOKEN")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    
    # Validate environment variables
    if not CDATA_EMAIL:
        print("Error: CDATA_EMAIL not set in .env file")
        return
    if not CDATA_ACCESS_TOKEN:
        print("Error: CDATA_ACCESS_TOKEN not set in .env file")
        return
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not set in .env file")
        return
    
    print("=" * 60)
    print("Claude Agent - Active Projects Assistant")
    print("=" * 60)
    print(f"CData MCP Server: {MCP_SERVER_URL}\n")
    
    # Load active projects from TSG Capacity Management Tool
    print("Loading active projects from TSG Capacity Management Tool...")
    try:
        project_count = active_projects_cache.load()
        sample_names = active_projects_cache.get_sample_names(10)
        print(f"Loaded {project_count} active projects/clients")
        print(f"Sample: {', '.join(sample_names[:5])}...")
    except Exception as e:
        print(f"Warning: Could not load active projects: {e}")
        print("Continuing without active projects filtering...")
        project_count = 0
        sample_names = []
    
    # Build dynamic system prompt with active projects context
    system_prompt = build_scalable_system_prompt(project_count, sample_names)
    
    print()  # Blank line before chatbot init
    
    # Initialize chatbot with CData tools + Active Projects tools
    chatbot = ConfluenceAgentChatbot(MCP_SERVER_URL, CDATA_EMAIL, CDATA_ACCESS_TOKEN)
    
    # Start interactive mode with the dynamic system prompt
    await interactive_mode(chatbot, system_prompt=system_prompt)


if __name__ == "__main__":
    asyncio.run(main())