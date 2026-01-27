## Identidad y contexto (siempre primero)

**Keycloak**

* Autentica usuario
* Emite JWT con:

  * `companyId`
  * `officeIds[]`
  * `roles`

**Backend**

* Valida JWT
* Extrae contexto de seguridad
  👉 **No consulta BD todavía**

---

## 1) Crear conversación

**UI → Backend**

* Solicita crear chat

**Backend**

* Usa `companyId` del JWT
* Crea `conversation`
* Inserta ACL inicial en BD:

  * (`conversationId`, `officeId`, `write`)

**BD (RDS)**

* INSERT `conversation`
* INSERT `conversation_office_access`

**Schema**

* `Conversation` (write)

---

## 2) Escribir mensaje (usuario)

**UI → Backend**

* Envía mensaje

**Backend**

* Valida JWT
* Verifica ACL en BD:

  * `officeId ∈ conversation`
* Valida con `MessageEvent`
* Asigna `seq`

**BD**

* INSERT `message_event` (+ items)

**Schema**

* `MessageEvent` (user)

---

## 3) Generar respuesta (assistant)

**Backend**

* Relee historial necesario
* Ejecuta IA / tools
* Crea **nuevo** `MessageEvent` (`assistant`)

**BD**

* INSERT `message_event` (+ tool items)

**Schema**

* `MessageEvent` (assistant)

---

## 4) Responder al UI

**Backend → UI**

* Devuelve `MessageEvent` del assistant

**UI**

* Renderiza por `seq`

---

## 5) Leer historial

**UI**

* `GET /conversations/{id}`

**Backend**

* Valida JWT
* Verifica ACL en BD (office ↔ conversation)
* Agrega datos

**Respuesta**

* `ConversationAggregate`

---

## 6) Búsqueda

**Backend**

* Indexa mensajes al escribir
* Incluye `companyId` + `officeIds`

**Elasticsearch**

* Filtra por `officeIds`

---

## Regla final

* **Keycloak** → identidad y pertenencia
* **BD** → permisos finos por conversación
* **RDS** → verdad
* **ES** → búsqueda
* **Cada mensaje = evento inmutable**

Este flujo es estable, escalable y el que se usa en producción real.
