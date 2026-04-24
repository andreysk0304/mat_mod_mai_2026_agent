from __future__ import annotations

import unittest

from agent.agent import AgentRuntime
from agent.config import Settings
from agent.logger import AgentLogger
from agent.memory import ConversationMemory
from agent.skills import SkillRegistry
from agent.tools import ToolRegistry
from agent.types import JsonDict
from agent.tool_api import tool


@tool(
    name="echo",
    description="Return text back.",
    parameters={
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
        "additionalProperties": False,
    },
)
def echo(arguments: JsonDict) -> JsonDict:
    return {"text": arguments["text"]}


class LoopingToolClient:
    def __init__(self) -> None:
        self.tool_counts: list[int] = []

    def chat_completions(self, messages: list[JsonDict], tools: list[JsonDict]) -> JsonDict:
        self.tool_counts.append(len(tools))
        if tools:
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": f"call_{len(self.tool_counts)}",
                                    "type": "function",
                                    "function": {
                                        "name": "echo",
                                        "arguments": "{\"text\":\"hello\"}",
                                    },
                                }
                            ],
                        }
                    }
                ],
                "usage": {},
            }
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "final answer from existing tool results",
                    }
                }
            ],
            "usage": {},
        }


class AgentRuntimeTests(unittest.TestCase):
    def test_forces_final_answer_after_tool_round_limit(self) -> None:
        registry = ToolRegistry()
        registry.register(echo)
        client = LoopingToolClient()
        runtime = AgentRuntime(
            settings=Settings(api_key="test", max_tool_rounds=1),
            client=client,  # type: ignore[arg-type]
            memory=ConversationMemory(),
            tools=registry,
            skills=SkillRegistry(),
            logger=AgentLogger(enabled=False),
        )

        response = runtime.ask("say hello")

        self.assertEqual(response.text, "final answer from existing tool results")
        self.assertEqual(response.tool_uses, ["echo"])
        self.assertEqual(client.tool_counts, [1, 0])


if __name__ == "__main__":
    unittest.main()
