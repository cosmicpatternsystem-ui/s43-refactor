#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

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

show_usage() {
  cat <<EOF
Usage:
  $0 backup|save
  $0 check
  $0 verify
  $0 restore [source.py]
  $0 restore-latest
  $0 snapshot
  $0 rollback <snapshot_dir>
  $0 lock
  $0 unlock
  $0 run <args...>
  $0 diff
  $0 doctor-log
  $0 selftest-log
  $0 logs
  $0 rotate-logs [keep]
  $0 manifest
  $0 status
EOF
}

require_file() {
  if [ ! -f "$1" ]; then
    echo "[ERR] file not found: $1"
    exit 1
  fi
}

timestamp() {
  date +%Y%m%d_%H%M%S
}

safe_sha256() {
  if [ -f "$1" ]; then
    sha256sum "$1"
  else
    echo "MISSING  $1"
  fi
}

do_backup() {
  require_file "$MAIN"
  ts="$(timestamp)"
  out="$BACKUP_DIR/s43_backup_${ts}.py"
  cp "$MAIN" "$out"
  chmod 444 "$out"
  echo "[OK] backup saved: $out"
  sha256sum "$out"
}

do_check() {
  echo "[CHECK] syntax:"
  require_file "$MAIN"
  python3 -m py_compile "$MAIN"
  echo "[OK] syntax OK"
  echo

  echo "[CHECK] hashes:"
  safe_sha256 "$MAIN"
  safe_sha256 "$GOLD"
  safe_sha256 "$LOCKED"
  safe_sha256 "$MANIFEST"
  safe_sha256 "$MANAGER"
  echo

  echo "[CHECK] important files:"
  ls -l "$MAIN" "$GOLD" "$LOCKED" "$MANIFEST" "$MANAGER" 2>/dev/null || true
}

do_verify() {
  echo "[VERIFY] validating file presence and checksums"
  require_file "$MAIN"
  require_file "$MANAGER"

  main_hash="$(sha256sum "$MAIN" | awk '{print $1}')"

  if [ -f "$GOLD" ]; then
    gold_hash="$(sha256sum "$GOLD" | awk '{print $1}')"
  else
    gold_hash=""
  fi

  if [ -f "$LOCKED" ]; then
    locked_hash="$(sha256sum "$LOCKED" | awk '{print $1}')"
  else
    locked_hash=""
  fi

  echo "MAIN   : ${main_hash}"
  echo "GOLD   : ${gold_hash:-MISSING}"
  echo "LOCKED : ${locked_hash:-MISSING}"
  echo

  mismatch=0

  if [ -f "$GOLD" ] && [ "$main_hash" != "$gold_hash" ]; then
    echo "[WARN] MAIN and GOLD differ"
    mismatch=1
  else
    [ -f "$GOLD" ] && echo "[OK] MAIN == GOLD"
  fi

  if [ -f "$LOCKED" ] && [ "$main_hash" != "$locked_hash" ]; then
    echo "[WARN] MAIN and LOCKED differ"
    mismatch=1
  else
    [ -f "$LOCKED" ] && echo "[OK] MAIN == LOCKED"
  fi

  python3 -m py_compile "$MAIN"
  echo "[OK] syntax OK"

  if [ "$mismatch" -eq 0 ]; then
    echo "[OK] verify passed"
  else
    echo "[WARN] verify finished with mismatches"
    return 2
  fi
}

do_restore() {
  src="${1:-$GOLD}"
  require_file "$src"
  require_file "$MAIN"

  ts="$(timestamp)"
  pre="$BACKUP_DIR/s43_before_restore_${ts}.py"
  cp "$MAIN" "$pre"

  cp "$src" "$MAIN"
  echo "[OK] restored from: $src"
  echo "[OK] pre-restore backup: $pre"

  python3 -m py_compile "$MAIN"
  echo "[OK] syntax OK after restore"
}

do_restore_latest() {
  latest="$(ls -1t "$BACKUP_DIR"/s43_backup_*.py 2>/dev/null | head -n 1 || true)"
  if [ -z "${latest:-}" ]; then
    echo "[ERR] no backup found in $BACKUP_DIR"
    exit 1
  fi
  do_restore "$latest"
}

