"""
Active Projects Tools - Custom tools for the agent to verify and list active projects.
These tools use the cached active projects to avoid repeated API calls.
"""

from scripts.active_projects_cache import active_projects_cache


def get_list_active_projects_tool_def() -> dict:
    """
    Return the tool definition for list_active_projects.
    This format is compatible with the Claude Agent SDK.
    """
    return {
        "name": "list_active_projects",
        "description": (
            "List all currently active projects and clients from the TSG Capacity Management Tool. "
            "Use this when the user asks about active projects, wants to see what projects are being tracked, "
            "or needs to know what projects are available."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }


def get_is_project_active_tool_def() -> dict:
    """
    Return the tool definition for is_project_active.
    This format is compatible with the Claude Agent SDK.
    """
    return {
        "name": "is_project_active",
        "description": (
            "Check if a specific project or client is currently active in the TSG Capacity Management Tool. "
            "IMPORTANT: Use this BEFORE querying Confluence, Jira, or GitHub for project-specific information. "
            "Pass the project name or TCM key (e.g., 'Thrivent', 'TCM-27829', '3M', 'Medtronic')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "The project name or TCM key to check"
                }
            },
            "required": ["project_name"]
        }
    }


async def handle_list_active_projects(args: dict) -> dict:
    """
    Handler for the list_active_projects tool.
    Returns the full list of active projects.
    """
    projects = active_projects_cache.list_all()
    
    if not projects:
        return {
            "content": [{
                "type": "text",
                "text": "No active projects loaded. The cache may not have been initialized."
            }]
        }
    
    # Format for readability
    formatted_lines = [f"  - {p['key']}: {p['name']}" for p in projects]
    output = f"Active Projects ({len(projects)} total):\n" + "\n".join(formatted_lines)
    
    return {
        "content": [{
            "type": "text",
            "text": output
        }]
    }


async def handle_is_project_active(args: dict) -> dict:
    """
    Handler for the is_project_active tool.
    Checks if a project name or key is in the active projects list.
    """
    project_name = args.get("project_name", "")
    result = active_projects_cache.is_active(project_name)
    
    return {
        "content": [{
            "type": "text",
            "text": result["message"]
        }]
    }


def get_active_projects_tool_definitions() -> list[dict]:
    """
    Return all active projects tool definitions.
    Use this to register the tools with the agent.
    """
    return [
        get_list_active_projects_tool_def(),
        get_is_project_active_tool_def()
    ]


def get_active_projects_tool_handlers() -> dict:
    """
    Return a mapping of tool names to their async handlers.
    """
    return {
        "list_active_projects": handle_list_active_projects,
        "is_project_active": handle_is_project_active
    }
