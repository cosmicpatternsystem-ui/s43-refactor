from .decisions import GovernanceDecision
from .policies import GovernancePolicy

class RiskGuard:
    _instance = None
    _observer = None
    _policies = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RiskGuard, cls).__new__(cls)
        return cls._instance

    @classmethod
    def set_decision_observer(cls, observer):
        cls._observer = observer

    def add_policy(self, policy: GovernancePolicy):
        """Instance method for adding policies (used by test suite)"""
        if policy not in self._policies:
            self._policies.append(policy)

    def clear_policies(self):
        """Clears all registered policies (used for test isolation)"""
        self._policies.clear()

    def validate_action(self, decision: GovernanceDecision) -> GovernanceDecision:
        for policy in self._policies:
            decision = policy.apply(decision)
        
        if RiskGuard._observer:
            # فراخوانی ایمن آبزرور
            RiskGuard._observer(decision)
            
        return decision

def _notify_decision_observer(decision: GovernanceDecision):
    guard = RiskGuard()
    return guard.validate_action(decision)
