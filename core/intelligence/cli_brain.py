import sys
from anomaly_detector import IntelligenceCore

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
