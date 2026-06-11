@echo off
setlocal EnableExtensions

if not exist "s43.py" (
  echo ERROR: s43.py not found in current directory.
  echo Run this command from the project root.
  exit /b 2
)

if not exist "tools" mkdir "tools"
if not exist "docs" mkdir "docs"

> "tools\s43_laptop_active_gap_filter_v4.py" (
echo import os
echo import re
echo import sys
echo import json
echo import hashlib
echo from datetime import datetime, timezone
echo.
echo EXPECTED_S43_SHA256 = "8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786"
echo ROOT = os.getcwd()
echo S43_PATH = os.path.join(ROOT, "s43.py")
echo.
echo EXCLUDED_DIR_NAMES = {
echo     ".git",
echo     "__pycache__",
echo     ".pytest_cache",
echo     ".mypy_cache",
echo     ".ruff_cache",
echo     ".terminal_backups",
echo     ".release_evidence",
echo     ".audit_discovery",
echo     ".patch_audit",
echo     "backups",
echo     "archive_packed_backup",
echo     "sealed_artifacts",
echo     "snapshots",
echo     "candidates",
echo     "verify_s43_snapshot",
echo }
echo.
echo EXCLUDED_PATH_MARKERS = [
echo     "/final_release_",
echo     "/phase13_",
echo     "/phase14_",
echo     "/laptop_active_gap_v",
echo     "/active_gap_review_",
echo     "/roadmap_consolidation_",
echo ]
echo.
echo INCLUDED_TOP_DIRS = [
echo     "docs",
echo     "tools",
echo     "s43_project",
echo ]
echo.
echo INCLUDED_ROOT_FILES = [
echo     "README",
echo     "README.md",
echo     "FUTURE_PHASES_ROADMAP.md",
echo     "NEXT_SESSION_ROADMAP.md",
echo     "THREE_WALLETS_RUNTIME_PLAN.md",
echo     "s43_refactor_plan.md",
echo     "s43_patch_plan_report.txt",
echo ]
echo.
echo INCLUDED_EXTENSIONS = {
echo     ".py",
echo     ".md",
echo     ".txt",
echo     ".json",
echo     ".cmd",
echo     ".bat",
echo     ".sh",
echo }
echo.
echo STRICT_TODO_PATTERN = re.compile(
echo     r"\b("
echo     r"TODO|FIXME|XXX|HACK|WIP|TBD|"
echo     r"PENDING_REVIEW|NEXT_ACTION|ACTION_REQUIRED|"
echo     r"REVIEW_REQUIRED|FOLLOW_UP_REQUIRED|BLOCKER"
echo     r")\b",
echo     re.IGNORECASE,
echo )
echo.
echo ROADMAP_PATTERN = re.compile(
echo     r"\b("
echo     r"roadmap|next action|next_action|milestone|backlog|"
echo     r"phase plan|release plan|patch plan|implementation plan"
echo     r")\b",
echo     re.IGNORECASE,
echo )
echo.
echo FALSE_POSITIVE_STATE_PATTERN = re.compile(
echo     r"\b(OPEN|PENDING|CLOSED|FAILED|PASS|PASSED|UNKNOWN|RUNNING)\b"
echo )
echo.
echo def utc_stamp():
echo     return datetime.now(timezone.utc).strftime("%%Y%%m%%d_%%H%%M%%S")
echo.
echo def utc_iso():
echo     return datetime.now(timezone.utc).strftime("%%Y-%%m-%%dT%%H:%%M:%%SZ")
echo.
echo def to_posix(path):
echo     return path.replace("\\", "/")
echo.
echo def display_path(path):
echo     p = to_posix(path)
echo     if not p.startswith("./"):
echo         p = "./" + p
echo     return p
echo.
echo def sha256_file(path):
echo     h = hashlib.sha256()
echo     with open(path, "rb") as f:
echo         for chunk in iter(lambda: f.read(1024 * 1024), b""):
echo             h.update(chunk)
echo     return h.hexdigest()
echo.
echo def read_text_lines(path):
echo     try:
echo         with open(path, "r", encoding="utf-8", errors="replace") as f:
echo             return f.readlines()
echo     except OSError:
echo         return []
echo.
echo def write_lines(path, lines):
echo     parent = os.path.dirname(path)
echo     if parent:
echo         os.makedirs(parent, exist_ok=True)
echo     with open(path, "w", encoding="utf-8", newline="\n") as f:
echo         for line in lines:
echo             f.write(str(line) + "\n")
echo.
echo def write_json(path, data):
echo     parent = os.path.dirname(path)
echo     if parent:
echo         os.makedirs(parent, exist_ok=True)
echo     with open(path, "w", encoding="utf-8", newline="\n") as f:
echo         json.dump(data, f, indent=2, sort_keys=True)
echo         f.write("\n")
echo.
echo def is_excluded_path(path):
echo     p = "/" + to_posix(path).strip("/") + "/"
echo     parts = [x for x in p.split("/") if x]
echo     if any(part in EXCLUDED_DIR_NAMES for part in parts):
echo         return True
echo     return any(marker in p for marker in EXCLUDED_PATH_MARKERS)
echo.
echo def is_text_candidate(path):
echo     ext = os.path.splitext(path)[1].lower()
echo     return ext in INCLUDED_EXTENSIONS
echo.
echo def collect_active_review_files():
echo     files = []
echo.
echo     if os.path.isfile("s43.py"):
echo         files.append("s43.py")
echo.
echo     for name in INCLUDED_ROOT_FILES:
echo         if os.path.isfile(name):
echo             files.append(name)
echo.
echo     for name in os.listdir("."):
echo         if os.path.isfile(name) and name.startswith("README_") and is_text_candidate(name):
echo             files.append(name)
echo.
echo     for top in INCLUDED_TOP_DIRS:
echo         if not os.path.isdir(top):
echo             continue
echo         for base, dirs, names in os.walk(top):
echo             dirs[:] = [
echo                 d for d in dirs
echo                 if not is_excluded_path(os.path.join(base, d))
echo             ]
echo             if is_excluded_path(base):
echo                 continue
echo             for name in names:
echo                 path = os.path.join(base, name)
echo                 if is_excluded_path(path):
echo                     continue
echo                 if is_text_candidate(path):
echo                     files.append(path)
echo.
echo     return sorted(set(display_path(x) for x in files))
echo.
echo def collect_roadmap_candidates(files):
echo     result = []
echo     for shown in files:
echo         path = shown[2:] if shown.startswith("./") else shown
echo         base = os.path.basename(path).upper()
echo         if "ROADMAP" in base or "PLAN" in base or base.startswith("NEXT_SESSION"):
echo             result.append(shown)
echo             continue
echo         text = "".join(read_text_lines(path))
echo         if ROADMAP_PATTERN.search(text):
echo             result.append(shown)
echo     return sorted(set(result))
echo.
echo def is_strict_action_line(line):
echo     if not STRICT_TODO_PATTERN.search(line):
echo         return False
echo.
echo     stripped = line.strip()
echo     if not stripped:
echo         return False
echo.
echo     if FALSE_POSITIVE_STATE_PATTERN.fullmatch(stripped):
echo         return False
echo.
echo     return True
echo.
echo def collect_strict_todos(files):
echo     rows = []
echo     counts = {}
echo.
echo     for shown in files:
echo         path = shown[2:] if shown.startswith("./") else shown
echo         for line_no, line in enumerate(read_text_lines(path), 1):
echo             text = line.rstrip("\n")
echo             if is_strict_action_line(text):
echo                 rows.append({
echo                     "file": shown,
echo                     "line": line_no,
echo                     "text": text,
echo                 })
echo                 counts[shown] = counts.get(shown, 0) + 1
echo.
echo     return rows, counts
echo.
echo def main():
echo     if not os.path.isfile(S43_PATH):
echo         print("ERROR: s43.py not found in current directory.")
echo         return 2
echo.
echo     actual_hash = sha256_file(S43_PATH)
echo     stamp = utc_stamp()
echo     outdir = os.path.join("docs", "laptop_active_gap_v4_" + stamp)
echo     os.makedirs(outdir, exist_ok=True)
echo.
echo     summary_path = os.path.join(outdir, "SUMMARY_FOR_ASSISTANT.txt")
echo     active_files_path = os.path.join(outdir, "ACTIVE_REVIEW_FILES.txt")
echo     roadmap_path = os.path.join(outdir, "STRICT_ROADMAP_CANDIDATES.txt")
echo     todos_path = os.path.join(outdir, "STRICT_TODO_FIXME_CANDIDATES.txt")
echo     todos_json_path = os.path.join(outdir, "STRICT_TODO_FIXME_CANDIDATES.json")
echo     todos_by_file_path = os.path.join(outdir, "STRICT_TODO_FIXME_BY_FILE.txt")
echo     decision_path = os.path.join(outdir, "NEXT_PATCH_DECISION.md")
echo     pointer_path = os.path.join("docs", "S43_LAPTOP_ACTIVE_GAP_V4_POINTER.md")
echo.
echo     hash_status = "MATCH" if actual_hash == EXPECTED_S43_SHA256 else "MISMATCH"
echo.
echo     summary = [
echo         "# S43 Laptop Active Gap Filter v4",
echo         "created_at_utc=" + utc_iso(),
echo         "root=" + to_posix(ROOT),
echo         "expected_s43_sha256=" + EXPECTED_S43_SHA256,
echo         "actual_s43_sha256=" + actual_hash,
echo         "s43_hash_status=" + hash_status,
echo     ]
echo.
echo     if hash_status != "MATCH":
echo         summary.append("status=STOPPED_HASH_MISMATCH")
echo         write_lines(summary_path, summary)
echo         print("ERROR: s43.py hash mismatch.")
echo         print("EXPECTED=" + EXPECTED_S43_SHA256)
echo         print("ACTUAL=" + actual_hash)
echo         print("SUMMARY=" + to_posix(summary_path))
echo         return 2
echo.
echo     active_files = collect_active_review_files()
echo     roadmap_candidates = collect_roadmap_candidates(active_files)
echo     todo_rows, todo_counts = collect_strict_todos(active_files)
echo.
echo     write_lines(active_files_path, active_files)
echo     write_lines(roadmap_path, ["STRICT ROADMAP CANDIDATES", ""] + roadmap_candidates)
echo.
echo     todo_text_lines = ["STRICT TODO/FIXME CANDIDATES", ""]
echo     for row in todo_rows[:300]:
echo         todo_text_lines.append(f"{row['file']}:{row['line']}:{row['text']}")
echo     write_lines(todos_path, todo_text_lines)
echo     write_json(todos_json_path, todo_rows[:300])
echo.
echo     by_file_lines = ["STRICT TODO/FIXME BY FILE", ""]
echo     for path, count in sorted(todo_counts.items(), key=lambda item: (-item[1], item[0])):
echo         by_file_lines.append(f"{count:6d}  {path}")
echo     write_lines(todos_by_file_path, by_file_lines)
echo.
echo     decision = [
echo         "# S43 Next Patch Decision",
echo         "",
echo         "## Integrity",
echo         "
```text",
echo         "s43.py.sha256=" + actual_hash,
echo         "s43.py.status=MATCH",
echo         "
```",
echo         "",
echo         "## Governance",
echo         "
```text",
echo         "PRIMARY_WORK_SURFACE=LAPTOP",
echo         "TERMUX_PHONE_ROLE=FINAL_VERIFY_ONLY",
echo         "S43_PY_MODIFIED=NO",
echo         "STRICT_FILTER_V4_APPLIED=YES",
echo         "OPEN_PENDING_RUNTIME_STATE_FALSE_POSITIVES_REMOVED=YES",
echo         "FUNCTIONAL_PATCH_APPROVED=NO",
echo         "NEXT_STEP=REVIEW_STRICT_ACTIVE_GAPS_BEFORE_ANY_S43_CHANGE",
echo         "
```",
echo         "",
echo         "## Counts",
echo         "- active_review_files: " + str(len(active_files)),
echo         "- strict_roadmap_candidates: " + str(len(roadmap_candidates)),
echo         "- strict_todo_fixme_lines_capped_at_300: " + str(min(len(todo_rows), 300)),
echo         "- strict_todo_fixme_total_lines: " + str(len(todo_rows)),
echo         "- strict_todo_fixme_files: " + str(len(todo_counts)),
echo         "",
echo         "## Artifacts",
echo         "- " + to_posix(active_files_path),
echo         "- " + to_posix(roadmap_path),
echo         "- " + to_posix(todos_by_file_path),
echo         "- " + to_posix(todos_path),
echo         "- " + to_posix(todos_json_path),
echo         "- " + to_posix(summary_path),
echo     ]
echo     write_lines(decision_path, decision)
echo.
echo     summary.extend([
echo         "status=COMPLETED",
echo         "active_review_files=" + str(len(active_files)),
echo         "strict_roadmap_candidates=" + str(len(roadmap_candidates)),
echo         "strict_todo_fixme_lines_capped_at_300=" + str(min(len(todo_rows), 300)),
echo         "strict_todo_fixme_total_lines=" + str(len(todo_rows)),
echo         "strict_todo_fixme_files=" + str(len(todo_counts)),
echo         "outdir=" + to_posix(outdir),
echo         "active_files=" + to_posix(active_files_path),
echo         "roadmaps=" + to_posix(roadmap_path),
echo         "todos_by_file=" + to_posix(todos_by_file_path),
echo         "todos=" + to_posix(todos_path),
echo         "todos_json=" + to_posix(todos_json_path),
echo         "decision=" + to_posix(decision_path),
echo     ])
echo     write_lines(summary_path, summary)
echo.
echo     pointer = [
echo         "# S43 Laptop Active Gap v4 Pointer",
echo         "",
echo         "latest_laptop_active_gap_v4_dir:",
echo         to_posix(outdir),
echo         "",
echo         "files:",
echo         "- " + to_posix(active_files_path),
echo         "- " + to_posix(roadmap_path),
echo         "- " + to_posix(todos_by_file_path),
echo         "- " + to_posix(todos_path),
echo         "- " + to_posix(todos_json_path),
echo         "- " + to_posix(decision_path),
echo         "- " + to_posix(summary_path),
echo     ]
echo     write_lines(pointer_path, pointer)
echo.
echo     print("LAPTOP_ACTIVE_GAP_FILTER_V4_APPLIED")
echo     print("OUTDIR=" + to_posix(outdir))
echo     print("POINTER=" + to_posix(pointer_path))
echo     print("S43_SHA256=" + actual_hash)
echo     return 0
echo.
echo if __name__ == "__main__":
echo     raise SystemExit(main())
)

> "docs\S43_WORK_SURFACE_POLICY.md" (
echo # S43 Work Surface Policy
echo.
echo PRIMARY_WORK_SURFACE=LAPTOP
echo TERMUX_PHONE_ROLE=FINAL_VERIFY_AND_RUNTIME_ONLY
echo DO_NOT_RUN_HEAVY_DISCOVERY_ON_PHONE=YES
echo DO_NOT_PATCH_S43_PY_WITHOUT_APPROVED_ACTIVE_GAP=YES
echo.
echo Canonical baseline:
echo.
echo
```text
echo 8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786  s43.py
echo 
