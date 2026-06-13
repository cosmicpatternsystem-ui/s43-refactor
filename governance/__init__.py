from .decisions import GovernanceDecision, validate_decision
from .risk_guard import (
    clear_decision_observer,
    evaluate_risk,
    set_decision_observer,
)

__all__ = [
    "GovernanceDecision",
    "validate_decision",
    "evaluate_risk",
    "set_decision_observer",
    "clear_decision_observer",
]

from governance.audit_observer import governance_audit_logger
from governance.risk_guard import set_decision_observer

set_decision_observer(governance_audit_logger)
