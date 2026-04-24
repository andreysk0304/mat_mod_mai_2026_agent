from __future__ import annotations

import argparse
import sys

from agent.agent import AgentRuntime
from agent.client import OpenAICompatibleError
from agent.project_paths import PROJECT_SKILLS_DIR, PROJECT_TOOLS_DIR
from agent.skills import SkillRegistry
from agent.terminal_markdown import render_markdown
from agent.tools import ToolRegistry


HELP_TEXT = """
Команды:
/help                 Показать команды
/exit                 Закрыть агента
/reset                Очистить историю чата
/reload               Перезагрузить tools и skills с диска
/log status           Показать статус логирования
/log on               Включить логирование
/log off              Выключить логирование
/log enable STAGES    Включить стадии логирования (`prompt`, `input`, `output`, ...)
/log disable STAGES   Выключить стадии логирования
/history              Вывести историю чата
/tools                Вывести список tools
/skills               Вывести список skills
/skill enable <NAME>  Включить skill
/skill disable <NAME> Выключить skill
"""


TOOLS_DIR = PROJECT_TOOLS_DIR
SKILLS_DIR = PROJECT_SKILLS_DIR


def build_runtime() -> AgentRuntime:
    return AgentRuntime.create(
        tools_dir=TOOLS_DIR,
        skills_dir=SKILLS_DIR,
    )


def reload_runtime_extensions(runtime: AgentRuntime) -> None:
    enabled_skills = set(runtime.skills.enabled_names())
    runtime.tools = ToolRegistry.with_defaults(tools_dir=TOOLS_DIR)
    runtime.skills = SkillRegistry.with_defaults(SKILLS_DIR)
    for name in enabled_skills:
        runtime.skills.enable(name)


def handle_command(runtime: AgentRuntime, command: str) -> bool:
    if command in {"/exit", "/quit"}:
        return False
    if command == "/help":
        print(HELP_TEXT)
        return True
    if command == "/reset":
        runtime.memory.clear()
        print("history cleared")
        return True
    if command == "/reload":
        reload_runtime_extensions(runtime)
        print("tools and skills reloaded")
        return True
    if command == "/log status":
        for line in runtime.logger.status_lines():
            print(line)
        return True
    if command == "/log on":
        runtime.logger.set_enabled(True)
        print("logging enabled")
        return True
    if command == "/log off":
        runtime.logger.set_enabled(False)
        print("logging disabled")
        return True
    if command.startswith("/log enable "):
        stages = command.removeprefix("/log enable ").split()
        enabled = runtime.logger.enable_stages(stages)
        print(f"enabled stages: {', '.join(enabled) if enabled else '-'}")
        return True
    if command.startswith("/log disable "):
        stages = command.removeprefix("/log disable ").split()
        disabled = runtime.logger.disable_stages(stages)
        print(f"disabled stages: {', '.join(disabled) if disabled else '-'}")
        return True
    if command == "/history":
        for index, message in enumerate(runtime.memory.messages, start=1):
            print(f"{index}. {message.role}: {message.content or '[tool call]'}")
        return True
    if command == "/tools":
        for name in runtime.tools.names():
            print(name)
        return True
    if command == "/skills":
        enabled = set(runtime.skills.enabled_names())
        for name in runtime.skills.names():
            marker = "*" if name in enabled else " "
            print(f"{marker} {name}")
        return True
    if command.startswith("/skill enable "):
        name = command.removeprefix("/skill enable ").strip()
        print("enabled" if runtime.skills.enable(name) else "unknown skill")
        return True
    if command.startswith("/skill disable "):
        name = command.removeprefix("/skill disable ").strip()
        print("disabled" if runtime.skills.disable(name) else "unknown skill")
        return True
    print("unknown command; use /help")
    return True


def run_cli() -> int:
    runtime = build_runtime()
    print("AI-агент для анализа репозиториев и планирования.\n\nИспользуйте /help для просмотра команд.")
    while True:
        try:
            raw = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if not raw:
            continue
        if raw.startswith("/"):
            if not handle_command(runtime, raw):
                return 0
            continue

        try:
            response = runtime.ask(raw)
        except OpenAICompatibleError as exc:
            runtime.logger.log("errors", f"api error: {exc}")
            print(f"api error: {exc}", flush=True)
            continue
        except Exception as exc:
            runtime.logger.log("errors", f"runtime error: {exc}")
            print(f"runtime error: {exc}", flush=True)
            continue

        print(render_markdown(response.text, enable_ansi=sys.stdout.isatty()), flush=True)
        if response.tool_uses:
            print(f"[tools: {', '.join(response.tool_uses)}]", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AI-агент для анализа репозиториев и планирования.")
    parser.parse_args()
    return run_cli()
