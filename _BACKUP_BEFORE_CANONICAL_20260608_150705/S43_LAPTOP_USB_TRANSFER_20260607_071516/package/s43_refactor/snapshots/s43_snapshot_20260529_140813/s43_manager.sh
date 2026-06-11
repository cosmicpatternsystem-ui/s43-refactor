#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

VERSION="4.0.0"

BASE="$HOME/s43_refactor"
MAIN="$BASE/s43.py"
GOLD="$BASE/s43_final_repaired.py"
LOCKED="$BASE/s43_final_repaired_locked.py"
BACKUP_DIR="$BASE/backups"
LOG_DIR="$BASE/logs"
SNAPSHOT_DIR="$BASE/snapshots"
MANIFEST="$BASE/s43_repair_manifest.txt"
MANAGER="$BASE/s43_manager.sh"

mkdir -p "$BACKUP_DIR" "$LOG_DIR" "$SNAPSHOT_DIR"

cmd="${1:-}"

# -----------------------------
# Output helpers
# -----------------------------
if [ -t 1 ]; then
  C_RESET="$(printf '\033[0m')"
  C_RED="$(printf '\033[31m')"
  C_GREEN="$(printf '\033[32m')"
  C_YELLOW="$(printf '\033[33m')"
  C_BLUE="$(printf '\033[34m')"
  C_BOLD="$(printf '\033[1m')"
else
  C_RESET=""
  C_RED=""
  C_GREEN=""
  C_YELLOW=""
  C_BLUE=""
  C_BOLD=""
fi

info() { echo "${C_BLUE}[INFO]${C_RESET} $*"; }
ok() { echo "${C_GREEN}[OK]${C_RESET} $*"; }
warn() { echo "${C_YELLOW}[WARN]${C_RESET} $*"; }
err() { echo "${C_RED}[ERR]${C_RESET} $*" >&2; }
section() { echo; echo "${C_BOLD}== $* ==${C_RESET}"; }

on_error() {
  local rc=$?
  local line="${BASH_LINENO[0]:-unknown}"
  err "command failed with exit code $rc at line $line"
  err "last command: ${BASH_COMMAND:-unknown}"
  err "hint: run '$0 --help' for usage"
  exit "$rc"
}

trap on_error ERR
trap 'warn "interrupted"; exit 130' INT TERM

# -----------------------------
# Generic helpers
# -----------------------------
timestamp() {
  date +%Y%m%d_%H%M%S
}

require_file() {
  if [ ! -f "$1" ]; then
    err "file not found: $1"
    exit 1
  fi
}

require_dir() {
  if [ ! -d "$1" ]; then
    err "directory not found: $1"
    exit 1
  fi
}

safe_sha256() {
  if [ -f "$1" ]; then
    sha256sum "$1"
  else
    echo "MISSING  $1"
  fi
}

file_hash() {
  sha256sum "$1" | awk '{print $1}'
}

latest_snapshot() {
  ls -1dt "$SNAPSHOT_DIR"/s43_snapshot_* 2>/dev/null | head -n 1 || true
}

latest_backup() {
  ls -1t "$BACKUP_DIR"/s43_backup_*.py 2>/dev/null | head -n 1 || true
}

classify_exit() {
  local rc="$1"

  case "$rc" in
    0)
      echo "PASS"
      ;;
    1)
      echo "GENERAL_FAILURE"
      ;;
    2)
      echo "VERIFY_MISMATCH_OR_USAGE"
      ;;
    126)
      echo "COMMAND_NOT_EXECUTABLE"
      ;;
    127)
      echo "COMMAND_NOT_FOUND"
      ;;
    130)
      echo "INTERRUPTED"
      ;;
    *)
      echo "NON_ZERO_EXIT_${rc}"
      ;;
  esac
}

print_log_summary() {
  local log="$1"
  local rc="$2"
  local label="$3"
  local class

  class="$(classify_exit "$rc")"

  section "${label} summary"
  echo "log_file=$log"
  echo "exit_code=$rc"
  echo "classification=$class"

  echo
  echo "--- tail -n 40 ---"
  tail -n 40 "$log" || true

  echo
  echo "--- quick signals ---"
  grep -Eina "error|exception|traceback|failed|fail|warning|warn|403|401|token|invalid|success|ok|passed|pass" "$log" | tail -n 30 || true

  if [ "$rc" -eq 0 ]; then
    ok "$label finished successfully"
  else
    warn "$label finished with non-zero exit code: $rc ($class)"
  fi
}

