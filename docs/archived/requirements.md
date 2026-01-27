# Requirements (RFC 2119/8174)

## Conversation Storage and Traceability
- The system MUST persist every user message in a conversation with a stable `message_id`, `conversation_id`, and timestamp.
- The system MUST persist every assistant message with a stable `message_id`, `conversation_id`, and timestamp.
- The system MUST store a single system prompt per conversation and reference it from the conversation.
- The system MUST store the agent identifier and semantic version used for a conversation.
- The system MUST keep message ordering stable and queryable (e.g., sequence or timestamp ordering).
- The system MUST allow full reconstruction of conversation history in order.
- The system MUST record traceability links between responses and the requests they answer (e.g., `response_to` or `request_id`).
- The system MUST persist tool call and tool result messages as non-renderable events.

## Caching
- The system SHOULD cache recent conversation history in ElastiCache (Redis) keyed by `conversation_id` to provide full context to agents.
- The system SHOULD update/invalidate cache on new messages.

## Observability and Analysis
- The system SHOULD allow a user-facing label for tool call/result steps (e.g., "Running SQL query").
- The system SHOULD support storing prompt metadata (hash, created_at) for analysis.

## Compatibility and UX
- The system SHOULD allow multiple agent types (maitre, bi, brain, etc.) to share the same storage model.
- The system MAY expose tool call/result events to the frontend as "steps."
- The system MAY archive older messages while keeping a readable summary.
- The system MAY provide paged conversation history for long chats.
