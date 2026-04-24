from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ENV_FILE = PROJECT_ROOT / ".env"
PROJECT_TOOLS_DIR = PROJECT_ROOT / "tools"
PROJECT_SKILLS_DIR = PROJECT_ROOT / "skills"


def resolve_project_path(raw_path: str) -> Path:
    candidate = (PROJECT_ROOT / raw_path).resolve()
    try:
        candidate.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError("path must stay within the project directory") from exc
    return candidate
