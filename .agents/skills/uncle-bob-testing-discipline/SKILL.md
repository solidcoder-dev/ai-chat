---
name: uncle-bob-testing-discipline
description: Use when adding or changing behavior to follow strict red-green-refactor TDD with expressive, behavior-focused tests inspired by Robert C. Martin's testing discipline.
---

# Uncle Bob Testing Discipline

Use this skill for every behavior change, bug fix, refactor protected by tests, and new use case.

## Goal

Tests must act as precise executable specifications. They must be clean, strict, expressive, and valuable.

## Red-green-refactor workflow

1. Write a failing test that describes the expected behavior.
2. Confirm the test fails for the right reason when practical.
3. Make the smallest production change that passes the test.
4. Refactor production and test code while keeping tests green.
5. Add edge cases before considering the behavior complete.

## Test style rules

- Test behavior, not implementation details.
- One clear reason to fail per test.
- Test names must read like specifications.
- Arrange, Act, and Assert must be obvious without comments.
- Assertions must be strict and meaningful.
- Avoid broad assertions that would pass for broken behavior.
- Avoid asserting internal calls unless the call is the public contract.
- Prefer fakes for application ports when testing use cases.
- Prefer real adapters in integration tests.
- Never weaken tests to match broken production behavior.
- Add regression tests before fixing bugs.

## Naming examples

Good:

```python
def test_rejects_tool_call_when_workspace_is_not_allowed():
def test_preserves_message_order_when_history_is_reloaded():
def test_returns_patch_without_modifying_files_before_approval():
def test_records_tool_failure_without_adding_visible_message():
```

Avoid:

```python
def test_service():
def test_handle_success():
def test_mock_called():
def test_case_1():
```

## Test data rules

- Build only the data needed by the behavior.
- Use named builders or factories when setup becomes repetitive.
- Do not hide important facts in overly generic fixtures.
- Keep edge-case values visible in the test.

## Mocking rules

Use mocks sparingly.

Good uses:

- Application tests where a port represents an external system.
- Verifying an externally observable interaction that is the behavior.
- Simulating rare failure modes.

Bad uses:

- Mocking domain objects.
- Mocking private methods.
- Verifying every internal call.
- Replacing a useful integration test with a brittle mock-only test.

## Done criteria

- The first failing test proves the new behavior was missing.
- Tests are readable as specifications.
- Failure messages would help diagnose the issue.
- Edge cases are covered.
- Refactoring did not make tests less expressive.
