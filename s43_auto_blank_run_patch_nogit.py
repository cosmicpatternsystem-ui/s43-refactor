import hashlib
import pathlib
import re
import sys
from datetime import datetime

APPLY = "--apply" in sys.argv
ACK = "I_APPROVE_CYCLE_002"

if APPLY:
    import os
    if os.environ.get("S43_UNLOCK_ACK") != ACK:
        print("ERROR: apply requires S43_UNLOCK_ACK=I_APPROVE_CYCLE_002", file=sys.stderr)
        sys.exit(3)

ROOT = pathlib.Path(".").resolve()
SKIP_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", ".nox", ".venv", "venv", "env", "node_modules"
}

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def nonempty_lines(data):
    return [ln for ln in data.splitlines(keepends=True) if ln.strip(b" \t\r\n")]

def normalize(data):
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    return re.sub(rb"(?:\r?\n[ \t]*){3,}", nl + nl, data)

def should_skip(path):
    return any(part in SKIP_DIRS for part in path.parts)

files = []
for path in ROOT.rglob("*.py"):
    rel = path.relative_to(ROOT)
    if should_skip(rel):
        continue
    if path.is_file():
        files.append(path)

changes = []
for path in files:
    original = path.read_bytes()
    patched = normalize(original)

    if original == patched:
        continue

    if nonempty_lines(original) != nonempty_lines(patched):
        print(f"ERROR: refusing non-empty content change: {path}", file=sys.stderr)
        sys.exit(10)

    changes.append((path, original, patched, sha256(original), sha256(patched)))

print("S43_CYCLE_002_AUTO_BLANK_RUN_PATCH")
print("MODE=" + ("APPLY" if APPLY else "DRY_RUN"))
print(f"ROOT={ROOT}")
print(f"SCANNED_FILES={len(files)}")
print(f"CANDIDATE_FILES={len(changes)}")

if not changes:
    print("NO_CHANGE_REQUIRED")
    sys.exit(0)

for path, original, patched, before, after in changes:
    rel = path.relative_to(ROOT)
    print(f"CHANGE {rel}")
    print(f"  before={before}")
    print(f"  after ={after}")

if not APPLY:
    print("DRY_RUN_ONLY")
    print("To apply:")
    print("  $env:S43_UNLOCK_ACK = 'I_APPROVE_CYCLE_002'")
    print("  py -3 .\\s43_auto_blank_run_patch_nogit.py --apply")
    sys.exit(0)

backup_root = ROOT / (".s43_cycle002_backup_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
backup_root.mkdir()

for path, original, patched, before, after in changes:
    rel = path.relative_to(ROOT)
    backup_path = backup_root / rel
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_bytes(original)
    path.write_bytes(patched)
    print(f"APPLIED {rel}")

print("PATCH_APPLIED_SAFELY")
print("BACKUP_DIR=" + str(backup_root))
