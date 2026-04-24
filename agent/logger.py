from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import sys


DEFAULT_LOG_STAGES = {"input", "prompt", "output", "usage", "tools", "errors"}


@dataclass(slots=True)
class AgentLogger:
    enabled: bool = False
    stages: set[str] = field(default_factory=lambda: set(DEFAULT_LOG_STAGES))
    file_path: str | None = None

    def log(self, stage: str, message: str) -> None:
        if not self.enabled or stage not in self.stages:
            return
        line = f"[{datetime.now().isoformat(timespec='seconds')}] [{stage}] {message}\n"
        self._write(line)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def enable_stages(self, stages: list[str]) -> list[str]:
        valid: list[str] = []
        for stage in stages:
            if stage in DEFAULT_LOG_STAGES:
                self.stages.add(stage)
                valid.append(stage)
        return valid

    def disable_stages(self, stages: list[str]) -> list[str]:
        valid: list[str] = []
        for stage in stages:
            if stage in DEFAULT_LOG_STAGES:
                self.stages.discard(stage)
                valid.append(stage)
        return valid

    def status_lines(self) -> list[str]:
        destination = self.file_path or "stdout"
        return [
            f"enabled: {self.enabled}",
            f"stages: {', '.join(sorted(self.stages)) or '-'}",
            f"destination: {destination}",
        ]

    def _write(self, line: str) -> None:
        if self.file_path:
            path = Path(self.file_path).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line)
            return
        sys.stdout.write(line)
        sys.stdout.flush()
