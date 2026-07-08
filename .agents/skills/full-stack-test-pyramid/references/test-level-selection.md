# Test level selection guide

## Add a domain test when

- A business invariant changes.
- A value object validates new input.
- An entity state transition changes.
- A policy or specification decides differently.

## Add an application test when

- A use case coordinates multiple dependencies.
- Tool execution policy changes.
- Approval, idempotency, authorization, or error handling changes.
- User-visible outcome changes.

## Add a contract test when

- JSON schema changes.
- WebSocket event type changes.
- MCP tool descriptors or arguments change.
- CLI request/response behavior changes.

## Add an integration test when

- SQL persistence changes.
- Filesystem behavior changes.
- Git behavior changes.
- Command execution changes.
- MCP transport changes.
- External SDK adapter changes.

## Add an end-to-end test when

- The main product flow changes.
- Multiple layers must work together.
- A regression previously crossed layer boundaries.
