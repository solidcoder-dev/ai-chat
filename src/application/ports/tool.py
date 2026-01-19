from abc import ABC, abstractmethod

from ...domain.structured_data import StructuredMap, StructuredValue

class Tool(ABC):
    @abstractmethod
    def run(self, args: StructuredMap) -> StructuredValue:
        raise NotImplementedError
