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
```

2) Start Postgres + Ollama (llama3):

```bash
docker compose up -d
```

3) Environment variables:
- Copy `.env.example` to `.env` if you need custom credentials.

4) Pull the Ollama model (first time only):

```bash
docker exec -it ai-chat-ollama ollama pull llama3
```