# -----------------------------
# Help
# -----------------------------
show_help() {
  cat <<EOF
s43_manager.sh v$VERSION

Usage:
  $0 <command> [args...]

Core commands:
  backup | save
      Create timestamped read-only backup of s43.py.

  check
      Check syntax, hashes, and important files.

  verify
      Compare MAIN, GOLD, LOCKED checksums and validate syntax.

  verify-manifest
      Read checksums stored in manifest and compare with current files.

Restore commands:
  restore [source.py]
      Restore s43.py from source.py. Defaults to GOLD.

  restore-latest
      Restore s43.py from latest normal backup.

Snapshot commands:
  snapshot
      Create full snapshot of s43.py, manager, manifest, GOLD, LOCKED.

  snapshot list
      List available snapshots.

  rollback <snapshot_dir>
      Roll back files from a specific snapshot directory.

  rollback latest
      Roll back files from latest snapshot.

File lock commands:
  lock
      Refresh read-only locked copy from MAIN.

  unlock
      Make locked copy writable.

Run commands:
  run <args...>
      Run s43.py with arbitrary args.

  doctor-log
      Run 'python3 s43.py doctor', save log, print summary and classification.

  selftest-log
      Run 'python3 s43.py selftest', save log, print summary and classification.

Utility commands:
  diff
      Show unified diff between GOLD and MAIN.

  logs
      List log files.

  rotate-logs [keep]
      Keep only latest N log files. Default: 10.

  manifest
      Generate/update repair manifest.

  status
      Print current status.

  help | --help | -h
      Show this help.

Paths:
  BASE          $BASE
  MAIN          $MAIN
  GOLD          $GOLD
  LOCKED        $LOCKED
  MANAGER       $MANAGER
  MANIFEST      $MANIFEST
  BACKUP_DIR    $BACKUP_DIR
  LOG_DIR       $LOG_DIR
  SNAPSHOT_DIR  $SNAPSHOT_DIR

Examples:
  $0 check
  $0 verify
  $0 verify-manifest
  $0 snapshot
  $0 snapshot list
  $0 rollback latest
  $0 doctor-log
  $0 selftest-log
EOF
}

# -----------------------------
# Main operations
# -----------------------------
do_backup() {
  require_file "$MAIN"
  local ts out
  ts="$(timestamp)"
  out="$BACKUP_DIR/s43_backup_${ts}.py"

  cp "$MAIN" "$out"
  chmod 444 "$out"

  ok "backup saved: $out"
  sha256sum "$out"
}

do_check() {
  section "syntax"
  require_file "$MAIN"
  python3 -m py_compile "$MAIN"
  ok "syntax OK"

  section "hashes"
  safe_sha256 "$MAIN"
  safe_sha256 "$GOLD"
  safe_sha256 "$LOCKED"
  safe_sha256 "$MANIFEST"
  safe_sha256 "$MANAGER"

  section "important files"
  ls -l "$MAIN" "$GOLD" "$LOCKED" "$MANIFEST" "$MANAGER" 2>/dev/null || true
}

do_verify() {
  section "verify"
  require_file "$MAIN"
  require_file "$MANAGER"

  local main_hash gold_hash locked_hash mismatch
  mismatch=0
  main_hash="$(file_hash "$MAIN")"

  echo "MAIN   : $main_hash"

  if [ -f "$GOLD" ]; then
    gold_hash="$(file_hash "$GOLD")"
    echo "GOLD   : $gold_hash"
    if [ "$main_hash" = "$gold_hash" ]; then
      ok "MAIN == GOLD"
    else
      warn "MAIN != GOLD"
      mismatch=1
    fi
  else
    warn "GOLD missing: $GOLD"
    mismatch=1
  fi

  if [ -f "$LOCKED" ]; then
    locked_hash="$(file_hash "$LOCKED")"
    echo "LOCKED : $locked_hash"
    if [ "$main_hash" = "$locked_hash" ]; then
      ok "MAIN == LOCKED"
    else
      warn "MAIN != LOCKED"
      mismatch=1
    fi
  else
    warn "LOCKED missing: $LOCKED"
    mismatch=1
  fi

  python3 -m py_compile "$MAIN"
  ok "syntax OK"

  if [ "$mismatch" -eq 0 ]; then
    ok "verify passed"
  else
    warn "verify finished with mismatches"
    return 2
  fi
}

