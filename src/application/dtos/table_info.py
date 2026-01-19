from dataclasses import dataclass


@dataclass(frozen=True)
class TableInfo:
    dataset_name: str
    table_name: str
