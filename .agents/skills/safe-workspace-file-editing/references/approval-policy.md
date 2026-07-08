# Approval policy

## Usually safe without approval

- Listing files inside the workspace.
- Reading non-secret text files inside the workspace within size limits.
- Running read-only Git status or diff commands.
- Running known test commands when configured and non-destructive.

## Requires approval

- Applying patches.
- Writing files.
- Deleting files.
- Moving files.
- Installing dependencies.
- Running commands that modify the workspace.
- Running network commands.
- Editing lock files, generated files, dependency directories, or config files with security impact.

## Must be blocked unless explicitly overridden by the user

- Reading secrets.
- Running destructive commands outside the workspace.
- Following symlinks outside the workspace.
- Modifying `.git/` internals directly.
- Running commands with elevated privileges.
