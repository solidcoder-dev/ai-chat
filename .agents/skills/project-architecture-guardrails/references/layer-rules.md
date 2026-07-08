# Layer rules

## Domain

Allowed:

- Pure Python entities and value objects.
- Domain exceptions.
- Domain services when behavior does not belong naturally to one entity or value object.
- Domain events that describe meaningful business facts.
- Repository contracts only when the contract is expressed in domain terms.

Forbidden:

- FastAPI.
- SQLAlchemy.
- Pydantic models used as API contracts.
- Ollama, OpenAI, Anthropic, MCP SDKs.
- Filesystem or subprocess calls.
- Environment variables.
- Logging infrastructure.

## Application

Allowed:

- Use cases.
- Application services.
- Ports.
- DTOs.
- Transaction and orchestration decisions.
- Policy coordination.

Forbidden:

- Direct database access.
- Direct filesystem access.
- Direct subprocess calls.
- Direct SDK usage for LLM, MCP, FastAPI, SQLAlchemy, or Docker.

## Infrastructure

Allowed:

- Port implementations.
- SQLAlchemy models and repositories.
- MCP client adapters.
- LLM adapters.
- Filesystem, Git, and command runner adapters.

Forbidden:

- Business decisions that belong in domain/application.
- Public contracts that leak infrastructure types.

## Presentation

Allowed:

- WebSocket handlers.
- CLI commands.
- Request validation at the transport boundary.
- Response serialization.

Forbidden:

- Business orchestration.
- Direct persistence decisions.
- Direct file editing.
- Direct MCP execution.
