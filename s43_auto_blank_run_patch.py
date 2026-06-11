import hashlib
import pathlib
import re
import subprocess
import sys
from datetime import datetime

APPLY = "--apply" in sys.argv
ACK = "I_APPROVE_CYCLE_002"

if APPLY:
    import os
    if os.environ.get("S43_UNLOCK_ACK") != ACK:
        print("ERROR: apply requires S43_UNLOCK_ACK=I_APPROVE_CYCLE_002", file=sys.stderr)
        sys.exit(3)

def run(cmd):
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def nonempty_lines(data):
    return [ln for ln in data.splitlines(keepends=True) if ln.strip(b" \t\r\n")]

def normalize(data):
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    return re.sub(rb"(?:\r?\n[ \t]*){3,}", nl + nl, data)

tracked = run(["git", "ls-files", "--", "*.py"])
if tracked.returncode != 0:
    print(tracked.stdout, file=sys.stderr)
    sys.exit(4)

files = [pathlib.Path(x) for x in tracked.stdout.splitlines() if x.strip()]
if not files:
    print("No git-tracked Python files found.")
    sys.exit(0)

changes = []
for path in files:
    if not path.is_file():
        continue

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
print(f"SCANNED_FILES={len(files)}")
print(f"CANDIDATE_FILES={len(changes)}")

if not changes:
    print("NO_CHANGE_REQUIRED")
    sys.exit(0)

for path, original, patched, before, after in changes:
    print(f"CHANGE {path}")
    print(f"  before={before}")
    print(f"  after ={after}")

if not APPLY:
    print("DRY_RUN_ONLY")
    print("To apply:")
    print("  $env:S43_UNLOCK_ACK = 'I_APPROVE_CYCLE_002'")
    print("  py -3 .\\s43_auto_blank_run_patch.py --apply")
    sys.exit(0)

backup_root = pathlib.Path(".s43_cycle002_backup_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
backup_root.mkdir()

for path, original, patched, before, after in changes:
    backup_path = backup_root / path
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_bytes(original)
    path.write_bytes(patched)
    print(f"APPLIED {path}")

check = run(["git", "diff", "--check"])
print("GIT_DIFF_CHECK_RESULT=" + str(check.returncode))
if check.stdout.strip():
    print(check.stdout.rstrip())

if check.returncode != 0:
    print("ERROR: git diff --check failed. Backup is in " + str(backup_root), file=sys.stderr)
    sys.exit(20)

print("PATCH_APPLIED_SAFELY")
print("BACKUP_DIR=" + str(backup_root))
print("NEXT:")
print("  git diff --check")
print("  git diff --stat")
print("  git diff -- *.py")
