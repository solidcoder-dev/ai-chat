from dataclasses import dataclass


@dataclass(frozen=True)
class SystemPrompt:
    id: str
    agent_id: str
    agent_version: str
    prompt_text: str
    prompt_hash: str | None = None
    created_at: str | None = None
