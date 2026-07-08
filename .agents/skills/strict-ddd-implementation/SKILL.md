---
name: strict-ddd-implementation
description: Use when implementing or changing domain entities, value objects, aggregates, domain services, repositories, domain events, bounded contexts, or use cases.
---

# Strict DDD Implementation

Use this skill for domain modeling, use-case design, bounded contexts, repository contracts, application services, domain events, and any change that introduces or modifies business concepts.

## Goal

Model the AI chat and coding-agent domain explicitly. Keep business rules in the domain or application layer. Keep infrastructure details outside the model.

## Domain modeling rules

- Use ubiquitous language from the project.
- Prefer explicit concepts over primitive strings, dictionaries, and booleans.
- Use value objects for validated values and concepts with equality-by-value.
- Use entities when identity and lifecycle matter.
- Use aggregate roots to protect consistency boundaries.
- Put invariants close to the data they protect.
- Use domain services only when behavior does not naturally belong to an entity or value object.
- Use application services to coordinate use cases, transactions, ports, and policies.
- Use repositories for aggregate persistence, not for arbitrary queries that leak database design.
- Use domain events to record meaningful facts, not technical implementation details.

## Anti-patterns to reject

- Anemic domain models with public mutable state and all behavior in services.
- Generic `Manager`, `Processor`, or `Helper` classes.
- Infrastructure SDK objects crossing into domain/application.
- Persistence models used as domain entities.
- Domain behavior implemented in WebSocket handlers, CLI commands, SQL repositories, MCP adapters, or LLM clients.
- Business rules encoded as scattered conditionals across multiple layers.

## Recommended concepts for this project

Consider these concepts when they are relevant to the task:

- `Conversation`
- `Message`
- `VisibleMessage`
- `AgentTrace`
- `ToolCall`
- `ToolResult`
- `Workspace`
- `WorkspaceRoot`
- `PatchProposal`
- `PatchApproval`
- `CommandExecution`
- `McpServerConnection`
- `CodingAgentSession`

Do not introduce all of them automatically. Introduce only the concepts needed by the current behavior.

## Implementation process

1. Name the use case in domain language.
2. Identify the aggregate or value object that owns the invariant.
3. Define the application port only when an external capability is required.
4. Keep implementation details in infrastructure.
5. Add domain/application tests before infrastructure tests.
6. Refactor names until the code reads like the model.

## Repository contracts

Repository contracts must express domain intent:

Good:

```python
class ConversationRepository(Protocol):
    def get_by_id(self, conversation_id: ConversationId) -> Conversation: ...
    def append_message(self, conversation_id: ConversationId, message: Message) -> None: ...
```

Avoid:

```python
class ConversationRepository(Protocol):
    def execute_query(self, sql: str) -> list[dict]: ...
```

## Done criteria

- Each new concept has a clear reason to exist.
- Each invariant has a single owner.
- The domain remains framework-free.
- The application layer orchestrates without owning domain rules.
- Infrastructure implements ports without leaking outward.
- Tests describe behavior, not implementation details.
