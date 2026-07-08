---
name: project-architecture-guardrails
description: Use before planning, implementing, or reviewing changes in this repository to enforce architectural boundaries, dependency direction, DDD layering, SOLID constraints, no-comments code, and the project definition of done.
---

# Project Architecture Guardrails

Apply this skill whenever a change touches repository structure, dependency direction, cross-layer behavior, use-case orchestration, or final review.

## Goal

Keep the repository evolvable as a strict DDD Python backend for a coding agent that can use MCP, tools, workspaces, file editing, WebSocket streaming, and persistence without corrupting architectural boundaries.

## Required architecture

- `src/domain/` owns business concepts, invariants, entities, value objects, domain services, and domain events.
- `src/application/` owns use cases, application services, orchestration, ports, DTOs, and transaction boundaries.
- `src/infrastructure/` owns adapters for databases, LLMs, MCP, tools, filesystem, Git, subprocesses, and external systems.
- `src/presentation/` owns CLI, FastAPI, WebSocket, and external request/response mapping.
- Tests must exist at the level where the behavior belongs.

## Dependency direction

Allowed direction:

```text
presentation -> application -> domain
infrastructure -> application/domain contracts
```

Forbidden direction:

```text
domain -> application
domain -> infrastructure
domain -> presentation
application -> infrastructure concrete classes
application -> FastAPI, SQLAlchemy, Ollama SDK, MCP SDK, filesystem, subprocess
```

## Review process

1. Identify the behavior being changed.
2. Identify the layer that should own that behavior.
3. Check imports for dependency-direction violations.
4. Check whether the change hides business rules in infrastructure or presentation.
5. Check whether names reflect domain language.
6. Check whether tests protect behavior at the correct level.
7. Check whether production code contains explanatory comments that should be removed through better naming or structure.
8. Check whether the final diff is cohesive and minimal.

## Hard rules

- Do not place business rules in WebSocket handlers, CLI code, SQLAlchemy models, MCP adapters, or LLM clients.
- Do not pass ORM models across application boundaries.
- Do not expose SDK-specific types from infrastructure through application ports.
- Do not create broad abstractions named `Manager`, `Handler`, `Processor`, or `Service` unless their responsibility is precise and unavoidable.
- Do not add comments to justify unclear code.
- Do not merge unrelated refactors into behavior changes.

## Done criteria

Before finishing, verify:

- The domain model is independent from frameworks.
- Application services depend on ports or domain abstractions, not concrete adapters.
- Infrastructure adapters are replaceable.
- Presentation code only translates protocol-specific input/output.
- Tests fail for meaningful regressions.
- The implementation is understandable through names, types, and structure rather than comments.
