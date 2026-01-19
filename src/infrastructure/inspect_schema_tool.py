from typing import Mapping

from ..application.ports.data_catalog import DataCatalog
from ..application.ports.tool import Tool
from ..domain.structured_data import StructuredMap, StructuredValue


class InspectSchemaTool(Tool):
    def __init__(self, data_catalog: DataCatalog) -> None:
        self._data_catalog = data_catalog

    def run(self, args: StructuredMap) -> StructuredValue:
        table_name = args.get("table_name")
        dataset = args.get("dataset")
        if table_name:
            schema = self._data_catalog.get_schema(str(table_name))
            return {"table_name": str(table_name), "columns": list(schema.columns)}

        if dataset:
            info = self._data_catalog.get_table_for_dataset(str(dataset))
            schema = self._data_catalog.get_schema(info.table_name)
            return {
                "dataset": str(dataset),
                "table_name": info.table_name,
                "columns": list(schema.columns),
            }

        raise ValueError("InspectSchemaTool requires 'table_name' or 'dataset'")
