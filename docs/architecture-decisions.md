Architecture Decisions

- Microservices architecture: aligns with scalability, fault-tolerance, and independent deployments.
- Domain-first boundaries: Chat Registry, Message Store, Specialist Responders, Realtime Gateway, Identity & Access Control.
- Message Store as source of truth: user-visible conversation is immutable, ordered, and stored only in Message Store.
- Specialist data ownership: each Specialist owns its domain data (tables and blobs).
- No cross-service DB access: data sharing via APIs or events only.
- Append-only + idempotent writes: stable ordering and safe retries.
- Conversation Cache placement: read-through cache behind History/Message Store for hot chats.
- History Query read model: optimized full-history reads and future search readiness.
- Event Bus + Outbox: decoupling and reliable delivery for projections and fan-out.
- Realtime protocol: SSE to the client (browser-friendly streaming).
- Service-to-service protocols: HTTP/gRPC for contracts, backpressure, and tooling.
- Auth: centralized IAM with external Keycloak validation.
- AWS choices: API Gateway, EventBridge, ElastiCache, S3, CloudWatch/X-Ray, Cloud Map/SSM, KMS.
- Security: TLS in transit, KMS at rest.
- Retention & archive: applied to Message Store and Specialist data.
- Load assumption: ~300 messages per chat; supports simple MVP with clear scaling path.

Message Store vs History Read Model
- message_store_db is the append-only source of truth for user-visible conversation data.
- history_read_db is a read-optimized projection that can differ in schema to serve fast history queries.

Best Practices (non-redundant)
- Validate access via Chat Registry before any history read.
- Use request_id for idempotent writes at Message Store.
- Store only user-visible content in Message Store (no internal prompts/tools).
- Paginate history reads to enforce size limits and performance.
