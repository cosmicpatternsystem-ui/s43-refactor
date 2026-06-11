# Offsite Copy Checklist

Status: CHECKLIST_READY
Decision: OFFSITE_COPY_CHECKLIST_AND_RECEIPT

This checklist is documentation-only. It does not perform network transfer or storage replication.

## Source Artifacts To Copy

1. Backup archive
   - path: .terminal_backups/s43_terminal_backup_snapshot_20260607_061300.tar.gz
   - sha256: d381f7c1eecfd71abc9c95731bb84c5aeb30fe2deaf7e018e302af030972f2a1

2. Backup archive sha256 sidecar
   - path: .terminal_backups/s43_terminal_backup_snapshot_20260607_061300.tar.gz.sha256

3. Backup manifest
   - path: .terminal_backups/s43_terminal_backup_snapshot_20260607_061300.manifest.sha256

4. Release evidence bundle
   - path: .release_evidence/s43_final_release_evidence_bundle_20260606_215239.tar.gz
   - sha256: a1a37e3ed2a440c8c517af02f2bdcc29f87738959792993c35d3d6d03aac39f0

## Pre-Copy Verification

- [ ] Verify source backup archive exists
- [ ] Verify source backup archive sha256 matches d381f7c1eecfd71abc9c95731bb84c5aeb30fe2deaf7e018e302af030972f2a1
- [ ] Verify source backup sha256 sidecar exists
- [ ] Verify source backup manifest exists
- [ ] Verify release evidence bundle exists
- [ ] Verify release evidence bundle sha256 matches a1a37e3ed2a440c8c517af02f2bdcc29f87738959792993c35d3d6d03aac39f0
- [ ] Verify OFFSITE_REPLICATION_READY seal exists
- [ ] Verify s43.py reference hash remains 8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786

## Copy Targets

- [ ] External removable media
- [ ] Secondary offline device
- [ ] Cold archive directory
- [ ] Other approved offline destination

## Copy Procedure

- [ ] Mount or attach destination media
- [ ] Create destination directory for sealed archive
- [ ] Copy backup archive
- [ ] Copy backup sha256 sidecar
- [ ] Copy backup manifest
- [ ] Copy release evidence bundle
- [ ] Safely flush and unmount destination media if applicable

## Post-Copy Verification

- [ ] Recompute sha256 for copied backup archive at destination
- [ ] Confirm copied backup archive sha256 matches d381f7c1eecfd71abc9c95731bb84c5aeb30fe2deaf7e018e302af030972f2a1
- [ ] Recompute sha256 for copied release evidence bundle at destination
- [ ] Confirm copied release evidence bundle sha256 matches a1a37e3ed2a440c8c517af02f2bdcc29f87738959792993c35d3d6d03aac39f0
- [ ] Record destination label, location class, and operator initials
- [ ] Complete offsite copy receipt

## Runtime Safety

- runtime impact: none
- s43.py modified: no
- network transfer required: no
