import sys
import json
import subprocess
from roadmap_sync import sync_roadmap

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "sync":
        print(json.dumps(sync_roadmap(trigger="cli"), indent=2))
    elif cmd == "validate":
        r1 = subprocess.run([sys.executable, "roadmap_guard.py"])
        r2 = subprocess.run([sys.executable, "validate_roadmap_state.py"])
        sys.exit(0 if r1.returncode == 0 and r2.returncode == 0 else 1)
    else:
        print("ASO-X Roadmap CLI: [sync | validate]")

if __name__ == "__main__":
    main()