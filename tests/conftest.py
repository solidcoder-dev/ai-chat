import os
import sys
import time
from pathlib import Path

import docker
import httpx
import pytest
from testcontainers.core.container import DockerContainer

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _docker_available() -> bool:
    try:
        docker.from_env().ping()
    except Exception:
        return False
    return True


@pytest.fixture(scope="session")
def ollama_container():
    return (
        DockerContainer("ollama/ollama:latest")
        .with_command("serve")
        .with_exposed_ports(11434)
        .with_env("OLLAMA_HOST", "0.0.0.0:11434")
    )


@pytest.fixture(scope="session")
def ollama_ready(ollama_container):
    model_name = os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")
    if not _docker_available():
        pytest.skip("Docker not available")

    with ollama_container as ollama:
        port = ollama.get_exposed_port(11434)
        ollama_url = f"http://localhost:{port}"

        with httpx.Client(base_url=ollama_url, timeout=300) as client:
            for _ in range(60):
                try:
                    tags = client.get("/api/tags")
                    tags.raise_for_status()
                    response = client.post("/api/pull", json={"name": model_name})
                    response.raise_for_status()
                    break
                except Exception:
                    time.sleep(1)
            else:
                pytest.skip("Ollama container not reachable on localhost; check Docker port mapping")

        previous = os.environ.get("OLLAMA_HOST")
        os.environ["OLLAMA_HOST"] = ollama_url
        try:
            yield {"url": ollama_url, "model": model_name}
        finally:
            if previous is None:
                os.environ.pop("OLLAMA_HOST", None)
            else:
                os.environ["OLLAMA_HOST"] = previous
