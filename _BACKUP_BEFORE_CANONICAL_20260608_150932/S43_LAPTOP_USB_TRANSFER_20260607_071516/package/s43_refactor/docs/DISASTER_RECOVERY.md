# S43 Disaster Recovery Guide

This document describes how to recover the S43 project from common failure scenarios.

## Scenario 1: Active `s43.py` Is Corrupted

List available release backups:

bash
ls -lt release_backups/s43.py.final_*

Restore the latest release:

bash
latest_release="$(ls -t release_backups/s43.py.final_* | head -n 1)"
cp "$latest_release" s43.py
python -m py_compile s43.py

Verify:

bash
cmp -s s43.py "$latest_release" && echo "OK: restored file matches release backup"

## Scenario 2: Project Artifacts Need Recovery

Go to packed archive directory:

bash
cd archive_packed_backup

List available packs:

bash
ls -lh S43_ARCHIVE_PACK_*.tar.gz

Verify archive listing:

bash
tar -tzf S43_ARCHIVE_PACK_YYYYMMDD_HHMMSS.tar.gz >/dev/null && echo "OK: archive is readable"

Extract:

bash
tar -xzf S43_ARCHIVE_PACK_YYYYMMDD_HHMMSS.tar.gz

## Scenario 3: Runtime Failure

Stop the process with `CTRL+C`, then run:

bash
python -m py_compile s43.py
python s43.py

Check logs:

bash
ls -lt logs/

## Backup Priority

Primary production source:

text
s43.py

Primary release backups:

text
release_backups/

Historical packed archives:

text
archive_packed_backup/

Recommended external backup target:

text
external storage or cloud backup
