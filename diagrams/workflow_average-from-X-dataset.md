Workflow actualizado para la petición:
**“dame la media de los datos de X”**

---

1. **Cliente → WebSocketEndpointV1**
   El mensaje llega al `WebSocketEndpointV1`, que delega en:

   * `ChatEngine.handleUserMessage(chatId, text)`
     (implementado por `ChatEngineV1`)

---

2. **ChatEngineV1: carga y actualiza el Chat**
   `ChatEngineV1` usa:

   * `ChatRepo.loadChat(chatId)` → obtiene `Chat`
   * `Chat.addMessage(role="user", content=...)`
   * `ChatRepo.saveChat(chat)`

---

3. **ChatEngineV1: prepara la llamada al Assistant**

   1. Obtiene todos los metadatos de tools:

      * `ToolCatalog.listAllToolSpecs()` → `allSpecs : List<ToolSpec>`

   2. Decide qué tools están permitidas para este assistant/contexto:

      * `ToolAccessPolicy.getAllowedTools(assistantId, context, allSpecs)`
        → `allowedSpecs : List<ToolSpec>`

   3. Construye un `AssistantRequest` con:

      * `messages = chat.getMessages()`
      * `tools = allowedSpecs`

   4. Llama al asistente (puede ser `AssistantV1` o `MultiAssistantV1`):

      * `Assistant.infer(request)`

   El `Assistant` decide que necesita el esquema y devuelve una `AssistantResponse` de tipo `tool_call` a `"inspect_schema"` con sus argumentos.

---

4. **ChatEngineV1: ejecuta inspect_schema**

   * `ToolRegistry.getTool("inspect_schema")` → instancia de `InspectSchemaToolV1`
   * `Tool.run(args)` sobre esa instancia

   Dentro de `InspectSchemaToolV1` se usa:

   * `DataCatalog.getTableForDataset(datasetName)`
   * `DataCatalog.getSchema(tableName)`

   La tool devuelve el esquema.

   `ChatEngineV1`:

   * añade el resultado como mensaje de tool al `Chat`
   * `ChatRepo.saveChat(chat)`

---

5. **ChatEngineV1: segunda llamada al Assistant (con esquema)**

   De nuevo:

   1. `ToolCatalog.listAllToolSpecs()` → `allSpecs`
   2. `ToolAccessPolicy.getAllowedTools(assistantId, context, allSpecs)` → `allowedSpecs`
   3. Construye un nuevo `AssistantRequest` (mensajes + `allowedSpecs`).
   4. Llama a `Assistant.infer(request)`.

   El `Assistant` usa el esquema, construye un SQL y devuelve otra `AssistantResponse` de tipo `tool_call` para `"run_sql_query"` con el SQL.

---

6. **ChatEngineV1: ejecuta run_sql_query**

   * `ToolRegistry.getTool("run_sql_query")` → instancia de `SqlExecutionToolV1`
   * `Tool.run(args)` sobre esa instancia

   Dentro de `SqlExecutionToolV1` se usa:

   * `QueryExecutor.execute(sql)` → `QueryResult` (con la media)

   `ChatEngineV1` añade este resultado como mensaje de tool al `Chat` y guarda:

   * `ChatRepo.saveChat(chat)`

---

7. **ChatEngineV1: tercera llamada al Assistant (con resultado)**

   Igual patrón:

   1. `ToolCatalog.listAllToolSpecs()` → `allSpecs`
   2. `ToolAccessPolicy.getAllowedTools(...)` → `allowedSpecs`
   3. `AssistantRequest(messages, allowedSpecs)`
   4. `Assistant.infer(request)`

   Ahora el `Assistant` devuelve una `AssistantResponse` de tipo `"message"` con el texto final:
   “La media de los datos de X es 42.3”.

---

8. **ChatEngineV1: guarda y responde**

   * `Chat.addMessage(role="assistant", content=...)`
   * `ChatRepo.saveChat(chat)`
   * Construye un `ChatResponse` con:

     * `chatId`
     * `content`
     * `meta` (por ejemplo, `{ "tool_used": "run_sql_query", "value": 42.3 }`)

   Devuelve este `ChatResponse` al `WebSocketEndpointV1`.

---

9. **WebSocketEndpointV1 → Cliente**

   El `WebSocketEndpointV1` envía el contenido del `ChatResponse` al cliente por WebSocket.
