# Refactoring smells

Reject these smells during implementation and review.

## Design smells

- A service class has many unrelated public methods.
- A function takes many primitive parameters that belong together.
- A class imports infrastructure and domain concepts at the same time.
- A boolean flag changes a method into two different behaviors.
- A domain rule is repeated in multiple layers.
- A mock verifies implementation details instead of behavior.

## Naming smells

- Names describe technology instead of intent.
- Names are too generic to search meaningfully.
- Names include `data`, `info`, `obj`, `stuff`, `manager`, `helper`, or `util` without strong justification.
- A comment is needed to understand a variable.

## Refactoring moves

- Extract Value Object.
- Introduce Policy.
- Introduce Specification.
- Introduce Port and Adapter.
- Replace conditional with Strategy.
- Move Method to invariant owner.
- Split broad interface.
- Replace primitive obsession with named type.
