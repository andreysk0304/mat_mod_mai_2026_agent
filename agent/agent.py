from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from agent.client import OpenAICompatibleClient
from agent.config import Settings
from agent.logger import AgentLogger, DEFAULT_LOG_STAGES
from agent.memory import ConversationMemory
from agent.skills import SkillRegistry
from agent.tools import ToolRegistry
from agent.types import AgentResponse, ChatMessage, JsonDict, TokenUsage


@dataclass(slots=True)
class AgentRuntime:
    settings: Settings
    client: OpenAICompatibleClient
    memory: ConversationMemory
    tools: ToolRegistry
    skills: SkillRegistry
    logger: AgentLogger

    def _system_messages(self) -> list[JsonDict]:
        parts = [self.settings.system_prompt, *self.skills.enabled_prompts()]
        prompt = "\n\n".join(part for part in parts if part.strip())
        return [ChatMessage(role="system", content=prompt).to_api_dict()]

    def _full_conversation(self) -> list[JsonDict]:
        return [*self._system_messages(), *self.memory.to_api_messages()]

    def ask(self, user_text: str) -> AgentResponse:
        self.logger.log("input", f"user: {user_text}")
        self.memory.add(ChatMessage(role="user", content=user_text))
        tool_uses: list[str] = []
        request_usages: list[TokenUsage] = []
        total_usage = TokenUsage()

        for iteration in range(1, self.settings.max_tool_rounds + 2):
            messages = self._full_conversation()
            tools = self.tools.list_for_api()
            self.logger.log(
                "prompt",
                self._format_prompt_payload(
                    iteration=iteration,
                    messages=messages,
                    tools=tools,
                ),
            )
            response = self.client.chat_completions(
                messages=messages,
                tools=tools,
            )
            usage = self._extract_usage(response.get("usage"))
            request_usages.append(usage)
            total_usage.add(usage)
            self.logger.log(
                "usage",
                (
                    f"iteration={iteration} "
                    f"prompt_tokens={usage.prompt_tokens} "
                    f"completion_tokens={usage.completion_tokens} "
                    f"total_tokens={usage.total_tokens}"
                ),
            )
            message = response["choices"][0]["message"]
            tool_calls = message.get("tool_calls") or []

            if tool_calls:
                self.memory.add(
                    ChatMessage(
                        role="assistant",
                        content=message.get("content"),
                        tool_calls=tool_calls,
                    )
                )
                executed_messages: list[ChatMessage] = []
                for tool_call in tool_calls:
                    function = tool_call["function"]
                    tool_name = function["name"]
                    arguments = self._parse_tool_arguments(function.get("arguments", "{}"))
                    self.logger.log("tools", f"call {tool_name} args={json.dumps(arguments, ensure_ascii=True)}")
                    try:
                        result = self.tools.execute(tool_name, arguments)
                    except Exception as exc:
                        result = {"error": str(exc), "tool": tool_name}
                    tool_uses.append(tool_name)
                    self.logger.log(
                        "tools",
                        f"result {tool_name} payload={self.tools.format_result(result)}",
                    )
                    executed_messages.append(
                        ChatMessage(
                            role="tool",
                            name=tool_name,
                            tool_call_id=tool_call["id"],
                            content=self.tools.format_result(result),
                        )
                    )
                self.memory.extend(executed_messages)
                continue

            text = message.get("content") or ""
            self.memory.add(ChatMessage(role="assistant", content=text))
            self.logger.log("output", f"assistant: {text}")
            self.logger.log(
                "usage",
                (
                    "task_total "
                    f"prompt_tokens={total_usage.prompt_tokens} "
                    f"completion_tokens={total_usage.completion_tokens} "
                    f"total_tokens={total_usage.total_tokens}"
                ),
            )
            return AgentResponse(
                text=text,
                tool_uses=tool_uses,
                request_usages=request_usages,
                total_usage=total_usage,
            )

        raise RuntimeError("Tool loop limit reached")

    @staticmethod
    def _parse_tool_arguments(raw_arguments: str) -> JsonDict:
        try:
            parsed = json.loads(raw_arguments)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid tool arguments: {raw_arguments}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("Tool arguments must be a JSON object")
        return parsed

    @staticmethod
    def _extract_usage(raw_usage: object) -> TokenUsage:
        if not isinstance(raw_usage, dict):
            return TokenUsage()
        return TokenUsage(
            prompt_tokens=int(raw_usage.get("prompt_tokens") or 0),
            completion_tokens=int(raw_usage.get("completion_tokens") or 0),
            total_tokens=int(raw_usage.get("total_tokens") or 0),
        )

    def _format_prompt_payload(
        self,
        *,
        iteration: int,
        messages: list[JsonDict],
        tools: list[JsonDict],
    ) -> str:
        payload: JsonDict = {
            "iteration": iteration,
            "model": self.settings.model,
            "temperature": self.settings.temperature,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return json.dumps(payload, ensure_ascii=False, indent=2)

    @classmethod
    def create(
        cls,
        *,
        tools_dir: Path | None = None,
        skills_dir: Path | None = None,
    ) -> "AgentRuntime":
        settings = Settings.from_env()
        return cls(
            settings=settings,
            client=OpenAICompatibleClient(settings),
            memory=ConversationMemory(),
            tools=ToolRegistry.with_defaults(tools_dir=tools_dir),
            skills=SkillRegistry.with_defaults(skills_dir=skills_dir),
            logger=AgentLogger(
                enabled=settings.log_enabled,
                stages=set(settings.log_stages or DEFAULT_LOG_STAGES),
                file_path=settings.log_file,
            ),
        )
