import os
import re
import json
import hashlib
from datetime import datetime, timezone

EXPECTED_S43_SHA256 = "8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786"

EXCLUDED_DIR_NAMES = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".terminal_backups", ".release_evidence", ".audit_discovery", ".patch_audit",
    "backups", "archive_packed_backup", "sealed_artifacts", "snapshots",
    "candidates", "verify_s43_snapshot",
}

EXCLUDED_PATH_MARKERS = [
    "/final_release_", "/phase13_", "/phase14_",
    "/laptop_active_gap_v", "/active_gap_review_", "/roadmap_consolidation_",
]

INCLUDED_TOP_DIRS = ["docs", "tools", "s43_project"]
INCLUDED_ROOT_FILES = [
    "README", "README.md", "FUTURE_PHASES_ROADMAP.md", "NEXT_SESSION_ROADMAP.md",
    "THREE_WALLETS_RUNTIME_PLAN.md", "s43_refactor_plan.md", "s43_patch_plan_report.txt",
]
INCLUDED_EXTENSIONS = {".py", ".md", ".txt", ".json", ".cmd", ".bat", ".sh"}

STRICT_TODO_PATTERN = re.compile(
    r"\b(TODO|FIXME|XXX|HACK|WIP|TBD|PENDING_REVIEW|NEXT_ACTION|ACTION_REQUIRED|REVIEW_REQUIRED|FOLLOW_UP_REQUIRED|BLOCKER)\b",
    re.IGNORECASE,
)
ROADMAP_PATTERN = re.compile(
    r"\b(roadmap|next action|next_action|milestone|backlog|phase plan|release plan|patch plan|implementation plan)\b",
    re.IGNORECASE,
)
FALSE_POSITIVE_STATE_PATTERN = re.compile(r"\b(OPEN|PENDING|CLOSED|FAILED|PASS|PASSED|UNKNOWN|RUNNING)\b")

def utc_stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

def utc_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def to_posix(path):
    return path.replace("\\", "/")

def display_path(path):
    p = to_posix(path)
    return p if p.startswith("./") else "./" + p

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read_text_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    except OSError:
        return []

def write_lines(path, lines):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write(str(line) + "\n")

def write_json(path, data):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")

def is_excluded_path(path):
    p = "/" + to_posix(path).strip("/") + "/"
    parts = [x for x in p.split("/") if x]
    if any(part in EXCLUDED_DIR_NAMES for part in parts):
        return True
    return any(marker in p for marker in EXCLUDED_PATH_MARKERS)

def is_text_candidate(path):
    return os.path.splitext(path)[1].lower() in INCLUDED_EXTENSIONS

def collect_active_review_files():
    files = []

    if os.path.isfile("s43.py"):
        files.append("s43.py")

    for name in INCLUDED_ROOT_FILES:
        if os.path.isfile(name):
            files.append(name)

    for name in os.listdir("."):
        if os.path.isfile(name) and name.startswith("README_") and is_text_candidate(name):
            files.append(name)

    for top in INCLUDED_TOP_DIRS:
        if not os.path.isdir(top):
            continue
        for base, dirs, names in os.walk(top):
            dirs[:] = [d for d in dirs if not is_excluded_path(os.path.join(base, d))]
            if is_excluded_path(base):
                continue
            for name in names:
                path = os.path.join(base, name)
                if is_excluded_path(path):
                    continue
                if is_text_candidate(path):
                    files.append(path)

    return sorted(set(display_path(x) for x in files))

def collect_roadmap_candidates(files):
    result = []
    for shown in files:
        path = shown[2:] if shown.startswith("./") else shown
        base = os.path.basename(path).upper()
        if "ROADMAP" in base or "PLAN" in base or base.startswith("NEXT_SESSION"):
            result.append(shown)
            continue
        text = "".join(read_text_lines(path))
        if ROADMAP_PATTERN.search(text):
            result.append(shown)
    return sorted(set(result))

def is_strict_action_line(line):
    if not STRICT_TODO_PATTERN.search(line):
        return False
    stripped = line.strip()
    if not stripped:
        return False
    if FALSE_POSITIVE_STATE_PATTERN.fullmatch(stripped):
        return False
    return True

def collect_strict_todos(files):
    rows = []
    counts = {}

    for shown in files:
        path = shown[2:] if shown.startswith("./") else shown
        for line_no, line in enumerate(read_text_lines(path), 1):
            text = line.rstrip("\n")
            if is_strict_action_line(text):
                rows.append({"file": shown, "line": line_no, "text": text})
                counts[shown] = counts.get(shown, 0) + 1

    return rows, counts

