# Claude Agent SDK × Confluence POC

**Project Context, Scope, and Next Steps**

---

## 1. What Has Already Been Completed

### Infrastructure & Access

* **CData Connect AI** is set up and authenticated
* **Confluence Cloud** is successfully connected using:
  * Atlassian API Token authentication
  * Read-only access
  * Existing user permissions (no admin access required)
* Connection status is **Authenticated**
* Confluence data model is visible, including tables such as:
  * `Spaces`
  * `Pages`
  * `PageChildren`
  * `PageAncestors`
  * `Comments`
  * `Attachments`

### Security & Governance

* No passwords are used
* No data is copied or stored outside Confluence
* Queries respect existing Confluence permissions
* This is a **read-only, demo-safe** configuration

### Intended AI Layer

* **Claude Agent SDK (Python)** will be used
* Claude will interact with Confluence **only via MCP tools exposed by CData**
* No direct Confluence API calls from the app

---

## 2. Current Architecture (As Built)

```
Claude Agent SDK (Python CLI)
        ↓
CData Connect AI (MCP Server)
        ↓
Confluence Cloud (Read-only)
```

Key characteristics:

* Claude dynamically discovers tools via MCP
* Claude issues structured queries against Confluence tables
* Claude receives results and produces synthesized, human-readable summaries

---

## 3. Project Scope (Defined & Locked)

### In Scope

* **Single data source:** Confluence only
* **Read-only access**
* CLI-based demo (no UI)
* Natural language queries over Confluence documentation
* Summarization, extraction, and Q&A over real company docs
* Clear source attribution in responses
* Safe, structured output (no raw dumps)

### Out of Scope

* Jira, GitHub, Microsoft 365 (future phases)
* Write operations or content updates
* Fine-tuning or training
* Production deployment
* Long-term storage or indexing
* Autonomous background agents

This is a **proof of concept**, not a production system.

---

## 4. Primary Demo Use Cases (What the POC Must Show)

### Use Case 1: Discovery

* List available Confluence spaces
* Describe what type of content exists in each

### Use Case 2: Project Understanding (Core Demo)

* Summarize "Project Kickoff" / "Project Scope" documentation
* Extract:
  * Goals
  * Scope
  * Known risks
  * Open questions
  * Next steps

### Use Case 3: Q&A Over Docs

* Answer follow-up questions using Confluence content
* Identify what is documented vs what is missing

---

## 5. Success Criteria (Definition of Done)

The POC is successful when:

* Claude can list Confluence spaces and pages
* Claude can summarize real project documentation accurately
* Claude can answer follow-up questions grounded in Confluence data
* Responses are:
  * Structured
  * Readable by non-technical stakeholders
  * Explicit about sources
* The demo can be run end-to-end locally via CLI

---

## 6. What Still Needs to Be Built

### Code-Level Work

1. Run the existing **Claude Agent SDK example project**
2. Confirm MCP tool discovery includes Confluence tables
3. Add a **custom system prompt** to guide behavior:
   * Read-only
   * Summarize, don't dump
   * Cite Confluence as source
   * Ask clarifying questions when data is missing
4. Add a small wrapper or helper to:
   * Encourage structured outputs
   * Keep responses consistent across demos

### Demo Prep

* Create 5–6 pre-written demo prompts
* Optionally add lightweight logging (tool called, table queried)

---

## 7. Instructions for Cursor (Very Important)

> **Cursor: you are working on a proof-of-concept using the Claude Agent SDK.
> The goal is to build a CLI-based internal assistant that queries Confluence via MCP (CData Connect AI) and produces structured summaries and Q&A responses.**

### Cursor Tasks (In Order)

1. Review the existing Claude Agent SDK example code
2. Identify where the agent is initialized
3. Add a custom **system prompt** aligned with the scope above
4. Ensure MCP tools are loaded dynamically
5. Test prompts that:
   * List Confluence spaces
   * Query pages
   * Summarize documentation
6. Refine output formatting for demos

### Constraints Cursor Must Respect

* Do NOT add new data sources
* Do NOT write to Confluence
* Do NOT store data locally
* Do NOT expose credentials
* Keep everything demo-safe and readable

---

## 8. Suggested System Prompt (Cursor Can Refine)

> You are an internal assistant with **read-only access to Confluence documentation**.
>
> * Always summarize content instead of returning large raw text blocks
> * Always indicate that information comes from Confluence
> * Structure responses with headings and bullet points
> * If information is missing or unclear, explicitly state that
> * Do not output sensitive or personal data

---

## 9. Suggested Demo Prompts (Copy/Paste Ready)

* "What Confluence spaces are available to me?"
* "List recent pages related to project kickoff or scope."
* "Summarize the Project Kickoff and Scope documentation."
* "What decisions have already been made according to Confluence?"
* "What risks or open questions are documented?"
* "What information is missing or unclear?"

---

## 10. What This POC Proves (Narrative)

> Claude can safely and dynamically reason over real internal documentation using existing permissions, without copying data or requiring admin access, through a governed MCP-based architecture.

---

## Getting Started

Follow the CData guide: https://www.cdata.com/developers/ai/dev-guide-claude-agent-sdk-getting-started/

### Prerequisites

* Python 3.8+
* Claude Agent SDK installed
* CData Connect AI configured and authenticated
* Confluence Cloud access (read-only)

### Next Steps

1. Set up Claude Agent SDK environment
2. Configure MCP server connection to CData Connect AI
3. Test MCP tool discovery
4. Implement custom system prompt
5. Test with demo prompts
