---
name: solid-clean-code-refactoring
description: Use when writing or refactoring production Python code to enforce strict SOLID, self-explanatory naming, cohesive modules, dependency inversion, and no explanatory comments.
---

# SOLID Clean Code Refactoring

Use this skill whenever production code is created or refactored.

## Goal

Keep the codebase strict, readable, extensible, and self-explanatory without relying on comments.

## SOLID rules

### Single Responsibility

- Each module, class, and function must have one reason to change.
- Split orchestration, policy, persistence, transport, and formatting responsibilities.
- Do not create objects that both decide and perform external side effects.

### Open/Closed

- Add new behavior by adding focused implementations behind ports or strategies when variation is expected.
- Avoid growing conditionals that must be edited for every new provider, tool type, protocol, or persistence backend.

### Liskov Substitution

- Ports must define contracts that all adapters can satisfy honestly.
- Do not add optional behavior that only one implementation supports unless the abstraction expresses it.

### Interface Segregation

- Prefer narrow ports.
- Do not force a caller to depend on methods it does not use.
- Split read/write/admin capabilities when permissions or responsibilities differ.

### Dependency Inversion

- Application code depends on abstractions.
- Infrastructure code implements abstractions.
- Domain code depends on no framework or external system.

## No-comments code rule

Production code must be understandable through names, types, and structure.

Do not add comments to explain what code does. Instead:

- Rename variables, methods, classes, and modules.
- Extract a concept when the extracted name improves understanding.
- Replace boolean flags with explicit methods, policies, or value objects when needed.
- Replace unclear conditionals with named predicates.
- Keep cohesive functions together when splitting would make flow harder to read.

Allowed comments are rare and must explain external constraints, not local code mechanics:

- Protocol compatibility requirements.
- Security-sensitive warnings that cannot be expressed in code.
- Generated-code markers.
- Vendor quirks that are verified by tests.

## Naming rules

Good names are precise and domain-oriented:

```python
workspace_allows_path
proposed_patch_requires_approval
append_visible_message
record_tool_trace_event
```

Avoid vague names:

```python
handle
process
manager
helper
data
result2
flag
```

## Refactoring process

1. Identify the responsibility being changed.
2. Move decisions to the object that owns them.
3. Introduce a port only at a real external boundary.
4. Make names explicit before extracting more code.
5. Remove explanatory comments by improving design.
6. Keep tests green after each small refactor.

## Done criteria

- Responsibilities are cohesive.
- Abstractions are narrow and useful.
- Dependencies point inward.
- Code names explain intent.
- Production code has no explanatory comments.
- Tests still describe behavior clearly.
