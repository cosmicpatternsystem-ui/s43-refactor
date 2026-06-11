# S43 Backup Validation Report

## Generated
- Timestamp: 20260603-140308
- Project Dir: /data/data/com.termux/files/home/s43_refactor

## Policy
- This report was generated without modifying `s43.py`.
- Final aliases are created with `cp -p`.
- Existing aliases are not overwritten.
- Python syntax validation is performed with `python -m py_compile`.

## Active File
- File: `s43.py`
- Lines: 29958
- Size bytes: 2620287
- SHA256: `c5b0b5cf1e20dc253d91867d833cf5a02f53324b07f491f4acb891caad45b334`

## Final Naming

| Role | Final Name |
|---|---|
| Active main file | `s43.py` |
| Stable baseline alias | `s43.py.STABLE_BASELINE_CONFIRMED` |
| Restore-confirmed alias | `s43.py.RESTORE_CONFIRMED` |
| Broken forensic reference | `s43.py.BROKEN_REFERENCE` |

## Source Mapping

| Role | Source |
|---|---|
| Stable source | `s43.py.bak_guard_phase1c_1780471331` |
| Restore-confirmed source | `s43.py.baseline_restored_phase1c_dryrun_ok` |
| Broken reference source | `s43.py.syntax_broken_guard_injected_backup` |

## Hash Comparison

| Check | Result |
|---|---|
| Active vs Stable Source | YES |
| Active vs Restore Source | YES |
| Stable Source vs Stable Alias | YES |

## Manifest
Detailed manifest file:

`BACKUP_MANIFEST_20260603-140308.tsv`

## Recommended Freeze Decision

If:
- `s43.py` has `PY_COMPILE=PASS`
- `s43.py.STABLE_BASELINE_CONFIRMED` has `PY_COMPILE=PASS`
- `s43.py.RESTORE_CONFIRMED` has `PY_COMPILE=PASS`
- Active hash matches at least one confirmed stable/restored backup

Then the project backup state is considered:

`VALIDATED / NAMED / FREEZE-SAFE`

