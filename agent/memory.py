from __future__ import annotations

from dataclasses import dataclass, field

from agent.types import ChatMessage


@dataclass(slots=True)
class ConversationMemory:
    messages: list[ChatMessage] = field(default_factory=list)

    def add(self, message: ChatMessage) -> None:
        self.messages.append(message)

    def extend(self, messages: list[ChatMessage]) -> None:
        self.messages.extend(messages)

    def clear(self) -> None:
        self.messages.clear()

    def to_api_messages(self) -> list[dict[str, object]]:
        return [message.to_api_dict() for message in self.messages]