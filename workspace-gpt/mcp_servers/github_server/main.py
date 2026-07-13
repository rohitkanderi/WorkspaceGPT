"""GitHub MCP server with lightweight repository tools."""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("github")
API_ROOT = "https://api.github.com"


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "WorkspaceGPT",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    with httpx.Client(timeout=20.0, headers=_headers()) as client:
        response = client.get(f"{API_ROOT}{path}", params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool()
def get_repository(owner: str, repo: str) -> dict[str, Any]:
    """Return repository metadata."""
    data = _get(f"/repos/{owner}/{repo}")
    return {
        "full_name": data["full_name"],
        "description": data.get("description"),
        "html_url": data["html_url"],
        "default_branch": data["default_branch"],
        "stars": data["stargazers_count"],
        "open_issues": data["open_issues_count"],
    }


@mcp.tool()
def list_issues(owner: str, repo: str, state: str = "open") -> list[dict[str, Any]]:
    """List repository issues."""
    issues = _get(f"/repos/{owner}/{repo}/issues", {"state": state, "per_page": 20})
    return [
        {
            "number": issue["number"],
            "title": issue["title"],
            "state": issue["state"],
            "html_url": issue["html_url"],
        }
        for issue in issues
        if "pull_request" not in issue
    ]


@mcp.tool()
def search_repositories(query: str) -> list[dict[str, Any]]:
    """Search public repositories."""
    data = _get("/search/repositories", {"q": query, "per_page": 10})
    return [
        {
            "full_name": item["full_name"],
            "description": item.get("description"),
            "html_url": item["html_url"],
            "stars": item["stargazers_count"],
        }
        for item in data.get("items", [])
    ]


if __name__ == "__main__":
    mcp.run()
