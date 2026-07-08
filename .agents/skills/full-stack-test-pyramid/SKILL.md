---
name: full-stack-test-pyramid
description: Use when designing, adding, or reviewing tests across domain, application, integration, contract, persistence, WebSocket, MCP, command-runner, and end-to-end levels.
---

# Full-Stack Test Pyramid

Use this skill to choose the correct level of test coverage for a change.

## Goal

Cover behavior at the cheapest level that provides real confidence, while adding integration and contract tests where boundaries are risky.

## Domain tests

Use for:

- Entities.
- Value objects.
- Domain services.
- Policies.
- Specifications.
- Invariants.

Rules:

- No database.
- No filesystem.
- No network.
- No SDKs.
- Fast and deterministic.

Examples:

- A workspace root rejects paths outside its boundary.
- A patch approval cannot be applied twice.
- A conversation preserves message ordering.

## Application tests

Use for:

- Use cases.
- Agent orchestration.
- Tool-call policies.
- Error paths.
- Idempotency.
- Authorization decisions.

Rules:

- Use fakes for ports.
- Do not mock domain behavior.
- Assert use-case outcomes and emitted events.

Examples:

- A coding-agent session reads files before proposing a patch.
- A tool failure is stored in trace history but not shown as a normal assistant message.
- A write operation requires approval.

## Contract tests

Use for:

- WebSocket event schemas.
- MCP tool descriptor mapping.
- DTO serialization.
- API request/response compatibility.
- Error contracts.

Rules:

- Test public payloads exactly.
- Test event ordering when ordering matters.
- Test backwards-compatible behavior when contracts evolve.

## Integration tests

Use for:

- Postgres repositories.
- SQLAlchemy models.
- MCP stdio client adapter.
- Filesystem workspace adapter.
- Git adapter.
- Safe command runner.
- Patch applier.
- Ollama/OpenAI adapter when feasible.

Rules:

- Use real external boundary behavior when practical.
- Use testcontainers for Postgres when required.
- Include failure modes: timeout, crash, invalid output, missing executable, path denial.

## End-to-end smoke tests

Use sparingly for the critical product flow:

1. User sends a chat request.
2. Agent reads project files.
3. Agent proposes a patch.
4. User approves the patch.
5. Patch is applied.
6. Tests or checks run.
7. Final response summarizes changes.

## Coverage expectations for this project

Every meaningful behavior change should normally include:

- Domain or application test for the rule.
- Integration test for risky adapters.
- Contract test for public WebSocket/MCP-facing payloads.
- Regression test for every bug fix.

## Done criteria

- The behavior is protected at the right level.
- Edge cases exist where invalid state or unsafe operations are possible.
- Integration boundaries are not replaced by mocks when the boundary is the risk.
- Tests are deterministic on macOS and Windows.
