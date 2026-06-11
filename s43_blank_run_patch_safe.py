import hashlib
import pathlib
import sys
from datetime import datetime

APPLY = "--apply" in sys.argv
ACK = "I_APPROVE_CYCLE_002"

args = [x for x in sys.argv[1:] if x != "--apply"]
if not args:
    print("ERROR: provide explicit target file(s). Example:")
    print("  py -3 .\\s43_blank_run_patch_safe.py .\\s43_instrumented_LATEST.py")
    sys.exit(2)

if APPLY:
    import os
    if os.environ.get("S43_UNLOCK_ACK") != ACK:
        print("ERROR: apply requires S43_UNLOCK_ACK=I_APPROVE_CYCLE_002", file=sys.stderr)
        sys.exit(3)

ROOT = pathlib.Path(".").resolve()

def sha256(data):
    return hashlib.sha256(data).hexdigest().upper()

def nonempty_lines(data):
    return [ln for ln in data.splitlines(keepends=True) if ln.strip(b" \t\r\n")]

def normalize_blank_runs_line_based(data):
    out = []
    blank_run = 0

    for line in data.splitlines(keepends=True):
        if line.strip(b" \t\r\n") == b"":
            blank_run += 1
            if blank_run <= 2:
                out.append(line)
            continue

        blank_run = 0
        out.append(line)

    return b"".join(out)

targets = []
for raw in args:
    path = pathlib.Path(raw)
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    if not path.is_file():
        print(f"ERROR: not a file: {path}", file=sys.stderr)
        sys.exit(4)
    targets.append(path)

changes = []
for path in targets:
    original = path.read_bytes()
    patched = normalize_blank_runs_line_based(original)

    if original == patched:
        continue

    if nonempty_lines(original) != nonempty_lines(patched):
        print(f"ERROR: refusing non-empty content change: {path}", file=sys.stderr)
        sys.exit(10)

    changes.append((path, original, patched, sha256(original), sha256(patched)))

print("S43_CYCLE_002_SAFE_LINE_BASED_BLANK_RUN_PATCH")
print("MODE=" + ("APPLY" if APPLY else "DRY_RUN"))
print(f"ROOT={ROOT}")
print(f"TARGET_FILES={len(targets)}")
print(f"CANDIDATE_FILES={len(changes)}")

if not changes:
    print("NO_CHANGE_REQUIRED")
    sys.exit(0)

for path, original, patched, before, after in changes:
    rel = path
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        pass
    print(f"CHANGE {rel}")
    print(f"  before={before}")
    print(f"  after ={after}")
    print(f"  bytes_before={len(original)}")
    print(f"  bytes_after ={len(patched)}")
    print(f"  removed_bytes={len(original) - len(patched)}")

if not APPLY:
    print("DRY_RUN_ONLY")
    print("To apply:")
    print("  $env:S43_UNLOCK_ACK = 'I_APPROVE_CYCLE_002'")
    print("  py -3 .\\s43_blank_run_patch_safe.py --apply .\\s43_instrumented_LATEST.py")
    sys.exit(0)

backup_root = ROOT / (".s43_cycle002_backup_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
backup_root.mkdir()

for path, original, patched, before, after in changes:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = pathlib.Path(path.name)

    backup_path = backup_root / rel
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_bytes(original)
    path.write_bytes(patched)
    print(f"APPLIED {rel}")

print("PATCH_APPLIED_SAFELY")
print("BACKUP_DIR=" + str(backup_root))