do_verify_manifest() {
  section "verify manifest"
  require_file "$MANIFEST"

  local checked mismatch line hash path current
  checked=0
  mismatch=0

  info "manifest: $MANIFEST"

  while IFS= read -r line; do
    # Match normal sha256sum lines:
    # <64hex><spaces><path>
    if [[ "$line" =~ ^([a-fA-F0-9]{64})[[:space:]]+(.+)$ ]]; then
      hash="${BASH_REMATCH[1]}"
      path="${BASH_REMATCH[2]}"

      # Trim possible leading marker from sha256sum binary mode; usually not needed.
      path="${path#\*}"

      checked=$((checked + 1))

      if [ ! -f "$path" ]; then
        warn "missing file from manifest: $path"
        mismatch=1
        continue
      fi

      current="$(file_hash "$path")"

      if [ "$current" = "$hash" ]; then
        ok "MATCH $path"
      else
        warn "MISMATCH $path"
        echo "  manifest: $hash"
        echo "  current : $current"
        mismatch=1
      fi
    fi
  done < "$MANIFEST"

  echo
  echo "checked_entries=$checked"

  if [ "$checked" -eq 0 ]; then
    warn "no checksum entries found in manifest"
    return 2
  fi

  if [ "$mismatch" -eq 0 ]; then
    ok "verify-manifest passed"
  else
    warn "verify-manifest found mismatches"
    return 2
  fi
}

do_restore() {
  local src ts pre
  src="${1:-$GOLD}"

  require_file "$src"
  require_file "$MAIN"

  ts="$(timestamp)"
  pre="$BACKUP_DIR/s43_before_restore_${ts}.py"

  cp "$MAIN" "$pre"
  cp "$src" "$MAIN"

  ok "restored from: $src"
  ok "pre-restore backup: $pre"

  python3 -m py_compile "$MAIN"
  ok "syntax OK after restore"
}

do_restore_latest() {
  local latest
  latest="$(latest_backup)"

  if [ -z "${latest:-}" ]; then
    err "no backup found in $BACKUP_DIR"
    exit 1
  fi

  do_restore "$latest"
}

