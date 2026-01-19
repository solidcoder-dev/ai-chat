from ..application.dtos.tool_spec import ToolSpec


def inspect_schema_tool_spec() -> ToolSpec:
    return ToolSpec(
        name="inspect_schema",
        description="Get table schema by table name or dataset.",
        parameters_schema={
            "type": "object",
            "properties": {
                "table_name": {"type": "string"},
                "dataset": {"type": "string"},
            },
            "anyOf": [{"required": ["table_name"]}, {"required": ["dataset"]}],
            "additionalProperties": False,
        },
    )


def sql_execution_tool_spec() -> ToolSpec:
    return ToolSpec(
        name="sql_execute",
        description="Execute a SQL query and return rows.",
        parameters_schema={
            "type": "object",
            "properties": {
                "sql": {"type": "string"},
            },
            "required": ["sql"],
            "additionalProperties": False,
        },
    )


def default_tool_specs() -> list[ToolSpec]:
    return [inspect_schema_tool_spec(), sql_execution_tool_spec()]
