from abc import ABC, abstractmethod


class MappingLoader(ABC):

    @abstractmethod
    def load(self, source_name: str) -> dict[str, str]:
        ...