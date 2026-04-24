from __future__ import annotations

from pathlib import Path

from agent.tool_api import JsonDict, tool


PROJECT_ROOT = Path.cwd().resolve()
MAX_READ_CHARS = 20_000


def _resolve_project_path(raw_path: str) -> Path:
    candidate = (PROJECT_ROOT / raw_path).resolve()
    try:
        candidate.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError("path must stay within the project directory") from exc
    return candidate


@tool(
    name="read_project_file",
    description="Read a UTF-8 text file from the current project directory.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path to a text file inside the project.",
            }
        },
        "required": ["path"],
        "additionalProperties": False,
    },
)
def read_project_file(arguments: JsonDict) -> JsonDict:
    raw_path = str(arguments.get("path", "")).strip()
    if not raw_path:
        raise ValueError("path is required")

    path = _resolve_project_path(raw_path)
    if not path.exists():
        raise FileNotFoundError(f"file not found: {raw_path}")
    if not path.is_file():
        raise ValueError(f"not a file: {raw_path}")

    content = path.read_text(encoding="utf-8")
    truncated = len(content) > MAX_READ_CHARS
    if truncated:
        content = content[:MAX_READ_CHARS]

    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "content": content,
        "truncated": truncated,
        "chars": len(content),
    }
