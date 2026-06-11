#!/usr/bin/env bash
set -e
cd ~/s43_refactor

LATEST_SNAP="$(ls -1t snap_before_patch_*.py 2>/dev/null | head -n 1)"

if python -m py_compile s43.py; then
  echo "COMPILE_OK"
else
  echo "COMPILE_FAIL"
  if [ -n "$LATEST_SNAP" ]; then
    cp -av "$LATEST_SNAP" s43.py
    echo "RESTORED_FROM: $LATEST_SNAP"
  else
    echo "NO_SNAPSHOT_FOUND"
    exit 1
  fi
fi
