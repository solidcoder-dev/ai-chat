Architecture Decisions

- Data ownership: Each Specialist MUST own its domain data (tables and blobs).
- Conversation source of truth: The user-visible conversation MUST live only in Message Store.
- Access boundaries: Other services access Specialist data via APIs or events, never direct DB access.
