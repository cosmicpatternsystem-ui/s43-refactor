from .decisions import GovernanceDecision
from .risk_guard import (
    RiskGuard,
    _notify_decision_observer
)

def set_decision_observer(observer):
    """Public API to set the global observer."""
    RiskGuard.set_decision_observer(observer)

def add_governance_policy(policy):
    """Public API to add a governance policy."""
    RiskGuard.add_policy(policy)

__all__ = [
    "GovernanceDecision",
    "RiskGuard",
    "set_decision_observer",
    "add_governance_policy",
    "_notify_decision_observer"
]
