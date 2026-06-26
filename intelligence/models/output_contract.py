from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class RiskAssessment:
    symbol: str
    price: float
    risk_level: str
    volatility: float
    signal_strength: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MarketAsset:
    symbol: str
    price: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligenceOutput:
    generated_at: str
    source: str
    status: str
    assets: list[MarketAsset] = field(default_factory=list)
    risk_assessment: list[RiskAssessment] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "source": self.source,
            "status": self.status,
            "assets": [asset.to_dict() for asset in self.assets],
            "risk_assessment": [risk.to_dict() for risk in self.risk_assessment],
            "summary": self.summary,
        }

    @staticmethod
    def now_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()