def main():
    root = os.getcwd()
    s43_path = os.path.join(root, "s43.py")

    if not os.path.isfile(s43_path):
        print("ERROR: s43.py not found in current directory.")
        return 2

    actual_hash = sha256_file(s43_path)
    stamp = utc_stamp()
    outdir = os.path.join("docs", "laptop_active_gap_v4_" + stamp)
    os.makedirs(outdir, exist_ok=True)

    summary_path = os.path.join(outdir, "SUMMARY_FOR_ASSISTANT.txt")
    active_files_path = os.path.join(outdir, "ACTIVE_REVIEW_FILES.txt")
    roadmap_path = os.path.join(outdir, "STRICT_ROADMAP_CANDIDATES.txt")
    todos_path = os.path.join(outdir, "STRICT_TODO_FIXME_CANDIDATES.txt")
    todos_json_path = os.path.join(outdir, "STRICT_TODO_FIXME_CANDIDATES.json")
    todos_by_file_path = os.path.join(outdir, "STRICT_TODO_FIXME_BY_FILE.txt")
    decision_path = os.path.join(outdir, "NEXT_PATCH_DECISION.md")
    pointer_path = os.path.join("docs", "S43_LAPTOP_ACTIVE_GAP_V4_POINTER.md")

    hash_status = "MATCH" if actual_hash == EXPECTED_S43_SHA256 else "MISMATCH"

    summary = [
        "# S43 Laptop Active Gap Filter v4",
        "created_at_utc=" + utc_iso(),
        "root=" + to_posix(root),
        "expected_s43_sha256=" + EXPECTED_S43_SHA256,
        "actual_s43_sha256=" + actual_hash,
        "s43_hash_status=" + hash_status,
    ]

    if hash_status != "MATCH":
        summary.append("status=STOPPED_HASH_MISMATCH")
        write_lines(summary_path, summary)
        print("ERROR: s43.py hash mismatch.")
        print("EXPECTED=" + EXPECTED_S43_SHA256)
        print("ACTUAL=" + actual_hash)
        print("SUMMARY=" + to_posix(summary_path))
        return 2

    active_files = collect_active_review_files()
    roadmap_candidates = collect_roadmap_candidates(active_files)
    todo_rows, todo_counts = collect_strict_todos(active_files)

    write_lines(active_files_path, active_files)
    write_lines(roadmap_path, ["STRICT ROADMAP CANDIDATES", ""] + roadmap_candidates)

    todo_text_lines = ["STRICT TODO/FIXME CANDIDATES", ""]
    for row in todo_rows[:300]:
        todo_text_lines.append(f"{row['file']}:{row['line']}:{row['text']}")
    write_lines(todos_path, todo_text_lines)
    write_json(todos_json_path, todo_rows[:300])

    by_file_lines = ["STRICT TODO/FIXME BY FILE", ""]
    for path, count in sorted(todo_counts.items(), key=lambda item: (-item[1], item[0])):
        by_file_lines.append(f"{count:6d}  {path}")
    write_lines(todos_by_file_path, by_file_lines)

    decision = [
        "# S43 Next Patch Decision",
        "",
        "Integrity:",
        "s43.py.sha256=" + actual_hash,
        "s43.py.status=MATCH",
        "",
        "Governance:",
        "PRIMARY_WORK_SURFACE=LAPTOP",
        "TERMUX_PHONE_ROLE=FINAL_VERIFY_ONLY",
        "S43_PY_MODIFIED=NO",
        "STRICT_FILTER_V4_APPLIED=YES",
        "OPEN_PENDING_RUNTIME_STATE_FALSE_POSITIVES_REMOVED=YES",
        "FUNCTIONAL_PATCH_APPROVED=NO",
        "NEXT_STEP=REVIEW_STRICT_ACTIVE_GAPS_BEFORE_ANY_S43_CHANGE",
        "",
        "Counts:",
        "active_review_files=" + str(len(active_files)),
        "strict_roadmap_candidates=" + str(len(roadmap_candidates)),
        "strict_todo_fixme_lines_capped_at_300=" + str(min(len(todo_rows), 300)),
        "strict_todo_fixme_total_lines=" + str(len(todo_rows)),
        "strict_todo_fixme_files=" + str(len(todo_counts)),
        "",
        "Artifacts:",
        to_posix(active_files_path),
        to_posix(roadmap_path),
        to_posix(todos_by_file_path),
        to_posix(todos_path),
        to_posix(todos_json_path),
        to_posix(summary_path),
    ]
    write_lines(decision_path, decision)

    summary.extend([
        "status=COMPLETED",
        "active_review_files=" + str(len(active_files)),
        "strict_roadmap_candidates=" + str(len(roadmap_candidates)),
        "strict_todo_fixme_lines_capped_at_300=" + str(min(len(todo_rows), 300)),
        "strict_todo_fixme_total_lines=" + str(len(todo_rows)),
        "strict_todo_fixme_files=" + str(len(todo_counts)),
        "outdir=" + to_posix(outdir),
        "active_files=" + to_posix(active_files_path),
        "roadmaps=" + to_posix(roadmap_path),
        "todos_by_file=" + to_posix(todos_by_file_path),
        "todos=" + to_posix(todos_path),
        "todos_json=" + to_posix(todos_json_path),
        "decision=" + to_posix(decision_path),
    ])
    write_lines(summary_path, summary)

    pointer = [
        "# S43 Laptop Active Gap v4 Pointer",
        "",
        "latest_laptop_active_gap_v4_dir:",
        to_posix(outdir),
        "",
        "files:",
        "- " + to_posix(active_files_path),
        "- " + to_posix(roadmap_path),
        "- " + to_posix(todos_by_file_path),
        "- " + to_posix(todos_path),
        "- " + to_posix(todos_json_path),
        "- " + to_posix(decision_path),
        "- " + to_posix(summary_path),
    ]
    write_lines(pointer_path, pointer)

    print("LAPTOP_ACTIVE_GAP_FILTER_V4_APPLIED")
    print("OUTDIR=" + to_posix(outdir))
    print("POINTER=" + to_posix(pointer_path))
    print("S43_SHA256=" + actual_hash)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
