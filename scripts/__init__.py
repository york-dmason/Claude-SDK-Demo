"""
Scripts package - Contains active projects fetching, caching, and tools.
"""

from scripts.get_active_projects import (
    get_active_projects_from_tcm,
    get_active_projects_keys_and_names,
)
from scripts.active_projects_cache import (
    ActiveProjectsCache,
    active_projects_cache,
)
from scripts.active_projects_tools import (
    get_active_projects_tool_definitions,
    get_active_projects_tool_handlers,
    handle_list_active_projects,
    handle_is_project_active,
)
from scripts.system_prompts import (
    build_scalable_system_prompt,
    build_simple_system_prompt,
    LEGACY_SYSTEM_PROMPT,
)

__all__ = [
    # Fetching
    "get_active_projects_from_tcm",
    "get_active_projects_keys_and_names",
    # Cache
    "ActiveProjectsCache",
    "active_projects_cache",
    # Tools
    "get_active_projects_tool_definitions",
    "get_active_projects_tool_handlers",
    "handle_list_active_projects",
    "handle_is_project_active",
    # Prompts
    "build_scalable_system_prompt",
    "build_simple_system_prompt",
    "LEGACY_SYSTEM_PROMPT",
]
