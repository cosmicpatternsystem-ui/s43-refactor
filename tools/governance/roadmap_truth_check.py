import os
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

REQUIRED_FILES = [
    ROOT / "docs" / "governance" / "ROADMAP_CURRENT.json",
    ROOT / "docs" / "governance" / "ROADMAP_CANONICAL.md"
]

def fail(msg):
    print(f"[FAIL] {msg}", file=sys.stderr)

def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def main():
    rc = 0
    for f in REQUIRED_FILES:
        if not f.exists():
            fail(f"missing required file: {f.relative_to(ROOT)}")
            rc = 1
            continue

    if rc:
        return rc

    try:
        roadmap_path = ROOT / "docs" / "governance" / "ROADMAP_CURRENT.json"
        roadmap_json = json.loads(read_text(roadmap_path))
        
        if roadmap_json.get("canonical_roadmap") != "ROADMAP_CANONICAL.md":
            fail("ROADMAP_CURRENT.json canonical_roadmap must equal ROADMAP_CANONICAL.md")
            rc = 1
            
    except Exception as e:
        fail(f"failed to parse or validate roadmap json: {str(e)}")
        rc = 1

    if rc == 0:
        print("[OK] Roadmap Repository Truth Gate validation successful.")
    return rc

if __name__ == "__main__":
    sys.exit(main())