#!/usr/bin/env bash
set -eu

PROJECT_DIR="${HOME}/s43_refactor"
cd "$PROJECT_DIR"

BASELINE_S43_SHA256="8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786"
RELEASE_BUNDLE=".release_evidence/s43_final_release_evidence_bundle_20260606_215239.tar.gz"
RELEASE_BUNDLE_SHA256="a1a37e3ed2a440c8c517af02f2bdcc29f87738959792993c35d3d6d03aac39f0"

TS="$(date +%Y%m%d_%H%M%S)"
AUDIT_DIR=".patch_audit/s43_offsite_copy_checklist_receipt_${TS}"
mkdir -p "$AUDIT_DIR"

LOG="$AUDIT_DIR/run.log"
STATUS="$AUDIT_DIR/status.txt"

log() {
  printf '%s\n' "$*" | tee -a "$LOG"
}

fail() {
  log "PATCH_FAIL: $*"
  exit 1
}

sha256_file() {
  sha256sum "$1" | awk '{print $1}'
}

require_file() {
  [ -f "$1" ] || fail "missing required file: $1"
}

require_dir() {
  [ -d "$1" ] || fail "missing required directory: $1"
}

ascii_check() {
  f="$1"
  python - "$f" <<'PY'
import sys
p = sys.argv[1]
data = open(p, "rb").read()
bad = [b for b in data if b not in (9, 10, 13) and not (32 <= b <= 126)]
if bad:
    print("NON_ASCII", p)
    raise SystemExit(1)
print("ASCII_OK", p)
PY
}

log "PATCH_START s43_offsite_copy_checklist_receipt"
log "PROJECT_DIR=$PROJECT_DIR"
log "AUDIT_DIR=$AUDIT_DIR"

require_file "s43.py"
S43_BEFORE="$(sha256_file s43.py)"
log "s43_before_sha256: $S43_BEFORE"
[ "$S43_BEFORE" = "$BASELINE_S43_SHA256" ] || fail "s43.py baseline hash mismatch before patch"

python -m py_compile s43.py >>"$LOG" 2>&1 || fail "py_compile failed for s43.py"

REQUIRED_FILES="
docs/OFFSITE_COLD_ARCHIVE_REPLICATION.md
.provenance/decisions/ADR-0005-offsite-cold-archive-replication.md
.provenance/final_seal/FINAL-SEAL-0004-OFFSITE-REPLICATION-READY.txt
docs/BACKUP_RESTORE_VERIFICATION.md
.provenance/final_seal/FINAL-SEAL-0004-BACKUP-RESTORE-VERIFICATION.txt
docs/TERMINAL_BACKUP_SNAPSHOT.md
.provenance/final_seal/FINAL-SEAL-0004-BACKUP-SNAPSHOT.txt
docs/TERMINAL_CLOSURE_RECORD.md
.provenance/final_seal/FINAL-SEAL-0004-TERMINAL-CLOSURE.txt
docs/ARCHIVE_READINESS_CERTIFICATE.md
.provenance/final_seal/FINAL-SEAL-0004-ARCHIVE-READINESS.txt
docs/FINAL_MANIFEST_LOCK.md
.provenance/final_seal/FINAL-SEAL-0004-MANIFEST-LOCK.txt
docs/FINAL_CHAIN_SEAL.md
.provenance/final_seal/FINAL-SEAL-0004.txt
"

for f in $REQUIRED_FILES; do
  require_file "$f"
  log "REQUIRED_OK $f"
done

require_file "$RELEASE_BUNDLE"
ACTUAL_RELEASE_SHA="$(sha256_file "$RELEASE_BUNDLE")"
log "release_bundle: $RELEASE_BUNDLE"
log "release_bundle_sha256_actual: $ACTUAL_RELEASE_SHA"
log "release_bundle_sha256_expected: $RELEASE_BUNDLE_SHA256"
[ "$ACTUAL_RELEASE_SHA" = "$RELEASE_BUNDLE_SHA256" ] || fail "release evidence bundle sha256 mismatch"

require_dir ".terminal_backups"
LATEST_BACKUP="$(ls -1t .terminal_backups/s43_terminal_backup_snapshot_*.tar.gz 2>/dev/null | head -n 1 || true)"
[ -n "$LATEST_BACKUP" ] || fail "no terminal backup snapshot found"

BACKUP_SHA_FILE="${LATEST_BACKUP}.sha256"
BACKUP_MANIFEST_FILE="${LATEST_BACKUP%.tar.gz}.manifest.sha256"

require_file "$BACKUP_SHA_FILE"
require_file "$BACKUP_MANIFEST_FILE"

EXPECTED_BACKUP_SHA="$(awk '{print $1}' "$BACKUP_SHA_FILE")"
ACTUAL_BACKUP_SHA="$(sha256_file "$LATEST_BACKUP")"

log "latest_backup: $LATEST_BACKUP"
log "latest_backup_sha256_actual: $ACTUAL_BACKUP_SHA"
log "latest_backup_sha256_expected: $EXPECTED_BACKUP_SHA"
[ "$ACTUAL_BACKUP_SHA" = "$EXPECTED_BACKUP_SHA" ] || fail "latest backup sha256 mismatch"

mkdir -p "docs"
mkdir -p ".provenance/operations"
mkdir -p ".provenance/final_seal"

CHECKLIST="docs/OFFSITE_COPY_CHECKLIST.md"
RECEIPT=".provenance/operations/OFFSITE-COPY-RECEIPT-TEMPLATE-0001.md"
SEAL=".provenance/final_seal/FINAL-SEAL-0004-OFFSITE-COPY-CHECKLIST-READY.txt"

