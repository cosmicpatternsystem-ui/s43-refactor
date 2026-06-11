#!/usr/bin/env bash
set -euo pipefail

TARGET_FILE="${1:-s43.py}"
REPORT_FILE="${2:-s43_readonly_probe_report.txt}"
TMP_DIR="${3:-.s43_probe_tmp}"

BEGIN_TIME="$(date '+%Y-%m-%d %H:%M:%S' 2>/dev/null || true)"
PWD_NOW="$(pwd)"

mkdir -p "$TMP_DIR"

PY_COMPILE_STDOUT="$TMP_DIR/s43_py_compile_stdout.txt"
PY_COMPILE_STDERR="$TMP_DIR/s43_py_compile_stderr.txt"

write_line() {
  printf '%s\n' "$1" | tee -a "$REPORT_FILE" >/dev/null
}

write_kv() {
  printf '%-32s %s\n' "$1:" "$2" | tee -a "$REPORT_FILE" >/dev/null
}

reset_report() {
  : > "$REPORT_FILE"
}

check_command() {
  if command -v "$1" >/dev/null 2>&1; then
    printf 'YES'
  else
    printf 'NO'
  fi
}

file_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    printf 'UNAVAILABLE'
  fi
}

line_count() {
  wc -l < "$1" | tr -d ' '
}

byte_count() {
  wc -c < "$1" | tr -d ' '
}

grep_count() {
  grep -c "$1" "$TARGET_FILE" 2>/dev/null || true
}

first_match_line() {
  grep -n "$1" "$TARGET_FILE" 2>/dev/null | head -n 1 || true
}

all_match_lines_limited() {
  grep -n "$1" "$TARGET_FILE" 2>/dev/null | head -n 20 || true
}

reset_report

write_line "S43 READONLY PROBE REPORT"
write_line "========================="
write_kv "status" "STARTED"
write_kv "time" "${BEGIN_TIME:-UNKNOWN}"
write_kv "working_directory" "$PWD_NOW"
write_kv "target_file" "$TARGET_FILE"
write_kv "report_file" "$REPORT_FILE"
write_kv "tmp_dir" "$TMP_DIR"
write_line ""

write_line "ENVIRONMENT"
write_line "-----------"
write_kv "shell" "${SHELL:-UNKNOWN}"
write_kv "uname" "$(uname -a 2>/dev/null || printf 'UNKNOWN')"
write_kv "python3_available" "$(check_command python3)"
write_kv "python_available" "$(check_command python)"
write_kv "sha256sum_available" "$(check_command sha256sum)"
write_kv "grep_available" "$(check_command grep)"
write_kv "awk_available" "$(check_command awk)"
write_kv "sed_available" "$(check_command sed)"
write_line ""

if [ ! -f "$TARGET_FILE" ]; then
  write_line "TARGET FILE"
  write_line "-----------"
  write_kv "exists" "NO"
  write_kv "final_status" "FAIL_TARGET_NOT_FOUND"
  exit 1
fi

write_line "TARGET FILE"
write_line "-----------"
write_kv "exists" "YES"
write_kv "readable" "$([ -r "$TARGET_FILE" ] && printf YES || printf NO)"
write_kv "writable" "$([ -w "$TARGET_FILE" ] && printf YES || printf NO)"
write_kv "lines" "$(line_count "$TARGET_FILE")"
write_kv "bytes" "$(byte_count "$TARGET_FILE")"
write_kv "sha256" "$(file_sha256 "$TARGET_FILE")"
write_line ""

write_line "PYTHON COMPILE CHECK"
write_line "--------------------"
PY_CMD=""
if command -v python3 >/dev/null 2>&1; then
  PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PY_CMD="python"
fi

if [ -z "$PY_CMD" ]; then
  write_kv "python_command" "UNAVAILABLE"
  write_kv "py_compile" "SKIPPED"
