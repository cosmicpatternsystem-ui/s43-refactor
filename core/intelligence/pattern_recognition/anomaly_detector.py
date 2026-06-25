import json
import os
from datetime import datetime

class AnomalyDetector:
    def __init__(self, log_path='runtime/audit/audit_log.json'):
        self.log_path = log_path
        self.threshold = 2.0  # ضریب حساسیت برای ناهنجاری

    def load_logs(self):
        if not os.path.exists(self.log_path):
            return []
        with open(self.log_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyze_latency(self):
        logs = self.load_logs()
        if not logs:
            print("[!] No logs found for analysis.")
            return

        print(f"[*] Analyzing {len(logs)} audit entries for anomalies...")
        # در اینجا منطق پیشرفته برای تشخیص الگوهای مشکوک قرار میگیرد
        # فعلاً به عنوان پایه سیستم سلامت زنجیره داده را چک میکند
        anomalies = [log for log in logs if log.get('status') == 'CRITICAL']
        
        if anomalies:
            print(f"[!] ALERT: {len(anomalies)} anomalies detected in the system history!")
        else:
            print("[+] System behavior is within normal parameters.")

if __name__ == "__main__":
    detector = AnomalyDetector()
    detector.analyze_latency()
