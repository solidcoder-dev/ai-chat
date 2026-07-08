---
name: safe-workspace-file-editing
description: Use when implementing workspace access, file reading, file editing, patch generation, diff review, approval flow, Git checkpoints, command execution, or filesystem safety.
---

# Safe Workspace File Editing

Use this skill for filesystem access, project workspaces, file reading, file editing, patch generation, diff review, approvals, Git checkpoints, and command execution.

## Goal

Allow the coding agent to inspect and modify projects safely. File operations must be bounded, reviewable, auditable, reversible, and cross-platform.

## Workspace boundary rules

- Every file operation must be scoped to a workspace root.
- Resolve paths before use.
- Reject path traversal.
- Reject symlinks that escape the workspace root.
- Never read secrets by default.
- Never edit generated, vendored, dependency, binary, or lock files unless explicitly requested.
- Apply size limits to file reads and tool results.
- Preserve file encoding and line endings.

## Editing rules

- Prefer patch proposals over direct writes.
- Do not apply broad or destructive changes without approval.
- Use unified diffs or structured patch operations.
- Show changed files before applying.
- Create a Git checkpoint or capture a rollback strategy before applying changes.
- Verify the patch still applies cleanly before writing.
- After applying, report exactly which files changed.

## Command execution rules

- Use a safe command runner behind an application port.
- Do not use `shell=True`.
- Pass subprocess arguments as lists.
- Set `cwd` to the workspace root or a validated child path.
- Set timeouts for every command.
- Capture stdout and stderr separately.
- Limit output size.
- Redact secrets before storing or showing output.
- Require approval for destructive, network, dependency-installing, or environment-changing commands.
- Return structured results: command, cwd, exit code, stdout, stderr, duration, timeout flag.

## Git rules

- Check working-tree status before applying patches.
- Do not silently overwrite user changes.
- Create a checkpoint before applying a patch when possible.
- Show final diff after changes.
- Keep Git operations inside the workspace root.

## Forbidden by default

- Reading `.env`, secret files, private keys, credential stores, or token files.
- Editing `.git/`, virtual environments, dependency directories, binary files, generated files, or lock files without explicit request.
- Running destructive shell commands.
- Running commands outside the workspace root.
- Following symlinks outside the workspace.

## Tests to add

- Rejects `../` path traversal.
- Rejects absolute paths outside root.
- Rejects symlink escape.
- Blocks secret files by default.
- Preserves CRLF and LF line endings.
- Proposes a patch without modifying files.
- Applies a patch only after approval.
- Rejects invalid patch operations.
- Creates or records a checkpoint before applying.
- Command runner times out safely.
- Command runner works without Bash-specific assumptions.
- Command output is size-limited and redacted.

## Done criteria

- Unsafe operations fail closed.
- The user can review changes before application.
- File changes are reversible or checkpointed.
- Tests cover filesystem and command edge cases.
- Implementation works on macOS Apple Silicon and Windows.
