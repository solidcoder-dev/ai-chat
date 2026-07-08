# Event contract checklist

Before changing WebSocket behavior, verify:

- Is the event type explicit?
- Is the payload schema documented by tests?
- Does the event belong in visible chat, internal trace, or both?
- Is event ordering important?
- What happens on client disconnect?
- What happens on tool timeout?
- What happens when approval is rejected?
- Are errors stable and sanitized?
- Does the CLI still work?
- Does the frontend have enough data to render the state?
