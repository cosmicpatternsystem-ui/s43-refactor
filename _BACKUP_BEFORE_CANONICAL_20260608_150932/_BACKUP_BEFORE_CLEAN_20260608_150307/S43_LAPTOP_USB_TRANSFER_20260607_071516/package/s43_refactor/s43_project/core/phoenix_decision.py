class PhoenixDecision:
    state: str
    confidence: float
    composite: float
    rsi: Optional[float]
    shadow_score: Optional[float]
    shadow_label: str
    ready: bool
    reason: str = ""
    def to_dict(self) -> dict:
        return {
            "state": str(self.state),
            "confidence": float(self.confidence or 0.0),
            "composite": float(self.composite or 0.0),
            "rsi": (float(self.rsi) if self.rsi is not None else None),
            "shadow_score": (float(self.shadow_score) if self.shadow_score is not None else None),
            "shadow_label": str(self.shadow_label or ""),
            "ready": bool(self.ready),
            "reason": str(self.reason or ""),
        }
    @classmethod
    def from_dict(cls, data: dict) -> "PhoenixDecision":
        if not isinstance(data, dict):
            data = {}
        return cls(
            state=str(data.get("state") or "FLAT"),
            confidence=float(data.get("confidence") or 0.0),
            composite=float(data.get("composite") or 0.0),
            rsi=(float(data.get("rsi")) if data.get("rsi") is not None else None),
            shadow_score=(float(data.get("shadow_score")) if data.get("shadow_score") is not None else None),
            shadow_label=str(data.get("shadow_label") or ""),
            ready=bool(data.get("ready") or False),
            reason=str(data.get("reason") or ""),
        )