# AI Chat

Python interfaces and domain models for the chat system described in
`diagrams/class-diagram.plantuml`.

## Structure
- `src/domain/` entities, value objects, repository interfaces
- `src/application/` services, ports, DTOs
- `diagrams/` UML source

## Setup (Docker + venv)
1) Create and activate a virtualenv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

2) Start Postgres + Ollama:

```bash
docker compose up -d
```

3) Environment variables:
- Copy `.env.example` to `.env` if you need custom credentials.

4) Pull the Ollama model used by coding mode (first time only):

```bash
docker exec -it ai-chat-ollama ollama pull llama3.1:8b
```

## Tests (Docker + testcontainers)
Run tests with Docker running locally:

```bash
pytest
```

## Run (CLI)
Start the chat CLI:

```bash
python main.py
```

Start the coding CLI with a workspace and a tool-capable model:

```bash
python3 main.py --mode coding --workspace . --model llama3.1:8b
```

If `--model` is omitted, coding mode uses `OLLAMA_MODEL`, then falls back to `llama3.1:8b`.

## Run (WebSocket API)
Start the FastAPI server:

```bash
uvicorn src.presentation.websocket_endpoint:app --host 0.0.0.0 --port 8000
```

WebSocket endpoint:
- `ws://localhost:8000/ws`

Message format:
```json
{"chat_id": "demo", "text": "Hello"}
```


## Run (Docker)
Build and run the WebSocket API container:

```bash
docker build -t ai-chat-ws .
docker run --rm -p 8000:8000 ai-chat-ws
```

## Run (Docker Compose)
Bring up the full stack (Postgres + Ollama + API):

```bash
docker compose up -d
```

WebSocket endpoint:
- `ws://localhost:8000/ws`

## CLI (WebSocket client)
Connect to the WebSocket API:

```bash
python cli.py ws://localhost:8000/ws
```
