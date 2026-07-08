import pytest

from src.application.dtos.tool_spec import ToolSpec
from src.infrastructure.ollama_tool_mapper import OllamaToolMapper


def test_ollama_tool_mapper_maps_internal_names_to_provider_names():
    mapper = OllamaToolMapper(
        [ToolSpec(name="filesystem.read_file", description="Read", parameters_schema={})]
    )

    assert mapper.to_provider_name("filesystem.read_file") == "filesystem__read_file"


def test_ollama_tool_mapper_maps_provider_names_back_to_internal_names():
    mapper = OllamaToolMapper(
        [ToolSpec(name="filesystem.read_file", description="Read", parameters_schema={})]
    )

    assert mapper.to_internal_name("filesystem__read_file") == "filesystem.read_file"


def test_ollama_tool_mapper_preserves_schema():
    schema = {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    }
    mapper = OllamaToolMapper(
        [ToolSpec(name="filesystem.read_file", description="Read", parameters_schema=schema)]
    )

    assert mapper.to_ollama_tools() == [
        {
            "type": "function",
            "function": {
                "name": "filesystem__read_file",
                "description": "Read",
                "parameters": schema,
            },
        }
    ]


def test_ollama_tool_mapper_rejects_unknown_provider_tool_name():
    mapper = OllamaToolMapper([])

    with pytest.raises(ValueError, match="Unknown Ollama tool name"):
        mapper.to_internal_name("filesystem__read_file")
