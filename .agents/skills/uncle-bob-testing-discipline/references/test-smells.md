# Test smells

Avoid these smells.

- The test name says `success` but not what behavior succeeded.
- The test verifies a mock call that does not matter to the user or domain.
- The assertion only checks `is not None`.
- The setup is larger than the behavior being tested.
- The test requires comments to understand the scenario.
- The test passes when the main behavior is removed.
- Multiple behaviors are asserted in one test without a strong scenario reason.
- Random data hides the important boundary value.
- Shared fixtures make the test order-dependent.
- A test is skipped instead of fixing the underlying design.

Prefer tests that fail loudly, precisely, and for one meaningful reason.
