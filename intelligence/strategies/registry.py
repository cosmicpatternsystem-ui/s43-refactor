from typing import Dict, Type
from .base import BaseStrategy

class StrategyRegistry:
    _strategies: Dict[str, Type[BaseStrategy]] = {}

    @classmethod
    def register(cls, strategy_class: Type[BaseStrategy]):
        name = strategy_class().name()
        cls._strategies[name] = strategy_class
        return strategy_class

    @classmethod
    def get_strategy(cls, name: str) -> BaseStrategy:
        if name not in cls._strategies:
            raise ValueError(f"Strategy '{name}' not found in registry.")
        return cls._strategies[name]()

    @classmethod
    def list_strategies(cls):
        return list(cls._strategies.keys())
