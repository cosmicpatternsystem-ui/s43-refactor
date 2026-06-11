class TradeHealth:
    __slots__ = ("mode", "size_mult", "severity", "reasons")
    def __init__(self, mode: str, size_mult: float, severity: float, reasons: dict):
        self.mode = str(mode)
        self.size_mult = float(size_mult)
        self.severity = float(severity)
        self.reasons = dict(reasons or {})