from .signal import Signal

class SignalConfidence(enum.Enum):
    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 1.0