import argparse
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.safety.integrity import sign_entry, verify_audit_chain

def run_tool(name):
    path = os.path.join(ROOT, "tools", name)
    if not os.path.exists(path):
        print(f"Missing: {path}")
        return False

    spec = importlib.util.spec_from_file_location(name.replace(".py", ""), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if hasattr(module, "main"):
        module.main()
        return True

    print(f"Missing main() in {path}")
    return False

def get_status():
    identity_path = os.path.join(ROOT, "config", "identity.json")
    identity = "ASO-PRIME-X1"
    if os.path.exists(identity_path):
        with open(identity_path, "r", encoding="utf-8") as f:
            identity = json.load(f).get("identity", identity)
    return {"status": "operational", "identity": identity}

def main():
    parser = argparse.ArgumentParser(description="ASO-X Command Line Interface")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status")
    sub.add_parser("verify-chain")
    sub.add_parser("roadmap")
    sub.add_parser("ai-cycle")
    sub.add_parser("backtest")

    args = parser.parse_args()

    if args.command == "status":
        result = get_status()
        print(json.dumps(result, indent=4))
        sign_entry({"command": "status", "result": result}, "asoctl")
    elif args.command == "verify-chain":
        print(json.dumps(verify_audit_chain(), indent=4))
    elif args.command == "ai-cycle":
        ok = run_tool("aso_ai.py")
        if ok:
            sign_entry({"command": "ai-cycle", "status": "completed"}, "offline_ai")
    elif args.command == "backtest":
        run_tool("aso_backtest.py")
    elif args.command == "roadmap":
        run_tool("aso_roadmap.py")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
