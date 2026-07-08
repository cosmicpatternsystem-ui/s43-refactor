import json
import os

class IntelligenceCore:
    def __init__(self, log_path='runtime/audit/audit_log.json'):
        self.log_path = log_path

    def calculate_integrity_score(self):
        if not os.path.exists(self.log_path): return 0
        with open(self.log_path, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
        total_entries = len(logs)
        if total_entries == 0: return 100
        
        # فرمول محاسباتی هوش هسته:
        # کسر امتیاز بر اساس خطاهای سیستمی و هشدارهای ثبت شده
        criticals = len([l for l in logs if l.get('status') == 'CRITICAL'])
        warnings = len([l for l in logs if l.get('status') == 'WARNING'])
        
        # جریمه برای هر خطا
        score = 100 - (criticals * 5) - (warnings * 2)
        return max(score, 0)

    def generate_report(self):
        score = self.calculate_integrity_score()
        print(f"\n--- ASO-X INTELLIGENCE REPORT ---")
        print(f"System Integrity Score: {score}/100")
        if score > 90:
            print("Status: ELITE - Infrastructure is optimal.")
        elif score > 70:
            print("Status: STABLE - Minor optimizations recommended.")
        else:
            print("Status: DEGRADED - Immediate inspection required!")
        print(f"----------------------------------\n")

if __name__ == "__main__":
    core = IntelligenceCore()
    core.generate_report()
