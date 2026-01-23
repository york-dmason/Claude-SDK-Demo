# Claude Agent SDK × Confluence POC

A proof-of-concept CLI application that uses Claude Agent SDK to query Confluence documentation through CData Connect AI's MCP (Model Context Protocol) server. This enables natural language Q&A over your Confluence content with read-only access.

---

## Project Brief

### What This Does

This POC demonstrates how Claude can safely query and summarize Confluence documentation using:
- **Claude Agent SDK** for AI agent capabilities
- **CData Connect AI** as an MCP server bridge
- **Confluence Cloud** as the data source (read-only)

The assistant can:
- Discover available Confluence spaces and pages
- Summarize project documentation
- Answer questions based on Confluence content
- Extract structured information (goals, scope, risks, decisions)

### Architecture

```
Claude Agent SDK (Python CLI)
        ↓
CData Connect AI (MCP Server)
        ↓
Confluence Cloud (Read-only)
```

### Key Features

- **Read-only access** - No modifications to Confluence
- **Dynamic tool discovery** - Automatically discovers available Confluence tables via MCP
- **Structured responses** - Summarized, readable output with source attribution
- **Stateful conversations** - Maintains context across multiple queries
- **Demo-safe** - Respects existing permissions, no data storage

### Constraints

- **Single data source:** Confluence only (no Jira, GitHub, etc.)
- **Read-only:** No write operations to Confluence
- **CLI-based:** Command-line interface only (no UI)
- **POC scope:** Not intended for production deployment

---

## Prerequisites

Before setting up locally, ensure you have:

1. **Python 3.8+** installed
2. **CData Connect AI account** with:
   - Email address
   - Personal Access Token
   - Confluence Cloud connection configured and authenticated
3. **Anthropic API key** for Claude Agent SDK
4. **Claude CLI** installed globally (optional, for SDK compatibility)

---

## Local Setup Instructions

### Step 1: Clone or Navigate to the Project

```bash
cd "/Users/yorkmacbook020/Desktop/York Solutions/January/Claude SDK Demo"
```

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `claude-agent-sdk` - Claude Agent SDK for Python
- `python-dotenv` - Environment variable management
- `requests` - HTTP client for MCP server communication

### Step 4: Install Claude CLI (Optional but Recommended)

```bash
npm install -g @anthropic-ai/claude-code
```

Verify installation:
```bash
which claude  # Should show path to claude executable
```

### Step 5: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Copy example if available, or create new file
cp .env.example .env  # If .env.example exists
# OR create manually:
touch .env
```

Add the following to your `.env` file:

```env
# CData Connect AI Credentials
CDATA_EMAIL=your-email@example.com
CDATA_ACCESS_TOKEN=your-personal-access-token

# Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

**Important:** 
- Never commit the `.env` file (it's in `.gitignore`)
- Get your CData credentials from your CData Connect AI account
- Get your Anthropic API key from https://console.anthropic.com/

### Step 6: Verify CData Connect AI Connection

Ensure your CData Connect AI account has:
- Confluence Cloud connection configured
- Connection status is "Authenticated"
- Read-only access permissions set

The MCP server URL is hardcoded to: `https://mcp.cloud.cdata.com/mcp/`

### Step 7: Run the Application

```bash
python agent_chatbot.py
```

You should see:
```
============================================================
Claude Confluence Assistant
============================================================
MCP Server: https://mcp.cloud.cdata.com/mcp/

Connecting to CData Connect AI MCP server...
Loaded X tools from MCP server

Available tools:
   - getInstructions
   - queryData
   - getCatalogs
   ...

Confluence Assistant Ready!
Try: 'What Confluence spaces are available to me?'
Type 'quit' to exit.
```

### Step 8: Test with Demo Prompts

Try these example queries:

- `What Confluence spaces are available to me?`
- `List recent pages related to project kickoff or scope.`
- `Summarize the Project Kickoff and Scope documentation.`
- `What decisions have already been made according to Confluence?`
- `What risks or open questions are documented?`

Type `quit` or `exit` to end the session.

---

## Project Structure

```
Claude SDK Demo/
├── .cursor/              # Cursor IDE rules and configuration
│   ├── rules            # Development constraints and guidelines
│   └── README.md        # Quick reference
├── .env                  # Environment variables (not in git)
├── .gitignore           # Git ignore rules
├── agent_chatbot.py     # Main application code
├── requirements.txt     # Python dependencies
├── README.md            # This file
└── credentials.md       # Credentials reference (not in git)
```

---

## How It Works

1. **MCP Client** (`MCPClient` class) connects to CData Connect AI's MCP server over HTTP
2. **Tool Discovery** dynamically loads available Confluence tools (queryData, getTables, etc.)
3. **Agent SDK Integration** wraps MCP tools for Claude Agent SDK
4. **Custom System Prompt** guides Claude to:
   - Summarize instead of dumping raw data
   - Always cite Confluence as the source
   - Structure responses clearly
   - Ask clarifying questions when needed
5. **Interactive Session** maintains conversation state for follow-up questions

---

## Troubleshooting

### Error: "CDATA_EMAIL not set in .env file"
- Ensure `.env` file exists in project root
- Verify all three environment variables are set
- Restart terminal after creating `.env` file

### Error: "Connection Issue" or "HTTP 400 Bad Request"
- Verify CData Connect AI connection is authenticated
- Check that Confluence connection is active in CData dashboard
- Ensure your CData credentials are correct

### Error: "ANTHROPIC_API_KEY not set"
- Get API key from https://console.anthropic.com/
- Add to `.env` file as `ANTHROPIC_API_KEY=sk-ant-api03-...`
- Ensure no extra spaces or quotes around the key

### No tools discovered
- Verify MCP server URL is accessible
- Check CData Connect AI account status
- Ensure Confluence connection is configured in CData

### Import errors
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`
- Verify Python version: `python3 --version` (should be 3.8+)

---

## Development Notes

### System Prompt

The custom system prompt (`SYSTEM_PROMPT`) in `agent_chatbot.py` ensures Claude:
- Operates in read-only mode
- Provides structured, summarized responses
- Always attributes information to Confluence
- Handles missing data gracefully

### MCP Server Communication

The application uses HTTP POST requests with JSON-RPC 2.0 protocol to communicate with CData Connect AI's MCP server. Server-Sent Events (SSE) responses are parsed to extract tool results.

### Stateful Conversations

Each interactive session maintains conversation state, allowing follow-up questions and context retention across multiple queries.

---

## Reference Documentation

- **CData Guide:** https://www.cdata.com/developers/ai/dev-guide-claude-agent-sdk-getting-started/
- **Claude Agent SDK:** https://platform.claude.com/docs/en/agent-sdk/quickstart
- **CData Connect AI:** https://cloud.cdata.com/

---

## Next Steps

Once the basic setup is working:

1. Test with real Confluence documentation
2. Refine system prompt for better responses
3. Add logging for tool calls and queries
4. Create demo script with pre-written prompts
5. Document any connection issues or improvements

---

## License & Usage

This is a proof-of-concept project. Use responsibly and ensure all credentials are kept secure. Never commit `.env` files or credentials to version control.
