## Chats

* **POST** `/chats`
  **Devuelve:** `Conversation`
  → `conversation/1.0.0/conversation.json`

* **GET** `/chats`
  **Devuelve:** `Conversation[]`
  → `conversation/1.0.0/conversation.json`

* **GET** `/chats/{chatId}`
  **Devuelve:** `ConversationAggregate`
  → `conversation-aggregate/1.0.0/conversation-aggregate.json`

* **PATCH** `/chats/{chatId}`
  **Devuelve:** `Conversation`
  → `conversation/1.0.0/conversation.json`

* **DELETE** `/chats/{chatId}`
  **Devuelve:** `Conversation` (status=archived)
  → `conversation/1.0.0/conversation.json`

---

## Mensajes

* **POST** `/chats/{chatId}/messages`
  **Devuelve:** `MessageEvent` (assistant)
  → `message-event/2.3.1/message-event.json`

* **GET** `/chats/{chatId}/messages`
  **Devuelve:** `MessageEvent[]`
  → `message-event/2.3.1/message-event.json`

---

## Búsqueda

* **GET** `/search/messages?q=…`
  **Devuelve:** resultados parciales (read model)
  *(derivado de `ConversationAggregate`, no validado completo)*

---

## Regla final

* **Write** → `Conversation`, `MessageEvent`
* **Read** → `ConversationAggregate`
* **API pública usa `chatId`**, dominio interno usa `conversationId`
