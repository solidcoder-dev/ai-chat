---
name: websocket-agent-contracts
description: Use when changing WebSocket APIs, streaming events, tool-call events, diff events, approval events, error contracts, or client-server agent communication.
---

# WebSocket Agent Contracts

Use this skill for WebSocket request/response formats, streaming events, tool-call events, diff events, approval events, command output events, and errors.

## Goal

Keep the WebSocket protocol explicit, versionable, testable, and safe for a coding-agent UI or CLI.

## Contract rules

- Use explicit event types.
- Validate incoming payloads before entering application services.
- Keep transport DTOs in presentation.
- Translate DTOs into application commands.
- Do not expose internal stack traces.
- Do not expose raw unsanitized tool output.
- Separate user-visible assistant text from internal tool/trace events.
- Preserve event ordering where the UI depends on it.
- Version public contracts when breaking changes are introduced.

## Suggested event types

Use names like these when relevant:

```text
assistant_delta
assistant_message_done
tool_call_started
tool_call_finished
tool_call_failed
diff_proposed
approval_required
approval_recorded
patch_applied
command_started
command_output
command_finished
agent_done
agent_error
```

Do not introduce all events automatically. Introduce only what the current behavior needs.

## Request rules

Requests should be explicit about intent:

```json
{
  "type": "user_message",
  "chat_id": "demo",
  "workspace_id": "workspace-demo",
  "text": "Change the repository to support MCP tools"
}
```

Approval requests should identify the operation being approved:

```json
{
  "type": "approve_operation",
  "chat_id": "demo",
  "operation_id": "patch-123"
}
```

## Error rules

- Return structured errors with stable error codes.
- Keep user-facing error messages clear.
- Log internal details separately if logging exists.
- Do not leak exception reprs, database URLs, file contents, secrets, or stack traces to clients.

## Tests to add

- Valid user message is accepted.
- Invalid payload is rejected with a stable error code.
- Event order is deterministic for tool call flows.
- Diff proposal event contains enough information for review.
- Approval event maps to the intended operation.
- Disconnect does not corrupt conversation state.
- Internal errors are sanitized before sending.
- Backwards-compatible fields remain supported when relevant.

## Done criteria

- The public event contract is explicit.
- Payloads are validated.
- Transport code does not contain business rules.
- Tests protect serialization, ordering, and errors.
