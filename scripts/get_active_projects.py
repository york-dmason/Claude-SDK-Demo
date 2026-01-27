"""
Fetch active projects from TSG Capacity Management Tool
"""

import os
import base64
import requests
import json
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "https://yorkb2e.atlassian.net")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")
TCM_PROJECT_KEY = "TCM"

def get_active_projects_from_tcm(
    jira_base_url: str = None,
    jira_email: str = None,
    jira_api_token: str = None,
    project_key: str = TCM_PROJECT_KEY,
    max_results: int = 100,
) -> list[dict]:
    """
    Return active projects and clients from the TCM Jira project.
    Only includes issuetypes "Client" and "Project" (excludes Candidate, operations, etc.).

    Returns list of {"key": "TCM-xxxx", "name": "Project Name"}.
    """
    base = (jira_base_url or JIRA_BASE_URL).rstrip("/")
    email = jira_email or JIRA_EMAIL
    token = jira_api_token or JIRA_API_TOKEN

    if not email or not token:
        raise ValueError("JIRA_EMAIL and JIRA_API_TOKEN must be set (e.g. in .env)")

    url = f"{base}/rest/api/3/search/jql"
    auth_str = base64.b64encode(f"{email}:{token}".encode()).decode()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_str}",
    }
    payload = {
        "jql": f'project = {project_key} AND issuetype in ("Client", "Project")',
        "maxResults": max_results,
        "fields": ["summary"],
    }

    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()

    out = []
    for issue in data.get("issues", []):
        key = issue.get("key")
        summary = (issue.get("fields") or {}).get("summary") or key
        out.append({"key": key, "name": summary})
    return out


def get_active_projects_keys_and_names(projects: list[dict] = None) -> tuple[list[str], list[str]]:
    """
    Optional: return (keys, names) for Confluence/GitHub matching.
    """
    if projects is None:
        projects = get_active_projects_from_tcm()
    keys = [p["key"] for p in projects]
    names = [p["name"] for p in projects]
    return keys, names

def fetch_all_tcm_data_to_file(
    output_path: str = "scripts/output/tcm_full_dump.json",
    jira_base_url: str = None,
    jira_email: str = None,
    jira_api_token: str = None,
    project_key: str = TCM_PROJECT_KEY,
    page_size: int = 100,
) -> list[dict]:
    """
    Fetch ALL issues from TCM (paginated), include issuetype and status,
    and write a flattened view to output_path for inspection.
    Returns the list of flattened issues.
    """
    base = (jira_base_url or JIRA_BASE_URL).rstrip("/")
    email = jira_email or JIRA_EMAIL
    token = jira_api_token or JIRA_API_TOKEN
    if not email or not token:
        raise ValueError("JIRA_EMAIL and JIRA_API_TOKEN must be set")

    url = f"{base}/rest/api/3/search/jql"
    auth_str = base64.b64encode(f"{email}:{token}".encode()).decode()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_str}",
    }
    fields = ["summary", "issuetype", "status"]
    all_issues = []
    next_page_token = None

    while True:
        payload = {
            "jql": f"project = {project_key}",
            "maxResults": page_size,
            "fields": fields,
        }
        if next_page_token is not None:
            payload["nextPageToken"] = next_page_token

        resp = requests.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

        for issue in data.get("issues", []):
            fld = issue.get("fields") or {}
            it = fld.get("issuetype") or {}
            st = fld.get("status") or {}
            all_issues.append({
                "key": issue.get("key"),
                "summary": fld.get("summary"),
                "issuetype": it.get("name"),
                "status": st.get("name"),
            })

        if data.get("isLast", True):
            break
        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(all_issues, f, indent=2)
    return all_issues

if __name__ == "__main__":
    all_issues = fetch_all_tcm_data_to_file()
    print(f"Dumped {len(all_issues)} TCM issues to scripts/output/tcm_full_dump.json")
    projects = get_active_projects_from_tcm()
    print(f"Active projects from TCM ({len(projects)}):")
    for p in projects:
        print(f"  {p['key']}: {p['name']}")
    keys, names = get_active_projects_keys_and_names(projects)
    print(f"\nKeys for filtering: {keys[:5]}..." if len(keys) > 5 else f"\nKeys: {keys}")