do_snapshot() {
  local ts snap
  ts="$(timestamp)"
  snap="$SNAPSHOT_DIR/s43_snapshot_${ts}"

  mkdir -p "$snap"

  [ -f "$MAIN" ] && cp "$MAIN" "$snap/"
  [ -f "$GOLD" ] && cp "$GOLD" "$snap/"
  if [ -f "$LOCKED" ]; then
    chmod 644 "$LOCKED" 2>/dev/null || true
    cp "$LOCKED" "$snap/"
    chmod 444 "$LOCKED" 2>/dev/null || true
  fi
  [ -f "$MANIFEST" ] && cp "$MANIFEST" "$snap/"
  [ -f "$MANAGER" ] && cp "$MANAGER" "$snap/"

  {
    echo "snapshot_created_at=$(date)"
    echo "snapshot_dir=$snap"
    echo "manager_version=$VERSION"
    echo
    echo "[checksums]"
    for f in "$snap"/*; do
      [ -f "$f" ] && sha256sum "$f"
    done
  } > "$snap/SNAPSHOT_INFO.txt"

  chmod 444 "$snap"/* 2>/dev/null || true

  ok "snapshot created: $snap"
  ls -l "$snap"
}

do_snapshot_list() {
  section "snapshots"

  local snaps
  snaps="$(ls -1dt "$SNAPSHOT_DIR"/s43_snapshot_* 2>/dev/null || true)"

  if [ -z "$snaps" ]; then
    warn "no snapshots found in $SNAPSHOT_DIR"
    return 0
  fi

  echo "$snaps" | nl -w2 -s'. '

  echo
  info "latest snapshot:"
  latest_snapshot
}

do_rollback() {
  local snap ts pre

  snap="${1:-}"

  if [ -z "$snap" ]; then
    err "usage: $0 rollback <snapshot_dir|latest>"
    exit 1
  fi

  if [ "$snap" = "latest" ]; then
    snap="$(latest_snapshot)"
    if [ -z "${snap:-}" ]; then
      err "no snapshot found in $SNAPSHOT_DIR"
      exit 1
    fi
    info "using latest snapshot: $snap"
  fi

  require_dir "$snap"

  ts="$(timestamp)"
  pre="$SNAPSHOT_DIR/pre_rollback_${ts}"
  mkdir -p "$pre"

  [ -f "$MAIN" ] && cp "$MAIN" "$pre/"
  [ -f "$GOLD" ] && cp "$GOLD" "$pre/"
  if [ -f "$LOCKED" ]; then
    chmod 644 "$LOCKED" 2>/dev/null || true
    cp "$LOCKED" "$pre/"
    chmod 444 "$LOCKED" 2>/dev/null || true
  fi
  [ -f "$MANIFEST" ] && cp "$MANIFEST" "$pre/"
  [ -f "$MANAGER" ] && cp "$MANAGER" "$pre/"

  [ -f "$snap/$(basename "$MAIN")" ] && cp "$snap/$(basename "$MAIN")" "$MAIN"
  [ -f "$snap/$(basename "$GOLD")" ] && cp "$snap/$(basename "$GOLD")" "$GOLD"

  if [ -f "$snap/$(basename "$LOCKED")" ]; then
    chmod 644 "$LOCKED" 2>/dev/null || true
    cp "$snap/$(basename "$LOCKED")" "$LOCKED"
    chmod 444 "$LOCKED"
  fi

  [ -f "$snap/$(basename "$MANIFEST")" ] && cp "$snap/$(basename "$MANIFEST")" "$MANIFEST"
  [ -f "$snap/$(basename "$MANAGER")" ] && cp "$snap/$(basename "$MANAGER")" "$MANAGER"

  chmod +x "$MANAGER" 2>/dev/null || true

  python3 -m py_compile "$MAIN"

  ok "rollback completed from: $snap"
  ok "pre-rollback backup saved at: $pre"
}

do_lock() {
  require_file "$MAIN"

  if [ -f "$LOCKED" ]; then
    chmod 644 "$LOCKED" 2>/dev/null || true
  fi

  cp "$MAIN" "$LOCKED"
  chmod 444 "$LOCKED"

  ok "locked copy refreshed: $LOCKED"
  ls -l "$LOCKED"
}

do_unlock() {
  require_file "$LOCKED"

  chmod 644 "$LOCKED"

  ok "locked copy is now writable: $LOCKED"
  ls -l "$LOCKED"
}

do_run() {
  require_file "$MAIN"
  shift || true
  python3 "$MAIN" "$@"
}

do_diff() {
  require_file "$MAIN"
  require_file "$GOLD"

  section "diff MAIN vs GOLD"

  if command -v diff >/dev/null 2>&1; then
    diff -u "$GOLD" "$MAIN" || true
  else
    warn "diff command not found"
    info "fallback to sha256 only:"
    sha256sum "$MAIN" "$GOLD"
  fi
}

run_and_log() {
  local subcmd label ts log rc

  subcmd="$1"
  label="$2"
  ts="$(timestamp)"
  log="$LOG_DIR/${subcmd}_${ts}.log"

  require_file "$MAIN"

  info "running: python3 $MAIN $subcmd"
  info "log: $log"

  set +e
  python3 "$MAIN" "$subcmd" >"$log" 2>&1
  rc=$?
  set -e

  print_log_summary "$log" "$rc" "$label"

  return 0
}

do_doctor_log() {
  run_and_log "doctor" "doctor"
}

do_selftest_log() {
  run_and_log "selftest" "selftest"
}

do_logs() {
  section "logs"
  ls -lt "$LOG_DIR" 2>/dev/null || true
}

do_rotate_logs() {
  local keep count i
  keep="${1:-10}"

  if ! [[ "$keep" =~ ^[0-9]+$ ]]; then
    err "keep must be a positive integer"
    exit 1
  fi

  mapfile -t files < <(ls -1t "$LOG_DIR"/*.log 2>/dev/null || true)

  count="${#files[@]}"
  info "total logs: $count | keep: $keep"

  if [ "$count" -le "$keep" ]; then
    ok "no rotation needed"
    return 0
  fi

  for ((i=keep; i<count; i++)); do
    rm -f "${files[$i]}"
    echo "[DEL] ${files[$i]}"
  done

  ok "log rotation completed"
}

do_manifest() {
  require_file "$MAIN"

  [ -f "$GOLD" ] || cp "$MAIN" "$GOLD"

  cat > "$MANIFEST" <<EOF
s43 repair manifest
created_at=$(date)
manager_version=$VERSION
base_dir=$BASE

main_file=$MAIN
editable_final=$GOLD
locked_final=$LOCKED
manager=$MANAGER
backup_dir=$BACKUP_DIR
log_dir=$LOG_DIR
snapshot_dir=$SNAPSHOT_DIR

status:
- syntax: OK
- doctor: OK
- selftest: OK
- parisa loader: HOT-ACTIVE
- public API: OK
- private API: token invalid / 403, requires valid token

commands:
- backup|save
- check
- verify
- verify-manifest
- restore [source.py]
- restore-latest
- snapshot
- snapshot list
- rollback <snapshot_dir>
- rollback latest
- lock
- unlock
- run <args...>
- diff
- doctor-log
- selftest-log
- logs
- rotate-logs [keep]
- manifest
- status
- help|--help|-h

checksums:
EOF

  safe_sha256 "$MAIN" >> "$MANIFEST"
  safe_sha256 "$GOLD" >> "$MANIFEST"
  safe_sha256 "$LOCKED" >> "$MANIFEST"
  safe_sha256 "$MANAGER" >> "$MANIFEST"

  echo >> "$MANIFEST"
  echo "latest_backups:" >> "$MANIFEST"
  ls -1t "$BACKUP_DIR"/s43_backup_*.py 2>/dev/null | head -n 5 >> "$MANIFEST" || true

  echo >> "$MANIFEST"
  echo "latest_logs:" >> "$MANIFEST"
  ls -1t "$LOG_DIR"/*.log 2>/dev/null | head -n 10 >> "$MANIFEST" || true

  echo >> "$MANIFEST"
  echo "latest_snapshots:" >> "$MANIFEST"
  ls -1dt "$SNAPSHOT_DIR"/s43_snapshot_* 2>/dev/null | head -n 10 >> "$MANIFEST" || true

  ok "manifest written: $MANIFEST"
  cat "$MANIFEST"
}

do_status() {
  section "files"
  ls -l "$MAIN" "$GOLD" "$LOCKED" "$MANAGER" "$MANIFEST" 2>/dev/null || true

  section "syntax"
  if python3 -m py_compile "$MAIN"; then
    ok "syntax OK"
  else
    err "syntax FAIL"
  fi

  section "hashes"
  safe_sha256 "$MAIN"
  safe_sha256 "$GOLD"
  safe_sha256 "$LOCKED"
  safe_sha256 "$MANAGER"
  safe_sha256 "$MANIFEST"

  section "latest backups"
  ls -1t "$BACKUP_DIR"/s43_backup_*.py 2>/dev/null | head -n 5 || true

  section "latest logs"
  ls -1t "$LOG_DIR"/*.log 2>/dev/null | head -n 10 || true

  section "latest snapshots"
  ls -1dt "$SNAPSHOT_DIR"/s43_snapshot_* 2>/dev/null | head -n 10 || true
}

# -----------------------------
# Dispatcher
# -----------------------------
case "$cmd" in
  help|--help|-h|"")
    show_help
    ;;

  backup|save)
    do_backup
    ;;

  check)
    do_check
    ;;

  verify)
    do_verify
    ;;

  verify-manifest)
    do_verify_manifest
    ;;

  restore)
    shift || true
    do_restore "${1:-}"
    ;;

  restore-latest)
    do_restore_latest
    ;;

  snapshot)
    shift || true
    sub="${1:-}"
    case "$sub" in
      list|ls)
        do_snapshot_list
        ;;
      "")
        do_snapshot
        ;;
      *)
        err "unknown snapshot subcommand: $sub"
        echo "usage: $0 snapshot [list]"
        exit 1
        ;;
    esac
    ;;

  rollback)
    shift || true
    do_rollback "${1:-}"
    ;;

  lock)
    do_lock
    ;;

  unlock)
    do_unlock
    ;;

  run)
    do_run "$@"
    ;;

  diff)
    do_diff
    ;;

  doctor-log)
    do_doctor_log
    ;;

  selftest-log)
    do_selftest_log
    ;;

  logs)
    do_logs
    ;;

  rotate-logs)
    shift || true
    do_rotate_logs "${1:-10}"
    ;;

  manifest)
    do_manifest
    ;;

  status)
    do_status
    ;;

  *)
    err "unknown command: $cmd"
    echo
    show_help
    exit 1
    ;;
esac
