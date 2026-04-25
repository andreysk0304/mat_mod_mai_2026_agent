from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from agent.types import SkillDefinition


@dataclass(slots=True)
class SkillRegistry:
    _skills: dict[str, SkillDefinition] = field(default_factory=dict)
    _enabled: set[str] = field(default_factory=set)

    def register(self, skill: SkillDefinition) -> None:
        self._skills[skill.name] = skill

    def enable(self, name: str) -> bool:
        if name not in self._skills:
            return False
        self._enabled.add(name)
        return True

    def disable(self, name: str) -> bool:
        if name not in self._skills:
            return False
        self._enabled.discard(name)
        return True

    def enabled_prompts(self) -> list[str]:
        return [self._skills[name].prompt for name in sorted(self._enabled)]

    def names(self) -> list[str]:
        return sorted(self._skills)

    def enabled_names(self) -> list[str]:
        return sorted(self._enabled)

    @classmethod
    def with_defaults(cls, skills_dir: Path | None = None) -> "SkillRegistry":
        registry = cls()
        registry.register(
            SkillDefinition(
                name="default-python",
                description="Настраивает ответы на практичные детали реализации на Python.",
                prompt=(
                    "Когда пишешь код на Python, предпочитай небольшие модули, type hints, "
                    "простые dataclass и практичные решения для консольного приложения."
                ),
            )
        )
        registry.enable("default-python")

        if skills_dir and skills_dir.exists():
            for path in sorted(skills_dir.glob("*.md")):
                registry.register(
                    SkillDefinition(
                        name=path.stem,
                        description=f"Loaded from {path.name}",
                        prompt=path.read_text(encoding="utf-8").strip(),
                    )
                )
        return registry
