# MCP boundaries

## Do not leak these outside infrastructure

- MCP SDK client/session objects.
- Raw MCP protocol payloads.
- Transport-specific stdio or HTTP details.
- Server process handles.
- SDK exceptions.

## Application-level concepts

Use application-owned concepts instead:

- `ToolDescriptor`
- `ToolInputSchema`
- `ToolCallRequest`
- `ToolCallResult`
- `ToolExecutionPolicy`
- `McpServerConfig`
- `McpConnectionStatus`

## Failure modes to model

- Tool not found.
- Tool disabled by policy.
- Invalid arguments.
- Server unavailable.
- Timeout.
- Malformed result.
- Result too large.
- Permission denied.

Each failure must be testable without a live MCP server.
