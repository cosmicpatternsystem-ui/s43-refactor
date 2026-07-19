import os, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CANONICAL_DIR = ROOT / "docs" / "governance"
REQUIRED_FILES = [
    CANONICAL_DIR / "ROADMAP_CURRENT.json",
    CANONICAL_DIR / "ROADMAP_CANONICAL.md"
]

def main():
    rc = 0
    for f in REQUIRED_FILES:
        if not f.exists():
            print(f"[FAIL] Missing canonical authority: {f.relative_to(ROOT)}", file=sys.stderr)
            rc = 1
    
    if rc == 0:
        try:
            data = json.loads((CANONICAL_DIR / "ROADMAP_CURRENT.json").read_text(encoding="utf-8"))
            if "ROADMAP_CANONICAL.md" not in data.get("canonical_roadmap", ""):
                print("[FAIL] ROADMAP_CURRENT.json integrity violation.", file=sys.stderr)
                rc = 1
        except Exception as e:
            print(f"[FAIL] Parse error: {e}", file=sys.stderr)
            rc = 1

    if rc == 0: print("[OK] Governance Repository Truth Gate Passed.")
    return rc

if __name__ == "__main__": sys.exit(main())