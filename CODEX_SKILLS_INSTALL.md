# Installing the Codex skills pack

This archive is designed to be extracted into the root of `solidcoder-dev/ai-chat`.

## Recommended installation

From the repository root:

```bash
unzip ai-chat-codex-skills.zip -d .
```

If the repository already has an `AGENTS.md`, merge it manually instead of overwriting it.

```bash
cp AGENTS.md AGENTS.md.backup
unzip ai-chat-codex-skills.zip -d .
```

## Expected result

```text
AGENTS.md
CODEX_SKILLS_INSTALL.md
.agents/
  skills/
    project-architecture-guardrails/
    strict-ddd-implementation/
    solid-clean-code-refactoring/
    uncle-bob-testing-discipline/
    full-stack-test-pyramid/
    mcp-coding-agent-architecture/
    safe-workspace-file-editing/
    persistence-and-event-history/
    websocket-agent-contracts/
    cross-platform-runtime/
```

## Validation

After extraction:

```bash
find .agents/skills -name SKILL.md -maxdepth 3
pytest
```

On Windows PowerShell:

```powershell
Get-ChildItem .agents\skills -Recurse -Filter SKILL.md
pytest
```

## Notes

- `AGENTS.md` contains always-on repository guidance.
- Each skill folder contains a mandatory `SKILL.md` file.
- `references/` files provide deeper checklists and examples that the skill can load when needed.
- The skills are intentionally written in English so Codex can apply them consistently in code-generation workflows.
