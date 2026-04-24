from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

from agent.types import JsonDict, ToolDefinition


class ToolLoadError(RuntimeError):
    pass


@dataclass(slots=True)
class ToolRegistry:
    _tools: dict[str, ToolDefinition] = field(default_factory=dict)

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def list_for_api(self) -> list[JsonDict]:
        return [tool.to_api_dict() for tool in self._tools.values()]

    def names(self) -> list[str]:
        return sorted(self._tools)

    def execute(self, name: str, arguments: JsonDict) -> JsonDict:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name].handler(arguments)

    def load_directory(self, tools_dir: Path | None) -> None:
        if tools_dir is None or not tools_dir.exists():
            return

        for path in sorted(tools_dir.glob("*.py")):
            if path.name.startswith("_"):
                continue
            module = self._load_module_from_path(path)
            self._register_module_tools(module, source=path)

    @classmethod
    def with_defaults(cls, tools_dir: Path | None = None) -> "ToolRegistry":
        registry = cls()
        registry.load_directory(tools_dir)
        return registry

    @staticmethod
    def format_result(result: JsonDict) -> str:
        return json.dumps(result, ensure_ascii=True)

    @staticmethod
    def _load_module_from_path(path: Path) -> ModuleType:
        module_name = f"agent_user_tool_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ToolLoadError(f"Failed to create import spec for {path}")

        module = importlib.util.module_from_spec(spec)
        try:
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
        except Exception as exc:
            sys.modules.pop(module_name, None)
            raise ToolLoadError(f"Failed to load tool module {path.name}: {exc}") from exc
        return module

    def _register_module_tools(self, module: ModuleType, source: Path) -> None:
        before = set(self._tools)
        register = getattr(module, "register", None)
        if callable(register):
            register(self)

        for tool in self._collect_declared_tools(module):
            self.register(tool)

        if set(self._tools) == before:
            raise ToolLoadError(f"No tools declared in {source.name}")

    @staticmethod
    def _collect_declared_tools(module: ModuleType) -> list[ToolDefinition]:
        seen: set[str] = set()
        collected: list[ToolDefinition] = []

        explicit_values: list[object] = []
        if hasattr(module, "TOOL"):
            explicit_values.append(getattr(module, "TOOL"))
        if hasattr(module, "TOOLS"):
            explicit_values.extend(getattr(module, "TOOLS"))

        if explicit_values:
            values = explicit_values
        else:
            values = list(module.__dict__.values())

        for value in values:
            if not isinstance(value, ToolDefinition):
                continue
            if value.name in seen:
                continue
            seen.add(value.name)
            collected.append(value)
        return collected