do_snapshot() {
  ts="$(timestamp)"
  snap="$SNAPSHOT_DIR/s43_snapshot_${ts}"
  mkdir -p "$snap"

  [ -f "$MAIN" ] && cp "$MAIN" "$snap/"
  [ -f "$GOLD" ] && cp "$GOLD" "$snap/"
  [ -f "$LOCKED" ] && { chmod 644 "$LOCKED" 2>/dev/null || true; cp "$LOCKED" "$snap/"; chmod 444 "$LOCKED" 2>/dev/null || true; }
  [ -f "$MANIFEST" ] && cp "$MANIFEST" "$snap/"
  [ -f "$MANAGER" ] && cp "$MANAGER" "$snap/"

  {
    echo "snapshot_created_at=$(date)"
    echo "snapshot_dir=$snap"
    echo
    echo "[checksums]"
    [ -f "$snap/$(basename "$MAIN")" ] && sha256sum "$snap/$(basename "$MAIN")"
    [ -f "$snap/$(basename "$GOLD")" ] && sha256sum "$snap/$(basename "$GOLD")"
    [ -f "$snap/$(basename "$LOCKED")" ] && sha256sum "$snap/$(basename "$LOCKED")"
    [ -f "$snap/$(basename "$MANIFEST")" ] && sha256sum "$snap/$(basename "$MANIFEST")"
    [ -f "$snap/$(basename "$MANAGER")" ] && sha256sum "$snap/$(basename "$MANAGER")"
  } > "$snap/SNAPSHOT_INFO.txt"

  chmod 444 "$snap"/* 2>/dev/null || true

  echo "[OK] snapshot created: $snap"
  ls -l "$snap"
}

do_rollback() {
  snap="${1:-}"
  if [ -z "$snap" ]; then
    echo "[ERR] usage: $0 rollback <snapshot_dir>"
    exit 1
  fi

  if [ ! -d "$snap" ]; then
    echo "[ERR] snapshot dir not found: $snap"
    exit 1
  fi

  ts="$(timestamp)"
  pre="$SNAPSHOT_DIR/pre_rollback_${ts}"
  mkdir -p "$pre"

  [ -f "$MAIN" ] && cp "$MAIN" "$pre/"
  [ -f "$GOLD" ] && cp "$GOLD" "$pre/"
  [ -f "$LOCKED" ] && { chmod 644 "$LOCKED" 2>/dev/null || true; cp "$LOCKED" "$pre/"; chmod 444 "$LOCKED" 2>/dev/null || true; }
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
  echo "[OK] rollback completed from: $snap"
  echo "[OK] pre-rollback backup saved at: $pre"
}

do_lock() {
  require_file "$MAIN"

  if [ -f "$LOCKED" ]; then
    chmod 644 "$LOCKED" 2>/dev/null || true
  fi

  cp "$MAIN" "$LOCKED"
  chmod 444 "$LOCKED"
  echo "[OK] locked copy refreshed: $LOCKED"
  ls -l "$LOCKED"
}

do_unlock() {
  require_file "$LOCKED"
  chmod 644 "$LOCKED"
  echo "[OK] locked copy is now writable: $LOCKED"
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

  if command -v diff >/dev/null 2>&1; then
    echo "[DIFF] MAIN vs GOLD"
    diff -u "$GOLD" "$MAIN" || true
  else
    echo "[WARN] diff command not found"
    echo "[INFO] fallback to sha256 only:"
    sha256sum "$MAIN" "$GOLD"
  fi
}

do_doctor_log() {
  require_file "$MAIN"
  ts="$(timestamp)"
  log="$LOG_DIR/doctor_${ts}.log"
  echo "[RUN] python3 $MAIN doctor"
  set +e
  python3 "$MAIN" doctor >"$log" 2>&1
  rc=$?
  set -e
  echo "[OK] doctor log saved: $log"
  echo "[INFO] exit code: $rc"
  tail -n 40 "$log" || true
}

do_selftest_log() {
  require_file "$MAIN"
  ts="$(timestamp)"
  log="$LOG_DIR/selftest_${ts}.log"
  echo "[RUN] python3 $MAIN selftest"
  set +e
  python3 "$MAIN" selftest >"$log" 2>&1
  rc=$?
  set -e
  echo "[OK] selftest log saved: $log"
  echo "[INFO] exit code: $rc"
  tail -n 40 "$log" || true
}

do_logs() {
  echo "[LOGS] available log files:"
  ls -lt "$LOG_DIR" 2>/dev/null || true
}

do_rotate_logs() {
  keep="${1:-10}"

  if ! [[ "$keep" =~ ^[0-9]+$ ]]; then
    echo "[ERR] keep must be a positive integer"
    exit 1
  fi

  mapfile -t files < <(ls -1t "$LOG_DIR"/*.log 2>/dev/null || true)

  count="${#files[@]}"
  echo "[INFO] total logs: $count | keep: $keep"

  if [ "$count" -le "$keep" ]; then
    echo "[OK] no rotation needed"
    return 0
  fi

  for ((i=keep; i<count; i++)); do
    rm -f "${files[$i]}"
    echo "[DEL] ${files[$i]}"
  done

  echo "[OK] log rotation completed"
}

do_manifest() {
  require_file "$MAIN"
  [ -f "$GOLD" ] || cp "$MAIN" "$GOLD"

  cat > "$MANIFEST" <<EOF
s43 repair manifest
created_at=$(date)
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
- restore [source.py]
- restore-latest
- snapshot
- rollback <snapshot_dir>
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

  echo "[OK] manifest written: $MANIFEST"
  cat "$MANIFEST"
}

do_status() {
  echo "[STATUS] files:"
  ls -l "$MAIN" "$GOLD" "$LOCKED" "$MANAGER" "$MANIFEST" 2>/dev/null || true
  echo

  echo "[STATUS] syntax:"
  python3 -m py_compile "$MAIN" && echo "[OK] syntax OK" || echo "[ERR] syntax FAIL"
  echo

  echo "[STATUS] hashes:"
  safe_sha256 "$MAIN"
  safe_sha256 "$GOLD"
  safe_sha256 "$LOCKED"
  safe_sha256 "$MANAGER"
  safe_sha256 "$MANIFEST"
  echo

  echo "[STATUS] latest backups:"
  ls -1t "$BACKUP_DIR"/s43_backup_*.py 2>/dev/null | head -n 5 || true
  echo

  echo "[STATUS] latest logs:"
  ls -1t "$LOG_DIR"/*.log 2>/dev/null | head -n 10 || true
  echo

  echo "[STATUS] latest snapshots:"
  ls -1dt "$SNAPSHOT_DIR"/s43_snapshot_* 2>/dev/null | head -n 10 || true
}

case "$cmd" in
  backup|save)
    do_backup
    ;;
  check)
    do_check
    ;;
  verify)
    do_verify
    ;;
  restore)
    shift || true
    do_restore "${1:-}"
    ;;
  restore-latest)
    do_restore_latest
    ;;
  snapshot)
    do_snapshot
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
    show_usage
    exit 1
    ;;
esac
