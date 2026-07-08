# Platform checklist

## macOS Apple Silicon

- Avoid assuming x86-only Docker images.
- Avoid Linux-only filesystem behavior.
- Expect zsh as default shell, but do not depend on it.

## Windows

- Use `Path` instead of string separators.
- Avoid Bash-only commands.
- Test CRLF handling.
- Handle drive letters.
- Handle case-insensitive paths.
- Use PowerShell-friendly docs when giving commands.

## Linux CI

- Keep tests deterministic without relying on local developer tools.
- Skip platform-specific tests explicitly and narrowly.
