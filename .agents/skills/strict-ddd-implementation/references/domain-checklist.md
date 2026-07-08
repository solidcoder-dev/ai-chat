# DDD checklist

Use this checklist before committing domain or application changes.

## Concept clarity

- Does the new name come from the product language?
- Is this concept stable enough to model explicitly?
- Is it behavior-rich or just a data bag?
- Is there a better value object hiding behind a primitive?

## Invariant ownership

- Which object prevents invalid state?
- Can invalid state be constructed directly?
- Are there setters that bypass rules?
- Are validation rules duplicated in another layer?

## Boundary control

- Does domain import only Python/domain modules?
- Does application depend only on ports and domain concepts?
- Are infrastructure details hidden behind ports?
- Are presentation DTOs translated before entering use cases?

## Test quality

- Does the test name describe a rule?
- Does at least one test fail if the invariant is removed?
- Are application tests using fakes instead of mocking internal implementation details?
