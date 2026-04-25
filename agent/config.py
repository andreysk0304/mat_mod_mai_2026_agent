from __future__ import annotations

import os
from dataclasses import dataclass

from agent.project_paths import PROJECT_ENV_FILE
from dotenv import load_dotenv


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
        "Ты практичный консольный AI-агент для анализа репозиториев и планирования. "
        "Используй github_repo_info, когда пользователь спрашивает о GitHub-репозитории. "
        "Используй plan_optimizer, когда пользователь просит распределить ограниченное время "
        "или бюджет между задачами. Используй инструменты, когда они помогают дать более точный "
        "ответ, и объясняй результат кратко. Форматируй структурированные ответы в Markdown: "
        "используй таблицы для сравнений, списки для планов и жирный текст для ключевых выводов."
    )
    ssl_verify: bool = True
    ca_bundle: str | None = None
    log_enabled: bool = False
    log_stages: set[str] | None = None
    log_file: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(PROJECT_ENV_FILE)
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
