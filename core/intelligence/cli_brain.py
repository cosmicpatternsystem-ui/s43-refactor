import sys
import os

# پیدا کردن مسیر ریشه پروه (دو مرحله بالاتر از فایل فعلی)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.append(project_root)
sys.path.append(current_dir) # برای اطمینان از شناسایی فایلهای کنار هم

try:
    from anomaly_detector import IntelligenceCore
except ImportError as e:
    print(f"[!] Error: {e}")
    sys.exit(1)

def main():
    print("========================================")
    print("   ASO-X PRIME-X1 | INTELLIGENCE UNIT   ")
    print("========================================")
    
    core = IntelligenceCore()
    core.generate_report()
    
    print("[*] Diagnostics Complete.")
    print("[*] Memory State: PERSISTENT")
    print("========================================")

if __name__ == "__main__":
    main()
