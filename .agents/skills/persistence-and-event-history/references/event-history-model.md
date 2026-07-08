# Event history model

## Visible message examples

- User message.
- Final assistant answer.
- Assistant clarification shown to the user.
- User approval or rejection when relevant to the conversation.

## Internal trace examples

- LLM request summary.
- Tool call started.
- Tool call finished.
- Tool call failed.
- File read summary.
- Patch proposed.
- Patch approved.
- Patch applied.
- Command started.
- Command output summary.
- Command failed.

## Principle

If the user should not normally see it in the chat transcript, store it as trace, not as a visible message.
