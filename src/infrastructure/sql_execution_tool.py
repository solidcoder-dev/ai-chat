from ..application.ports.query_executor import QueryExecutor
from ..application.ports.tool import Tool
from ..domain.structured_data import StructuredMap, StructuredValue


class SqlExecutionTool(Tool):
    def __init__(self, query_executor: QueryExecutor) -> None:
        self._query_executor = query_executor

    def run(self, args: StructuredMap) -> StructuredValue:
        sql = args.get("sql")
        if not sql:
            raise ValueError("SqlExecutionTool requires 'sql'")
        result = self._query_executor.execute(str(sql))
        return {"rows": list(result.rows)}
