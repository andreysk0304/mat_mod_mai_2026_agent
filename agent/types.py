from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


JsonDict = dict[str, Any]
ToolHandler = Callable[[JsonDict], JsonDict]


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str | None = None
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[JsonDict] | None = None

    def to_api_dict(self) -> JsonDict:
        payload: JsonDict = {"role": self.role}
        if self.content is not None:
            payload["content"] = self.content
        if self.name is not None:
            payload["name"] = self.name
        if self.tool_call_id is not None:
            payload["tool_call_id"] = self.tool_call_id
        if self.tool_calls is not None:
            payload["tool_calls"] = self.tool_calls
        return payload


@dataclass(slots=True)
class ToolDefinition:
    name: str
    description: str
    parameters: JsonDict
    handler: ToolHandler

    def to_api_dict(self) -> JsonDict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass(slots=True)
class SkillDefinition:
    name: str
    description: str
    prompt: str


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: "TokenUsage") -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens


@dataclass(slots=True)
class AgentResponse:
    text: str
    tool_uses: list[str] = field(default_factory=list)
    request_usages: list[TokenUsage] = field(default_factory=list)
    total_usage: TokenUsage = field(default_factory=TokenUsage)
