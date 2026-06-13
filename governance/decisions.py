import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class GovernanceDecision:
    action_id: str
    outcome: str       # "APPROVED", "REJECTED"
    reason: str
    actor_id: Optional[str] = "SYSTEM"
    source_rule: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    context: Dict[str, Any] = field(default_factory=dict)
