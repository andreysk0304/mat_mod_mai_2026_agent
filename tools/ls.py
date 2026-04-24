from __future__ import annotations

from agent.project_paths import PROJECT_ROOT, resolve_project_path
from agent.tool_api import JsonDict, tool


MAX_ENTRIES = 200


@tool(
    name="ls",
    description="List files and directories inside the current project directory.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path to a directory inside the project. Defaults to project root.",
            },
            "include_hidden": {
                "type": "boolean",
                "description": "Whether to include entries whose names start with a dot.",
            },
        },
        "additionalProperties": False,
    },
)
def ls(arguments: JsonDict) -> JsonDict:
    raw_path = str(arguments.get("path", ".")).strip() or "."
    include_hidden = bool(arguments.get("include_hidden", False))

    path = resolve_project_path(raw_path)
    if not path.exists():
        raise FileNotFoundError(f"path not found: {raw_path}")
    if not path.is_dir():
        raise ValueError(f"not a directory: {raw_path}")

    entries: list[JsonDict] = []
    truncated = False
    for child in sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
        if not include_hidden and child.name.startswith("."):
            continue
        entries.append(
            {
                "name": child.name,
                "type": "directory" if child.is_dir() else "file",
            }
        )
        if len(entries) >= MAX_ENTRIES:
            truncated = True
            break

    return {
        "path": str(path.relative_to(PROJECT_ROOT)) if path != PROJECT_ROOT else ".",
        "entries": entries,
        "count": len(entries),
        "truncated": truncated,
    }
