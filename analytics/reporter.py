import json
import os
from collections import Counter

class GovernanceAnalytics:
    def __init__(self, log_file="governance_audit.log"):
        self.log_file = log_file

    def generate_report(self):
        if not os.path.exists(self.log_file):
            return "No audit logs found. Run the system first."

        stats = {
            "total_actions": 0,
            "outcomes": Counter(),
            "top_reasons": Counter(),
            "total_risk_denied": 0
        }

        with open(self.log_file, "r") as f:
            for line in f:
                try:
                    # فرض بر این است که لاگ‌ها با فرمت JSON یا حاوی کلیدواژه هستند
                    # اگر فرمت شما متنی ساده است، اینجا پارس می‌شود
                    stats["total_actions"] += 1
                    if "REJECTED" in line:
                        stats["outcomes"]["REJECTED"] += 1
                    elif "APPROVED" in line:
                        stats["outcomes"]["APPROVED"] += 1
                    
                    if "Risk score" in line:
                        stats["total_risk_denied"] += 1
                except:
                    continue

        return stats

if __name__ == "__main__":
    analyzer = GovernanceAnalytics()
    report = analyzer.generate_report()
    print("--- GOVERNANCE ANALYTICS REPORT ---")
    print(f"Total Transactions Processed: {report.get('total_actions')}")
    print(f"Outcomes: {dict(report.get('outcomes'))}")
    print(f"Risk Denials: {report.get('total_risk_denied')}")
