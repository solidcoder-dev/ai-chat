---
name: mcp-coding-agent-architecture
description: Use when implementing MCP client integration, MCP tool discovery, MCP tool execution, agent loops, tool orchestration, workspace roots, resources, prompts, or coding-agent behavior.
---

# MCP Coding Agent Architecture

Use this skill for MCP integration and coding-agent orchestration.

## Goal

Add MCP as an infrastructure capability without leaking MCP SDK details into domain or application logic. Build an agent loop that is bounded, auditable, safe, testable, and extensible.

## Architectural rules

- Treat MCP as infrastructure.
- Do not expose MCP SDK types outside infrastructure adapters.
- Map MCP tools into application-level tool descriptors.
- Map application tool calls into MCP client requests inside the infrastructure adapter.
- Validate all MCP tool input and output at the boundary.
- Treat model output as untrusted.
- Treat MCP output as untrusted.
- Store tool calls and tool results as internal trace events, not normal visible messages.
- Keep agent loops bounded by max iterations, timeouts, and explicit stop conditions.
- Fail closed on unknown tools, invalid arguments, malformed results, timeout, server crash, or denied policy.

## Suggested module layout

```text
src/application/ports/
  mcp_client.py
  tool_registry.py
  agent_trace_repository.py

src/application/services/
  coding_agent.py
  tool_orchestrator.py
  workspace_tool_policy.py

src/infrastructure/mcp/
  stdio_mcp_client.py
  mcp_tool_mapper.py
  mcp_session_manager.py

src/domain/agent/
  tool_call.py
  tool_result.py
  agent_trace_event.py
```

Adjust names to match the actual repository conventions. Do not introduce all modules unless the current task needs them.

## Tool discovery rules

- Discover available tools through the MCP adapter.
- Convert discovered tools to application-level descriptors.
- Keep descriptors immutable for the session unless the MCP server changes.
- Validate tool names and schemas before exposing them to the LLM.
- Hide tools that violate workspace or user permissions.

## Tool execution rules

- A model may request a tool call, but application policy decides whether the call is allowed.
- Read-only tools can be safer but still need workspace and secret checks.
- Write, command, network, dependency, and destructive tools require stricter policy.
- Tool results must be size-limited and sanitized before entering model context.
- Tool failures must be represented as structured results.

## Agent loop rules

- Keep a hard maximum number of tool iterations.
- Keep per-tool and whole-session timeouts.
- Record every tool call in the trace store.
- Do not add raw tool results to visible chat history.
- Summarize large outputs before returning them to the model.
- Do not continue blindly after repeated tool failures.

## Tests to add

- Tool discovery maps MCP schemas to application descriptors.
- Unknown tools are rejected.
- Invalid tool args are rejected before calling MCP.
- MCP timeout returns structured failure.
- MCP server crash returns structured failure.
- Tool calls are stored as trace events.
- Visible history does not include internal trace details.
- Agent loop stops at the configured iteration limit.

## Done criteria

- MCP remains replaceable infrastructure.
- Application logic can be tested without a real MCP server.
- Tool execution policy is explicit.
- Agent traces are auditable.
- Unsafe operations fail closed.