else
  write_kv "python_command" "$PY_CMD"
  : > "$PY_COMPILE_STDOUT"
  : > "$PY_COMPILE_STDERR"
  if "$PY_CMD" -m py_compile "$TARGET_FILE" >"$PY_COMPILE_STDOUT" 2>"$PY_COMPILE_STDERR"; then
    write_kv "py_compile" "PASS"
  else
    write_kv "py_compile" "FAIL"
    write_line ""
    write_line "py_compile stderr:"
    sed -n '1,80p' "$PY_COMPILE_STDERR" | tee -a "$REPORT_FILE" >/dev/null || true
  fi
fi
write_line ""

write_line "PROJECT MARKERS"
write_line "---------------"
write_kv "AUTOPATCH_STAGE1_MARKER_count" "$(grep_count 'AUTOPATCH_STAGE1_MARKER')"
write_kv "_s43_autopatch_probe_count" "$(grep_count '_s43_autopatch_probe')"
write_kv "monkey_patch_mentions" "$(grep_count 'monkey')"
write_kv "official_patch_mentions" "$(grep_count 'patch')"
write_kv "dataclass_frozen_mentions" "$(grep_count '@dataclass(frozen=True)')"
write_line ""

write_line "FIRST MATCHES"
write_line "-------------"
write_line "AUTOPATCH_STAGE1_MARKER:"
first_match_line 'AUTOPATCH_STAGE1_MARKER' | tee -a "$REPORT_FILE" >/dev/null
write_line ""
write_line "_s43_autopatch_probe:"
first_match_line '_s43_autopatch_probe' | tee -a "$REPORT_FILE" >/dev/null
write_line ""
write_line "@dataclass(frozen=True):"
all_match_lines_limited '@dataclass(frozen=True)' | tee -a "$REPORT_FILE" >/dev/null
write_line ""

write_line "STRUCTURE INVENTORY"
write_line "-------------------"
write_kv "class_count" "$(grep_count '^class ')"
write_kv "def_count" "$(grep_count '^def ')"
write_kv "async_def_count" "$(grep_count '^async def ')"
write_kv "import_count" "$(grep_count '^import ')"
write_kv "from_import_count" "$(grep_count '^from ')"
write_line ""

write_line "TOP LEVEL CLASSES"
write_line "-----------------"
grep -n '^class ' "$TARGET_FILE" 2>/dev/null | head -n 80 | tee -a "$REPORT_FILE" >/dev/null || true
write_line ""

write_line "TOP LEVEL FUNCTIONS"
write_line "-------------------"
grep -n '^def ' "$TARGET_FILE" 2>/dev/null | head -n 120 | tee -a "$REPORT_FILE" >/dev/null || true
write_line ""

write_line "ASYNC TOP LEVEL FUNCTIONS"
write_line "-------------------------"
grep -n '^async def ' "$TARGET_FILE" 2>/dev/null | head -n 120 | tee -a "$REPORT_FILE" >/dev/null || true
write_line ""

write_line "RISK KEYWORDS SUMMARY"
write_line "---------------------"
write_kv "eval_count" "$(grep_count 'eval(')"
write_kv "exec_count" "$(grep_count 'exec(')"
write_kv "subprocess_count" "$(grep_count 'subprocess')"
write_kv "os_system_count" "$(grep_count 'os.system')"
write_kv "pickle_count" "$(grep_count 'pickle')"
write_kv "requests_count" "$(grep_count 'requests')"
write_kv "sqlite_count" "$(grep_count 'sqlite')"
write_kv "thread_count" "$(grep_count 'thread')"
write_kv "asyncio_count" "$(grep_count 'asyncio')"
write_line ""

write_line "READONLY POLICY RESULT"
write_line "----------------------"
write_kv "modified_target" "NO"
write_kv "restore_performed" "NO"
write_kv "patch_performed" "NO"
write_kv "refactor_performed" "NO"
write_kv "report_generated" "YES"
write_kv "final_status" "READONLY_PROBE_COMPLETE"

printf '\nReport written to: %s\n' "$REPORT_FILE"
printf 'Temporary files kept in: %s\n' "$TMP_DIR"
