#!/usr/bin/env bash
set -e
cd ~/s43_refactor
SNAP="snap_before_patch_$(date +%Y%m%d_%H%M%S).py"
cp -av s43.py "$SNAP"
python -m py_compile s43.py
echo "SAFE: $SNAP"
