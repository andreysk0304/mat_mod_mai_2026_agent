from __future__ import annotations

from agent.project_paths import PROJECT_ROOT, resolve_project_path
from agent.tool_api import JsonDict, tool


@tool(
    name="mkdir",
    description="Create a new directory inside the current project directory.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path to the directory to create.",
            },
            "parents": {
                "type": "boolean",
                "description": "Create parent directories if they do not exist.",
                "default": False,
            },
        },
        "required": ["path"],
        "additionalProperties": False,
    },
)
def mkdir(arguments: JsonDict) -> JsonDict:
    raw_path = str(arguments["path"]).strip()
    parents = bool(arguments.get("parents", False))

    if not raw_path:
        raise ValueError("path cannot be empty")

    path = resolve_project_path(raw_path)

    if path.exists():
        if path.is_dir():
            return {
                "path": str(path.relative_to(PROJECT_ROOT)),
                "created": False,
                "message": "directory already exists",
            }
        raise FileExistsError(f"file exists at path: {raw_path}")

    try:
        path.mkdir(parents=parents, exist_ok=True)
    except PermissionError as exc:
        raise PermissionError(f"permission denied to create directory: {raw_path}") from exc
    except OSError as exc:
        raise OSError(f"failed to create directory: {raw_path}") from exc

    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "created": True,
        "parents_created": parents,
    }
