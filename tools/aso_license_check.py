import json
import sys

def check_access():
    try:
        with open('LICENSE_COMMERCIAL.json', 'r') as f:
            lic = json.load(f)
            if lic['product'] == "ASO-X Prime":
                print(f"ACCESS_GRANTED: Welcome to {lic['tier_status'] if 'tier_status' in lic else 'Enterprise'} Mode")
                return True
    except:
        print("ACCESS_DENIED: No Valid Commercial License Found.")
        return False

if __name__ == "__main__":
    check_access()
