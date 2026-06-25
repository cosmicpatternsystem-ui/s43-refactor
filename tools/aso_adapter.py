import json
import os

class IntelligenceAdapter:
    def __init__(self, policy_path):
        with open(policy_path, 'r') as f:
            self.policy = json.load(f)
    
    def validate_intent(self, intent):
        # اینجا خریدار می‌تواند مدل AI خود را وصل کند
        # فعلاً به صورت Rule-based عمل می‌کند
        if intent in self.policy["allowed_actions"]:
            return True, "Action allowed by policy"
        return False, "Action prohibited by customer policy"

# تست ساده آداپتور
adapter = IntelligenceAdapter("policies/default_policy.json")
status, msg = adapter.validate_intent("status")
print(f"Policy Check: {status} - {msg}")
