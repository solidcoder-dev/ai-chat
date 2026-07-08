from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence


@dataclass(frozen=True)
class McpServerConfig:
    name: str
    command: str
    args: Sequence[str] = field(default_factory=list)
    env: Mapping[str, str] | None = None

    @classmethod
    def filesystem(cls, name: str, workspace_root: str | Path) -> "McpServerConfig":
        root_path = Path(workspace_root).expanduser().resolve()
        return cls(
            name=name,
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", str(root_path)],
        )

    def command_line(self) -> list[str]:
        return [self.command, *self.args]
