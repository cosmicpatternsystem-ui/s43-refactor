# S43 Backup Validation Report V2

## Generated
- Timestamp: 20260603-140739
- Project Dir: /data/data/com.termux/files/home/s43_refactor
- Temp Compile Dir: .s43_tmp_compile_20260603-140739

## Policy
- This report was generated without modifying `s43.py`.
- Final aliases are created with `cp -p`.
- Existing aliases are not overwritten.
- Python syntax validation is performed with `python -m py_compile`.
- Termux-safe local temp directory is used instead of `/tmp`.

## Expected Stable Fingerprint
- Lines: 29958
- Size bytes: 2620287
- SHA256: `c5b0b5cf1e20dc253d91867d833cf5a02f53324b07f491f4acb891caad45b334`

## Active File
- File: `s43.py`
- Lines: 29958
- Size bytes: 2620287
- SHA256: `c5b0b5cf1e20dc253d91867d833cf5a02f53324b07f491f4acb891caad45b334`
- PY_COMPILE: PASS
- Stable Fingerprint Match: YES

## Final Naming

| Role | Final Name |
|---|---|
| Active main file | `s43.py` |
| Stable baseline alias | `s43.py.STABLE_BASELINE_CONFIRMED` |
| Restore-confirmed alias | `s43.py.RESTORE_CONFIRMED` |
| Broken forensic reference | `s43.py.BROKEN_REFERENCE` |

## Hash Comparison

| Check | Result |
|---|---|
| Active vs Stable Source | YES |
| Active vs Restore Source | YES |
| Stable Source vs Stable Alias | YES |
| Active Stable Fingerprint | YES |

## Manifest
Detailed manifest file:

`BACKUP_MANIFEST_V2_20260603-140739.tsv`

## Decision

If:
- Active PY_COMPILE is `PASS`
- Active Stable Fingerprint is `YES`
- Active vs Stable Source is `YES`
- Active vs Restore Source is `YES`

Then status is:

`VALIDATED / NAMED / FREEZE-SAFE / TERMUX-COMPATIBLE`

