import sys
import os

# افزودن مسیر فعلی به پایتون برای شناسایی ماولهای همردیف
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from anomaly_detector import IntelligenceCore
except ImportError:
    print("[!] Error: IntelligenceCore not found. Check directory structure.")
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
