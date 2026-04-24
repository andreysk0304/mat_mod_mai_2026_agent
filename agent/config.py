from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path: str | os.PathLike[str] = ".env") -> None:
        env_path = Path(path)
        if not env_path.exists():
            return
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value


def _parse_bool(raw_value: str | None, default: bool) -> bool:
    if raw_value is None:
        return default
    value = raw_value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    return default


def _parse_csv(raw_value: str | None) -> set[str]:
    if not raw_value:
        return set()
    return {chunk.strip() for chunk in raw_value.split(",") if chunk.strip()}


@dataclass(slots=True)
class Settings:
    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    temperature: float = 0.2
    max_tool_rounds: int = 4
    system_prompt: str = (
        "You are a practical CLI AI agent for repository analysis and planning. "
        "Use github_repo_info when the user asks about a GitHub repository. "
        "Use plan_optimizer when the user asks to allocate limited time or budget across tasks. "
        "Use tools when they help produce a more accurate answer, and explain the result concisely. "
        "Format structured answers in Markdown: use tables for comparisons, bullet lists for plans, "
        "and bold text for key conclusions."
    )
    ssl_verify: bool = True
    ca_bundle: str | None = None
    log_enabled: bool = False
    log_stages: set[str] | None = None
    log_file: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        defaults = cls()
        return cls(
            model=os.getenv("AI_AGENT_MODEL", defaults.model),
            api_key=os.getenv("AI_AGENT_API_KEY", ""),
            base_url=os.getenv("AI_AGENT_BASE_URL", defaults.base_url).rstrip("/"),
            temperature=float(os.getenv("AI_AGENT_TEMPERATURE", defaults.temperature)),
            max_tool_rounds=int(
                os.getenv("AI_AGENT_MAX_TOOL_ROUNDS", defaults.max_tool_rounds)
            ),
            system_prompt=os.getenv("AI_AGENT_SYSTEM_PROMPT", defaults.system_prompt),
            ssl_verify=_parse_bool(
                os.getenv("AI_AGENT_SSL_VERIFY"),
                defaults.ssl_verify,
            ),
            ca_bundle=os.getenv("AI_AGENT_CA_BUNDLE"),
            log_enabled=_parse_bool(
                os.getenv("AI_AGENT_LOG_ENABLED"),
                defaults.log_enabled,
            ),
            log_stages=_parse_csv(os.getenv("AI_AGENT_LOG_STAGES")) or None,
            log_file=os.getenv("AI_AGENT_LOG_FILE"),
        )
