from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseStrategy(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def execute(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        pass
