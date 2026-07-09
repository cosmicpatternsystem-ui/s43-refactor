#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python -m py_compile asoctl.py
python -m pytest tests/test_p33_validator.py tests/test_p34_ledger.py tests/test_p35_commercial_positioning.py -q
