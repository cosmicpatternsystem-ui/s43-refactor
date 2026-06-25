import sys
import os

# افزودن ریشه پروه به مسیرهای سیستم
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # استفاده از مسیر کامل پکیج
    from core.intelligence.pattern_recognition.anomaly_detector import IntelligenceCore
except ImportError as e:
    print(f"[!] Critical Import Error: {e}")
    sys.exit(1)

def main():
    print("========================================")
    print("   ASO-X PRIME-X1 | INTELLIGENCE UNIT   ")
    print("========================================")
    
    # مسیر لاگ را نسبت به ریشه پروه تنظیم میکنیم
    log_path = os.path.join(project_root, 'runtime/audit/audit_log.json')
    core = IntelligenceCore(log_path=log_path)
    core.generate_report()
    
    print("[*] Diagnostics Complete.")
    print("[*] Memory State: PERSISTENT")
    print("========================================")

if __name__ == "__main__":
    main()
