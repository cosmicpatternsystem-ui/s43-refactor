#!/data/data/com.termux/files/usr/bin/bash
set -e

BASE="$HOME/s43_refactor"
MAIN="$BASE/s43.py"
GOLD="$BASE/s43_final_repaired.py"
LOCKED="$BASE/s43_final_repaired_locked.py"
BACKUP_DIR="$BASE/backups"

mkdir -p "$BACKUP_DIR"

cmd="${1:-}"

case "$cmd" in
  backup|save)
    ts="$(date +%Y%m%d_%H%M%S)"
    out="$BACKUP_DIR/s43_backup_${ts}.py"
    cp "$MAIN" "$out"
    chmod 444 "$out"
    echo "[OK] backup saved: $out"
    sha256sum "$out"
    ;;

  check)
    echo "[CHECK] syntax:"
    python3 -m py_compile "$MAIN"
    echo "[OK] syntax OK"
    echo
    echo "[CHECK] hashes:"
    sha256sum "$MAIN" "$GOLD" "$LOCKED" 2>/dev/null || true
    echo
    echo "[CHECK] important files:"
    ls -l "$MAIN" "$GOLD" "$LOCKED" 2>/dev/null || true
    ;;

  restore)
    src="${2:-$GOLD}"
    if [ ! -f "$src" ]; then
      echo "[ERR] restore source not found: $src"
      exit 1
    fi
    cp "$MAIN" "$BACKUP_DIR/s43_before_restore_$(date +%Y%m%d_%H%M%S).py"
    cp "$src" "$MAIN"
    echo "[OK] restored from: $src"
    python3 -m py_compile "$MAIN"
    echo "[OK] syntax OK after restore"
    ;;

  lock)
    if [ -f "$LOCKED" ]; then
      chmod 644 "$LOCKED" 2>/dev/null || true
    fi
    cp "$MAIN" "$LOCKED"
    chmod 444 "$LOCKED"
    echo "[OK] locked copy refreshed: $LOCKED"
    ls -l "$LOCKED"
    ;;

  run)
    shift
    python3 "$MAIN" "$@"
    ;;

  *)
    echo "Usage:"
    echo "  $0 backup|save"
    echo "  $0 check"
    echo "  $0 restore [source.py]"
    echo "  $0 lock"
    echo "  $0 run <args...>"
    exit 1
    ;;
esac
