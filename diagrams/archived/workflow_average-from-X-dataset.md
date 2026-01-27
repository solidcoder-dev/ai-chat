Workflow actualizado para la petición:
**“dame la media de los datos de X”**

---

1. **Cliente → WebSocketEndpoint**
   El mensaje llega al `WebSocketEndpoint`, que delega en:

   * `OrchestratedChatEngine.handle_user_message_with_events(chat_id, text, on_event)`

---

2. **OrchestratedChatEngine: carga y actualiza el Chat**
   `OrchestratedChatEngine` usa:

   * `ChatRepo.loadChat(chatId)` → obtiene `Chat`
   * `Chat.addMessage(role="user", content=...)`
   * `ChatRepo.saveChat(chat)`

---

3. **OrchestratedChatEngine: prepara la llamada al Assistant**

   1. Obtiene todos los metadatos de tools:

      * `ToolCatalog.list_all_tool_specs()` → `all_specs : List<ToolSpec>`

   2. Decide qué tools están permitidas para este assistant/contexto:

      * `ToolAccessPolicy.get_allowed_tools(assistant_id, context, all_specs)`
        → `allowed_specs : List<ToolSpec>`

   3. Construye un `AssistantRequest` con:

      * `messages = chat.get_messages()`
      * `tools = allowed_specs`

   4. Llama al asistente (puede ser `AssistantV1` o `MultiAssistantV1`):

      * `Assistant.infer(request)`

   El `Assistant` decide que necesita el esquema y devuelve una `AssistantResponse` de tipo `tool_call` a `"inspect_schema"` con sus argumentos.

---

4. **OrchestratedChatEngine: ejecuta inspect_schema**

   * `ToolRegistry.get_tool("inspect_schema")` → instancia de `InspectSchemaTool`
   * `Tool.run(args)` sobre esa instancia

   Dentro de `InspectSchemaTool` se usa:

   * `DataCatalog.getTableForDataset(datasetName)`
   * `DataCatalog.getSchema(tableName)`

   La tool devuelve el esquema.

   `OrchestratedChatEngine`:

   * añade el resultado como mensaje de tool al `Chat`
   * `ChatRepo.saveChat(chat)`

---

5. **OrchestratedChatEngine: segunda llamada al Assistant (con esquema)**

   De nuevo:

   1. `ToolCatalog.list_all_tool_specs()` → `all_specs`
   2. `ToolAccessPolicy.get_allowed_tools(assistant_id, context, all_specs)` → `allowed_specs`
   3. Construye un nuevo `AssistantRequest` (mensajes + `allowed_specs`).
   4. Llama a `Assistant.infer(request)`.

   El `Assistant` usa el esquema, construye un SQL y devuelve otra `AssistantResponse` de tipo `tool_call` para `"sql_execute"` con el SQL.

---

6. **OrchestratedChatEngine: ejecuta sql_execute**

   * `ToolRegistry.get_tool("sql_execute")` → instancia de `SqlExecutionTool`
   * `Tool.run(args)` sobre esa instancia

   Dentro de `SqlExecutionTool` se usa:

   * `QueryExecutor.execute(sql)` → `QueryResult` (con la media)

   `OrchestratedChatEngine` añade este resultado como mensaje de tool al `Chat` y guarda:

   * `ChatRepo.saveChat(chat)`

---

7. **OrchestratedChatEngine: tercera llamada al Assistant (con resultado)**

   Igual patrón:

   1. `ToolCatalog.list_all_tool_specs()` → `all_specs`
   2. `ToolAccessPolicy.get_allowed_tools(...)` → `allowed_specs`
   3. `AssistantRequest(messages, allowed_specs)`
   4. `Assistant.infer(request)`

   Ahora el `Assistant` devuelve una `AssistantResponse` de tipo `"message"` con el texto final:
   “La media de los datos de X es 42.3”.

---

8. **OrchestratedChatEngine: guarda y responde**

   * `Chat.addMessage(role="assistant", content=...)`
   * `ChatRepo.saveChat(chat)`
   * Construye un `ChatResponse` con:

     * `chatId`
     * `content`
     * `meta` (por ejemplo, `{ "tool_used": "run_sql_query", "value": 42.3 }`)

   Devuelve este `ChatResponse` al `WebSocketEndpoint`.

---

9. **WebSocketEndpoint → Cliente**

   El `WebSocketEndpoint` envía eventos intermedios (`tool_call`, `tool_result`) y el `ChatResponse` final al cliente por WebSocket.
