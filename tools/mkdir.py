from __future__ import annotations

from pathlib import Path

from agent.tool_api import JsonDict, tool


PROJECT_ROOT = Path.cwd().resolve()


def _resolve_project_path(raw_path: str) -> Path:
    candidate = (PROJECT_ROOT / raw_path).resolve()
    try:
        candidate.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError("path must stay within the project directory") from exc
    return candidate


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

    path = _resolve_project_path(raw_path)

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
