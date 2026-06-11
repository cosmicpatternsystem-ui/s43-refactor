# S43 Runbook

Operational guide for running and verifying the S43 system.

## Requirements

Recommended Python version:

bash
python --version

Python 3.10+ is recommended.

## Start

Run:

bash
python s43.py

## Compile Check

Before and after changes, run:

bash
python -m py_compile s43.py

Expected result:

No output and exit code `0`.

## Release Integrity Check

Find the latest release backup:

bash
ls -t release_backups/s43.py.final_* | head -n 1

Compare active file with latest release backup:

bash
latest_release="$(ls -t release_backups/s43.py.final_* | head -n 1)"
cmp -s s43.py "$latest_release" && echo "OK: active s43.py matches latest release backup" || echo "WARNING: active s43.py differs from latest release backup"

## Logs

Runtime logs should be stored in:

text
logs/

## Emergency Stop

Press:

text
CTRL+C

## Basic Health Check

Confirm:

- `s43.py` compiles cleanly
- runtime starts without immediate exception
- logs are updating if logging is enabled
- latest release backup exists
