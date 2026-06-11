# Backup Restore Verification

## Status

BACKUP_RESTORE_VERIFIED

## Target

- file: s43.py
- current sha256: 8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786
- restored sha256: 8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786
- baseline sha256: 8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786

## Backup Archive

- tar: .terminal_backups/s43_terminal_backup_snapshot_20260607_061300.tar.gz
- sha file: .terminal_backups/s43_terminal_backup_snapshot_20260607_061300.tar.gz.sha256
- sha256: d381f7c1eecfd71abc9c95731bb84c5aeb30fe2deaf7e018e302af030972f2a1
- manifest: .terminal_backups/s43_terminal_backup_snapshot_20260607_061300.manifest.sha256
- backup root: s43_terminal_backup_snapshot_20260607_061300

## Verification

- backup checksum: ok
- restore extraction: ok
- restored manifest hashes: ok
- restored s43.py hash: ok
- release evidence bundle: ok
- validator exit code: 0
- py_compile: ok

## Chain Status

- BACKUP_RESTORE_VERIFIED
- TERMINAL_BACKUP_SNAPSHOT_CREATED
- TERMINAL_CLOSURE_RECORDED
- ARCHIVE_READY_CERTIFIED
- FINAL_MANIFEST_LOCKED
- FINAL_CHAIN_SEALED
- S43_UNCHANGED
- TRIWALLET_PROFILE_LAYER_PRESERVED

## Runtime Impact

No runtime modification was made to s43.py.
