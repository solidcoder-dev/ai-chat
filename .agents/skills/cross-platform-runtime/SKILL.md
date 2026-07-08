---
name: cross-platform-runtime
description: Use when implementing platform-sensitive Python code for paths, subprocesses, environment variables, Docker, local workspace access, filesystem behavior, or command execution on macOS Apple Silicon and Windows.
---

# Cross-Platform Runtime

Use this skill for filesystem, subprocess, Docker, environment variables, local workspace access, command execution, and tests that must work on macOS Apple Silicon and Windows.

## Goal

Keep local development and coding-agent behavior portable across macOS Apple Silicon, Windows, and Linux CI where possible.

## Path rules

- Use `pathlib.Path`.
- Do not concatenate paths with `/` strings.
- Normalize and resolve paths before security checks.
- Preserve relative paths for UI and traces.
- Do not assume case-sensitive filesystems.
- Handle spaces in paths.
- Preserve line endings when editing files.

## Subprocess rules

- Do not use `shell=True`.
- Pass command arguments as lists.
- Do not assume Bash, zsh, grep, sed, awk, rm, or other Unix tools exist.
- Use Python implementations where practical for cross-platform behavior.
- Set timeouts.
- Capture stdout and stderr separately.
- Use explicit text encoding.

## Docker rules

- Docker may be required for Postgres/testcontainers.
- Do not assume the application backend must run inside Docker to access local workspaces.
- For local coding-agent filesystem access, prefer host execution unless the workspace is intentionally mounted.
- Be clear when a command requires Docker Desktop on macOS or Windows.

## Environment rules

- Read environment variables at infrastructure boundaries.
- Do not read environment variables in domain code.
- Do not assume POSIX environment behavior.
- Do not print secrets.

## Tests to add

- Windows-style paths are handled correctly.
- Paths with spaces are handled correctly.
- CRLF and LF files are preserved.
- Subprocess command is called without `shell=True`.
- Missing executable returns structured failure.
- Timeout behavior is deterministic.
- Tests avoid Unix-only commands unless skipped with clear platform reason.

## Done criteria

- Implementation uses portable Python APIs.
- Security checks work with resolved paths on macOS and Windows.
- Tests are deterministic across platforms.
- Platform-specific behavior is isolated and tested.
