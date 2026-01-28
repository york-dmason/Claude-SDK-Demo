"""Tests for active_projects_cache.py"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.active_projects_cache import ActiveProjectsCache, active_projects_cache


class TestActiveProjectsCache:
    """Test the ActiveProjectsCache class."""
    
    def test_load_projects(self):
        """Test loading projects from TCM."""
        cache = ActiveProjectsCache()
        count = cache.load()
        
        assert count > 0, "Should load at least one project"
        assert cache.is_loaded(), "Cache should be marked as loaded"
        print(f"Loaded {count} projects")
    
    def test_list_all(self):
        """Test listing all projects."""
        cache = ActiveProjectsCache()
        cache.load()
        
        projects = cache.list_all()
        assert len(projects) > 0
        assert "key" in projects[0]
        assert "name" in projects[0]
    
    def test_is_active_exact_match(self):
        """Test exact name match."""
        cache = ActiveProjectsCache()
        cache.load()
        
        # Use a known active project
        result = cache.is_active("3M")
        
        assert result["active"] is True
        assert result["exact_match"] is True
        print(f"Result for '3M': {result['message']}")
    
    def test_is_active_key_match(self):
        """Test matching by TCM key."""
        cache = ActiveProjectsCache()
        cache.load()
        
        # Use a known key
        result = cache.is_active("TCM-27828")
        
        assert result["active"] is True
        assert result["exact_match"] is True
        print(f"Result for 'TCM-27828': {result['message']}")
    
    def test_is_active_partial_match(self):
        """Test partial/fuzzy matching."""
        cache = ActiveProjectsCache()
        cache.load()
        
        # "Thrivent" should match multiple projects
        result = cache.is_active("Thrivent")
        
        assert result["active"] is True
        print(f"Result for 'Thrivent': {result['message']}")
        print(f"Matches: {[m['name'] for m in result['matches']]}")
    
    def test_is_active_not_found(self):
        """Test a project that doesn't exist."""
        cache = ActiveProjectsCache()
        cache.load()
        
        result = cache.is_active("Acme Corp")
        
        assert result["active"] is False
        assert result["matches"] == []
        print(f"Result for 'Acme Corp': {result['message']}")
    
    def test_global_cache_instance(self):
        """Test the global cache instance."""
        # Load the global instance
        active_projects_cache.load()
        
        assert active_projects_cache.is_loaded()
        assert active_projects_cache.count() > 0


if __name__ == "__main__":
    # Run with pytest or directly
    pytest.main([__file__, "-v"])