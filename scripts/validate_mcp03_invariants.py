"""MCP-03 Invariant Validator - CI Gate (Phase 32.01)."""
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOV = ROOT / "docs" / "governance"
CANONICAL = GOV / "ROADMAP_CANONICAL.md"
CURRENT = GOV / "ROADMAP_CURRENT.json"
GOV_FILES = [CANONICAL, CURRENT, GOV / "MCP03_INVARIANTS.md"]

def _git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
    return r.stdout.strip()

def check_inv_000():
    changed = set(_git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines())
    md = "docs/governance/ROADMAP_CANONICAL.md" in changed
    js = "docs/governance/ROADMAP_CURRENT.json" in changed
    if md != js:
        print(f"  FAIL: atomicity violated at HEAD: MD={md} JSON={js}")
        return False
    return True

def check_inv_001():
    cmd = [sys.executable, str(ROOT / "scripts" / "resolve_next_action.py")]
    r1 = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    r2 = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if r1.stdout != r2.stdout:
        print("  FAIL: resolver output differs between runs")
        return False
    return True

def check_inv_002():
    for line in _git("status", "--porcelain").splitlines():
        if "ledger" in line.lower() and line[:2].strip() in {"D", "R"}:
            print(f"  FAIL: ledger mutation detected: {line}")
            return False
    return True

def check_inv_003():
    if not CANONICAL.exists():
        print("  FAIL: ROADMAP_CANONICAL.md missing")
        return False
    try:
        json.loads(CURRENT.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  FAIL: ROADMAP_CURRENT.json invalid: {e}")
        return False
    return True

def check_inv_004():
    ok = True
    for f in GOV_FILES:
        if not f.exists():
            continue
        raw = f.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            print(f"  FAIL: BOM found in {f.name}"); ok = False
        if b"\r\n" in raw:
            print(f"  FAIL: CRLF found in {f.name}"); ok = False
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            print(f"  FAIL: not valid UTF-8: {f.name}"); ok = False
    return ok

CHECKS = {
    "INV-MCP03-000": check_inv_000,
    "INV-MCP03-001": check_inv_001,
    "INV-MCP03-002": check_inv_002,
    "INV-MCP03-003": check_inv_003,
    "INV-MCP03-004": check_inv_004,
}

def main():
    p = argparse.ArgumentParser(description="MCP-03 invariant validator")
    p.add_argument("--inv", choices=sorted(CHECKS))
    a = p.parse_args()
    items = {a.inv: CHECKS[a.inv]} if a.inv else CHECKS
    failed = []
    for name, fn in items.items():
        ok = fn()
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        if not ok:
            failed.append(name)
    if failed:
        print(f"RESULT: FAIL ({', '.join(failed)})")
        sys.exit(1)
    print("RESULT: PASS (all invariants hold)")

if __name__ == "__main__":
    main()
