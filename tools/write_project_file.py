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
    name="write_project_file",
    description=(
        "Write or append UTF-8 text to a file inside the current project directory. "
        "Use overwrite to replace file contents or append to add text at the end."
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path to a text file inside the project.",
            },
            "content": {
                "type": "string",
                "description": "Text to write using UTF-8 encoding.",
            },
            "mode": {
                "type": "string",
                "enum": ["overwrite", "append"],
                "description": "overwrite replaces file contents, append adds content to the end.",
            },
            "create_dirs": {
                "type": "boolean",
                "description": "Create parent directories if they do not exist.",
            },
        },
        "required": ["path", "content"],
        "additionalProperties": False,
    },
)
def write_project_file(arguments: JsonDict) -> JsonDict:
    raw_path = str(arguments.get("path", "")).strip()
    if not raw_path:
        raise ValueError("path is required")

    content = str(arguments.get("content", ""))
    mode = str(arguments.get("mode", "overwrite")).strip() or "overwrite"
    if mode not in {"overwrite", "append"}:
        raise ValueError("mode must be overwrite or append")

    path = _resolve_project_path(raw_path)
    if bool(arguments.get("create_dirs")):
        path.parent.mkdir(parents=True, exist_ok=True)
    elif not path.parent.exists():
        raise FileNotFoundError(f"directory does not exist: {path.parent.relative_to(PROJECT_ROOT)}")

    previous_content = ""
    if path.exists():
        if not path.is_file():
            raise ValueError(f"not a file: {raw_path}")
        previous_content = path.read_text(encoding="utf-8")

    new_content = previous_content + content if mode == "append" else content
    path.write_text(new_content, encoding="utf-8")

    return {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "mode": mode,
        "chars_written": len(content),
        "final_chars": len(new_content),
    }
