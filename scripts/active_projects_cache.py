"""
Active Projects Cache - Caches active projects from TCM at startup.
Provides efficient lookup without repeated API calls.
"""

from typing import Optional


class ActiveProjectsCache:
    """
    Cache active projects at startup to avoid repeated API calls.
    Provides exact and fuzzy matching for project verification.
    """
    
    def __init__(self):
        self._projects: list[dict] = []
        self._names_lower: set[str] = set()
        self._keys: set[str] = set()
        self._loaded: bool = False
    
    def load(self) -> int:
        """
        Fetch active projects from TCM and cache.
        Returns the number of projects loaded.
        """
        from scripts.get_active_projects import get_active_projects_from_tcm
        
        self._projects = get_active_projects_from_tcm()
        self._names_lower = {p["name"].lower() for p in self._projects}
        self._keys = {p["key"].upper() for p in self._projects}
        self._loaded = True
        
        return len(self._projects)
    
    def is_loaded(self) -> bool:
        """Check if the cache has been loaded."""
        return self._loaded
    
    def list_all(self) -> list[dict]:
        """Return all active projects."""
        return self._projects
    
    def count(self) -> int:
        """Return the number of cached projects."""
        return len(self._projects)
    
    def get_sample_names(self, limit: int = 10) -> list[str]:
        """Return a sample of project names for prompt summaries."""
        return [p["name"] for p in self._projects[:limit]]
    
    def is_active(self, query: str) -> dict:
        """
        Check if a project name or key is active.
        
        Args:
            query: Project name or TCM key to check
            
        Returns:
            dict with keys:
                - active: bool - whether any match was found
                - exact_match: bool - whether it was an exact match
                - matches: list[dict] - matching projects
                - message: str - human-readable result
        """
        if not query:
            return {
                "active": False,
                "exact_match": False,
                "matches": [],
                "message": "No project name provided."
            }
        
        query_stripped = query.strip()
        query_lower = query_stripped.lower()
        query_upper = query_stripped.upper()
        
        # Exact key match (e.g., "TCM-27829")
        if query_upper in self._keys:
            match = next(p for p in self._projects if p["key"].upper() == query_upper)
            return {
                "active": True,
                "exact_match": True,
                "matches": [match],
                "message": f"YES - '{query_stripped}' is an active project: {match['key']}: {match['name']}"
            }
        
        # Exact name match (case-insensitive)
        exact_name_matches = [p for p in self._projects if p["name"].lower() == query_lower]
        if exact_name_matches:
            matches_str = ", ".join(f"{m['key']}: {m['name']}" for m in exact_name_matches)
            return {
                "active": True,
                "exact_match": True,
                "matches": exact_name_matches,
                "message": f"YES - '{query_stripped}' is an active project. Matches: {matches_str}"
            }
        
        # Partial/fuzzy match (name contains query or query contains name)
        partial_matches = [
            p for p in self._projects
            if query_lower in p["name"].lower() or p["name"].lower() in query_lower
        ]
        if partial_matches:
            matches_str = ", ".join(f"{m['key']}: {m['name']}" for m in partial_matches)
            return {
                "active": True,
                "exact_match": False,
                "matches": partial_matches,
                "message": f"PARTIAL MATCH - '{query_stripped}' partially matches active projects: {matches_str}. Please clarify which one."
            }
        
        # No match found
        return {
            "active": False,
            "exact_match": False,
            "matches": [],
            "message": f"NO - '{query_stripped}' is NOT in the active projects list. Do not query Confluence/Jira/GitHub for this project."
        }


# Global cache instance - import this in other modules
active_projects_cache = ActiveProjectsCache()
