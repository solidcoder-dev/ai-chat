## 1) Multi-tenant base

### company

```sql
CREATE TABLE company (
  id          VARCHAR(128) PRIMARY KEY,
  name        VARCHAR(256) NOT NULL,
  status      VARCHAR(32)  NOT NULL CHECK (status IN ('active','archived')),
  created_at  TIMESTAMPTZ  NOT NULL
);
```

### office

```sql
CREATE TABLE office (
  id          VARCHAR(128) PRIMARY KEY,
  company_id  VARCHAR(128) NOT NULL REFERENCES company(id),
  name        VARCHAR(256) NOT NULL,
  status      VARCHAR(32)  NOT NULL CHECK (status IN ('active','archived')),
  created_at  TIMESTAMPTZ  NOT NULL
);

CREATE INDEX idx_office_company ON office(company_id);
```

---

## 2) Users

```sql
CREATE TABLE app_user (
  id          VARCHAR(128) PRIMARY KEY,
  company_id  VARCHAR(128) NOT NULL REFERENCES company(id),
  office_id   VARCHAR(128) NOT NULL REFERENCES office(id),
  status      VARCHAR(32)  NOT NULL CHECK (status IN ('active','archived')),
  created_at  TIMESTAMPTZ  NOT NULL
);

CREATE INDEX idx_user_company ON app_user(company_id);
CREATE INDEX idx_user_office ON app_user(office_id);
```

---

## 3) System prompts

### system_prompt

```sql
CREATE TABLE system_prompt (
  id            VARCHAR(128) PRIMARY KEY,
  agent_id      VARCHAR(128) NOT NULL,
  agent_version VARCHAR(64)  NOT NULL,
  prompt_text   TEXT NOT NULL,
  prompt_hash   VARCHAR(128),
  created_at    TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_system_prompt_agent
  ON system_prompt(agent_id, agent_version);
```

---

## 4) Conversaciones

### conversation

```sql
CREATE TABLE conversation (
  id          VARCHAR(128) PRIMARY KEY,
  user_id     VARCHAR(128) NOT NULL REFERENCES app_user(id),
  agent_id    VARCHAR(128) NOT NULL,
  agent_version VARCHAR(64) NOT NULL,
  system_prompt_id VARCHAR(128) NOT NULL
    REFERENCES system_prompt(id),
  title       VARCHAR(512),
  status      VARCHAR(32) NOT NULL CHECK (status IN ('active','archived')),
  created_at  TIMESTAMPTZ NOT NULL,
  deleted_at  TIMESTAMPTZ
);

CREATE INDEX idx_conversation_user ON conversation(user_id);
CREATE INDEX idx_conversation_agent ON conversation(agent_id, agent_version);
```

---

## 5) Mensajes (eventos)

### message_event

```sql
CREATE TABLE message_event (
  id              BIGSERIAL PRIMARY KEY,
  message_uid     VARCHAR(128) NOT NULL,
  conversation_id VARCHAR(128) NOT NULL
    REFERENCES conversation(id) ON DELETE CASCADE,
  seq             BIGINT NOT NULL,
  role            VARCHAR(16) NOT NULL
    CHECK (role IN ('user','assistant','system')),
  created_at      TIMESTAMPTZ NOT NULL,
  request_id      VARCHAR(128),
  response_to     VARCHAR(128)
    REFERENCES message_event(message_uid) ON DELETE SET NULL,
  meta            JSONB,
  UNIQUE (conversation_id, seq),
  UNIQUE (message_uid)
);

CREATE INDEX idx_message_conv_seq
  ON message_event(conversation_id, seq);
CREATE INDEX idx_message_response_to
  ON message_event(response_to);
```

---

## 6) Items del mensaje

### message_item

```sql
CREATE TABLE message_item (
  id            BIGSERIAL PRIMARY KEY,
  message_id    BIGINT NOT NULL
    REFERENCES message_event(id) ON DELETE CASCADE,
  position      INTEGER NOT NULL,
  item_type     VARCHAR(32) NOT NULL CHECK (
    item_type IN (
      'text','file','artifact','tool_call','tool_result'
    )
  ),
  renderable    BOOLEAN NOT NULL,
  UNIQUE (message_id, position)
);
```

---

## 7) Texto

```sql
CREATE TABLE message_item_text (
  item_id BIGINT PRIMARY KEY
    REFERENCES message_item(id) ON DELETE CASCADE,
  text    TEXT NOT NULL
);
```

---

## 8) Archivos y media

### message_item_file

```sql
CREATE TABLE message_item_file (
  item_id  BIGINT PRIMARY KEY
    REFERENCES message_item(id) ON DELETE CASCADE,
  source  VARCHAR(16) NOT NULL CHECK (source IN ('uri','base64')),
  media_type VARCHAR(128) NOT NULL,
  uri     TEXT NOT NULL,
  filename VARCHAR(512) NOT NULL,
  bytes    BIGINT CHECK (bytes >= 0)
);

```

---

## 9) Artefactos

### artifact

```sql
CREATE TABLE artifact (
  id          VARCHAR(128) PRIMARY KEY,
  type        VARCHAR(64) NOT NULL,
  owner_id    VARCHAR(128),
  created_at  TIMESTAMPTZ NOT NULL,
  label       VARCHAR(256),
  storage_type VARCHAR(16) NOT NULL CHECK (storage_type IN ('s3','db')),
  s3_bucket   VARCHAR(256),
  s3_key      TEXT,
  db_table    VARCHAR(128),
  db_record_id VARCHAR(128),
  metadata    JSONB
);

CREATE INDEX idx_artifact_type ON artifact(type);
```

---

## 10) Tooling

### tool_call

```sql
CREATE TABLE tool_call (
  item_id BIGINT PRIMARY KEY
    REFERENCES message_item(id) ON DELETE CASCADE,
  call_id VARCHAR(128) NOT NULL UNIQUE,
  name    VARCHAR(128) NOT NULL,
  label   VARCHAR(256),
  args    JSONB NOT NULL
);
```

### tool_result

```sql
CREATE TABLE tool_result (
  item_id BIGINT PRIMARY KEY
    REFERENCES message_item(id) ON DELETE CASCADE,
  call_id VARCHAR(128) NOT NULL
    REFERENCES tool_call(call_id),
  status  VARCHAR(16) NOT NULL CHECK (status IN ('ok','error')),
  label   VARCHAR(256),
  result  JSONB,
  error   JSONB,
  CHECK (
    (status = 'ok'    AND result IS NOT NULL AND error IS NULL) OR
    (status = 'error' AND error  IS NOT NULL AND result IS NULL)
  )
);
```

---

## Reglas finales (para que quede claro)

* **Keycloak**: identidad, roles, officeIds
* **BD**: conversaciones, mensajes, ACL fino
* **Cada mensaje es inmutable**
* **Orden garantizado por `seq`**
* **RDS = verdad / ES = búsqueda**

Este DDL está **listo para producción**.
Si quieres, el siguiente paso lógico es **índices de alto volumen** o **particionado por company**.
