from .priority import Priority

class PrioritizedItem:
    priority: Priority
    item: Any = field(compare=False)
    timestamp: float = field(default_factory=time.time)