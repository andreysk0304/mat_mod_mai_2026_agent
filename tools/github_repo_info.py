from __future__ import annotations

import datetime as dt
import json
import os
import re
import ssl
from urllib import error, parse, request

from agent.tool_api import JsonDict, tool

try:
    import certifi
except ImportError:
    certifi = None


GITHUB_API_BASE = "https://api.github.com"
REPO_RE = re.compile(
    r"^(?:https?://github\.com/)?(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


def _parse_repo(raw_repo: str) -> tuple[str, str]:
    match = REPO_RE.match(raw_repo.strip())
    if not match:
        raise ValueError("repo must look like 'owner/name' or 'https://github.com/owner/name'")
    return match.group("owner"), match.group("repo")


def _github_get(path: str) -> JsonDict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-planning-agent",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{GITHUB_API_BASE}{path}"
    http_request = request.Request(url, headers=headers, method="GET")
    ssl_context = _build_ssl_context()
    try:
        with request.urlopen(http_request, timeout=30, context=ssl_context) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}: {details}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Failed to reach GitHub API: {exc.reason}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("GitHub API returned an unexpected payload")
    return payload


def _build_ssl_context() -> ssl.SSLContext:
    ca_bundle = os.getenv("GITHUB_CA_BUNDLE", "").strip()
    if ca_bundle:
        return ssl.create_default_context(cafile=ca_bundle)
    if certifi is not None:
        return ssl.create_default_context(cafile=certifi.where())
    return ssl.create_default_context()


@tool(
    name="github_repo_info",
    description=(
        "Fetch public GitHub repository metadata through the GitHub API. "
        "Use it before answering questions about repository activity, popularity, language mix, "
        "open issues, or planning work for a repo."
    ),
    parameters={
        "type": "object",
        "properties": {
            "repo": {
                "type": "string",
                "description": "Repository as owner/name or a GitHub URL.",
            }
        },
        "required": ["repo"],
        "additionalProperties": False,
    },
)
def github_repo_info(arguments: JsonDict) -> JsonDict:
    raw_repo = str(arguments.get("repo", "")).strip()
    if not raw_repo:
        raise ValueError("repo is required")

    owner, repo = _parse_repo(raw_repo)
    encoded_owner = parse.quote(owner, safe="")
    encoded_repo = parse.quote(repo, safe="")

    repo_payload = _github_get(f"/repos/{encoded_owner}/{encoded_repo}")
    languages_payload = _github_get(f"/repos/{encoded_owner}/{encoded_repo}/languages")

    pushed_at = repo_payload.get("pushed_at")
    updated_at = repo_payload.get("updated_at")
    collected_at = dt.datetime.now(dt.timezone.utc).isoformat()

    return {
        "source": f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
        "collected_at": collected_at,
        "full_name": repo_payload.get("full_name"),
        "description": repo_payload.get("description"),
        "url": repo_payload.get("html_url"),
        "default_branch": repo_payload.get("default_branch"),
        "stars": repo_payload.get("stargazers_count"),
        "forks": repo_payload.get("forks_count"),
        "open_issues": repo_payload.get("open_issues_count"),
        "watchers": repo_payload.get("subscribers_count"),
        "license": (repo_payload.get("license") or {}).get("spdx_id"),
        "archived": repo_payload.get("archived"),
        "created_at": repo_payload.get("created_at"),
        "updated_at": updated_at,
        "pushed_at": pushed_at,
        "languages_bytes": languages_payload,
    }