cat > "$CHECKLIST" <<EOF
# Offsite Copy Checklist

Status: CHECKLIST_READY
Decision: OFFSITE_COPY_CHECKLIST_AND_RECEIPT

This checklist is documentation-only. It does not perform network transfer or storage replication.

## Source Artifacts To Copy

1. Backup archive
   - path: ${LATEST_BACKUP}
   - sha256: ${ACTUAL_BACKUP_SHA}

2. Backup archive sha256 sidecar
   - path: ${BACKUP_SHA_FILE}

3. Backup manifest
   - path: ${BACKUP_MANIFEST_FILE}

4. Release evidence bundle
   - path: ${RELEASE_BUNDLE}
   - sha256: ${RELEASE_BUNDLE_SHA256}

## Pre-Copy Verification

- [ ] Verify source backup archive exists
- [ ] Verify source backup archive sha256 matches ${ACTUAL_BACKUP_SHA}
- [ ] Verify source backup sha256 sidecar exists
- [ ] Verify source backup manifest exists
- [ ] Verify release evidence bundle exists
- [ ] Verify release evidence bundle sha256 matches ${RELEASE_BUNDLE_SHA256}
- [ ] Verify OFFSITE_REPLICATION_READY seal exists
- [ ] Verify s43.py reference hash remains ${BASELINE_S43_SHA256}

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
- [ ] Confirm copied backup archive sha256 matches ${ACTUAL_BACKUP_SHA}
- [ ] Recompute sha256 for copied release evidence bundle at destination
- [ ] Confirm copied release evidence bundle sha256 matches ${RELEASE_BUNDLE_SHA256}
- [ ] Record destination label, location class, and operator initials
- [ ] Complete offsite copy receipt

## Runtime Safety

- runtime impact: none
- s43.py modified: no
- network transfer required: no
EOF

cat > "$RECEIPT" <<EOF
# OFFSITE COPY RECEIPT TEMPLATE 0001

Status: TEMPLATE_READY

## Copy Session Metadata

- date_utc:
- operator:
- witness_optional:
- source_system:
- destination_type:
- destination_label:
- destination_location_class:
- transfer_mode:
- notes:

## Copied Artifacts

### Backup Archive
- path: ${LATEST_BACKUP}
- expected_sha256: ${ACTUAL_BACKUP_SHA}
- destination_path:
- destination_sha256:
- match_expected: yes/no

### Backup Sha256 Sidecar
- path: ${BACKUP_SHA_FILE}
- destination_path:
- copied: yes/no

### Backup Manifest
- path: ${BACKUP_MANIFEST_FILE}
- destination_path:
- copied: yes/no

### Release Evidence Bundle
- path: ${RELEASE_BUNDLE}
- expected_sha256: ${RELEASE_BUNDLE_SHA256}
- destination_path:
- destination_sha256:
- match_expected: yes/no

## Completion Checks

- source hashes reverified before copy: yes/no
- destination hashes verified after copy: yes/no
- media safely ejected if applicable: yes/no
- chain of custody recorded if applicable: yes/no

## Safety Declaration

This receipt records an offsite copy operation without modifying s43.py or project runtime artifacts.
EOF

cat > "$SEAL" <<EOF
FINAL-SEAL-0004-OFFSITE-COPY-CHECKLIST-READY

status: OFFSITE_COPY_CHECKLIST_READY
date_utc: ${TS}

checklist: ${CHECKLIST}
receipt_template: ${RECEIPT}

basis:
- OFFSITE_REPLICATION_READY
- BACKUP_RESTORE_VERIFIED
- TERMINAL_BACKUP_SNAPSHOT_CREATED
- TERMINAL_CLOSURE_RECORDED
- ARCHIVE_READY_CERTIFIED
- FINAL_MANIFEST_LOCKED
- S43_UNCHANGED

source_backup: ${LATEST_BACKUP}
source_backup_sha256: ${ACTUAL_BACKUP_SHA}
source_backup_sha256_file: ${BACKUP_SHA_FILE}
source_backup_manifest: ${BACKUP_MANIFEST_FILE}
release_bundle: ${RELEASE_BUNDLE}
release_bundle_sha256: ${RELEASE_BUNDLE_SHA256}
s43_py_sha256: ${BASELINE_S43_SHA256}

runtime_impact: none
s43_py_modified: no
copy_performed_by_this_patch: no
EOF

ascii_check "$CHECKLIST" | tee -a "$LOG"
ascii_check "$RECEIPT" | tee -a "$LOG"
ascii_check "$SEAL" | tee -a "$LOG"

S43_AFTER="$(sha256_file s43.py)"
log "s43_after_sha256: $S43_AFTER"
[ "$S43_AFTER" = "$BASELINE_S43_SHA256" ] || fail "s43.py hash mismatch after patch"
[ "$S43_BEFORE" = "$S43_AFTER" ] || fail "s43.py changed during patch"

cat > "$STATUS" <<EOF
OFFSITE_COPY_CHECKLIST_READY
OFFSITE_REPLICATION_READY
ADR_0005_ACCEPTED
BACKUP_RESTORE_VERIFIED
TERMINAL_BACKUP_SNAPSHOT_CREATED
TERMINAL_CLOSURE_RECORDED
ARCHIVE_READY_CERTIFIED
FINAL_MANIFEST_LOCKED
S43_UNCHANGED
TRIWALLET_PROFILE_LAYER_PRESERVED
EOF

log "created: $CHECKLIST"
log "created: $RECEIPT"
log "created: $SEAL"
log "OFFSITE_COPY_ASCII_STATUS OK"
log "PATCH_OK"
log "AUDIT_DIR=$AUDIT_DIR"
cat "$STATUS"
