---
name: persistence-and-event-history
description: Use when changing chat persistence, message history, repository implementations, migrations, event traces, idempotency, archival, deletion, or database-backed state.
---

# Persistence and Event History

Use this skill when modifying repositories, database models, migrations, message history, conversation state, agent traces, idempotency, archival, or deletion behavior.

## Goal

Keep persisted state correct, auditable, append-friendly, and independent from infrastructure details.

## Persistence rules

- Keep ORM models inside infrastructure.
- Do not expose SQLAlchemy models through domain or application boundaries.
- Repository contracts must use domain/application concepts.
- Writes must be idempotent when the same request can be retried.
- Persist stable ordering for messages and trace events.
- Prefer append-only history for conversations and traces.
- Model archive/delete states explicitly when needed instead of physically deleting by accident.
- Separate user-visible chat history from internal agent trace history.
- Do not persist raw secrets in messages, traces, logs, or command output.

## Conversation history rules

- Visible history stores what the user and assistant should see.
- Internal trace history stores tool calls, tool results, command output summaries, patch proposals, approvals, and execution metadata.
- Raw large outputs should be summarized, truncated, or stored externally with explicit policy.
- Message order must be deterministic after reload.

## Agent trace rules

Trace events should be structured and sanitized.

Useful fields:

- `trace_id`
- `conversation_id`
- `workspace_id`
- `event_type`
- `started_at`
- `finished_at`
- `status`
- `tool_name`
- `sanitized_input_summary`
- `sanitized_output_summary`
- `error_code`
- `correlation_id`

Do not store raw secret values or unnecessary file contents.

## Migration rules

- Add migration tests for schema changes when migration tooling exists.
- Keep migrations forward-compatible where practical.
- Avoid destructive schema changes without a data migration plan.
- Add repository contract tests for new persistence behavior.

## Tests to add

- Appending messages preserves order.
- Retrying a write with the same idempotency key does not duplicate state.
- Visible messages and trace events are stored separately.
- Repository returns domain/application objects, not ORM models.
- Archive/delete state behaves as the domain requires.
- Secret-looking values are redacted from trace persistence.
- Persistence failures return domain/application errors without leaking SQL internals.

## Done criteria

- Persistence contracts stay clean.
- History is stable and auditable.
- Trace and visible history are separated.
- Idempotency is explicit where retries are possible.
- Sensitive data is not accidentally stored.
