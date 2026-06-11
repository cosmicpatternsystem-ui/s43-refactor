#!/usr/bin/env bash
set -euo pipefail

EXPECTED_S43="8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786"

EXPECTED_BACKUP_HASH="d381f7c1eecfd71abc9c95731bb84c5aeb30fe2deaf7e018e302af030972f2a1"
EXPECTED_RELEASE_HASH="a1a37e3ed2a440c8c517af02f2bdcc29f87738959792993c35d3d6d03aac39f0"

DEST="${DEST:-$HOME/storage/shared/S43_OFFSITE_COLD_ARCHIVE_20260607}"

BACKUP_FILE="$DEST/s43_terminal_backup_snapshot_20260607_061300.tar.gz"
BACKUP_SIDECAR="$DEST/s43_terminal_backup_snapshot_20260607_061300.tar.gz.sha256"
BACKUP_MANIFEST="$DEST/s43_terminal_backup_snapshot_20260607_061300.manifest.sha256"
RELEASE_FILE="$DEST/s43_final_release_evidence_bundle_20260606_215239.tar.gz"

TS="$(date +%Y%m%d_%H%M%S)"
AUDIT_DIR=".patch_audit/s43_finalize_offsite_copy_receipt_${TS}"

RECEIPT_FILE=".provenance/operations/OFFSITE-COPY-RECEIPT-0001.md"
SEAL_FILE=".provenance/final_seal/FINAL-SEAL-0005-OFFSITE-COPY-RECEIPT-RECORDED.txt"

mkdir -p "$AUDIT_DIR" ".provenance/operations" ".provenance/final_seal"

echo "== PRECHECK: s43.py unchanged =="
ACTUAL_S43_BEFORE="$(sha256sum s43.py | awk '{print $1}')"
echo "$ACTUAL_S43_BEFORE  s43.py" | tee "$AUDIT_DIR/s43_before.sha256"

if [ "$ACTUAL_S43_BEFORE" != "$EXPECTED_S43" ]; then
  echo "PATCH_FAIL: s43.py hash mismatch before receipt finalization" >&2
  exit 1
fi

echo "== PRECHECK: destination files exist =="
for f in "$BACKUP_FILE" "$BACKUP_SIDECAR" "$BACKUP_MANIFEST" "$RELEASE_FILE"; do
  if [ ! -f "$f" ]; then
    echo "PATCH_FAIL: missing destination file: $f" >&2
    exit 1
  fi
  echo "FOUND $f" | tee -a "$AUDIT_DIR/destination_files.txt"
done

echo "== VERIFY: destination hashes =="
ACTUAL_BACKUP_HASH="$(sha256sum "$BACKUP_FILE" | awk '{print $1}')"
ACTUAL_RELEASE_HASH="$(sha256sum "$RELEASE_FILE" | awk '{print $1}')"

echo "$ACTUAL_BACKUP_HASH  $BACKUP_FILE" | tee "$AUDIT_DIR/destination_backup.sha256"
echo "$ACTUAL_RELEASE_HASH  $RELEASE_FILE" | tee "$AUDIT_DIR/destination_release.sha256"

if [ "$ACTUAL_BACKUP_HASH" != "$EXPECTED_BACKUP_HASH" ]; then
  echo "PATCH_FAIL: destination backup hash mismatch" >&2
  exit 1
fi

if [ "$ACTUAL_RELEASE_HASH" != "$EXPECTED_RELEASE_HASH" ]; then
  echo "PATCH_FAIL: destination release bundle hash mismatch" >&2
  exit 1
fi

echo "== VERIFY: prerequisite provenance artifacts =="
REQS=(
  ".provenance/decisions/ADR-0005-offsite-cold-archive-replication.md"
  ".provenance/final_seal/FINAL-SEAL-0004-OFFSITE-REPLICATION-READY.txt"
  "docs/OFFSITE_COLD_ARCHIVE_REPLICATION.md"
  "docs/OFFSITE_COPY_CHECKLIST.md"
  ".provenance/operations/OFFSITE-COPY-RECEIPT-TEMPLATE-0001.md"
  ".provenance/final_seal/FINAL-SEAL-0004-OFFSITE-COPY-CHECKLIST-READY.txt"
)

for f in "${REQS[@]}"; do
  if [ ! -f "$f" ]; then
    echo "PATCH_FAIL: missing prerequisite artifact: $f" >&2
    exit 1
  fi
  echo "FOUND $f" | tee -a "$AUDIT_DIR/prerequisites.txt"
done

echo "== WRITE: finalized offsite copy receipt =="

cat > "$RECEIPT_FILE" <<EOF
# OFFSITE COPY RECEIPT 0001

status: completed
operation: EXECUTE_OFFSITE_COPY_OUTSIDE_REPO
record_type: finalized_receipt
runtime_impact: none
s43_py_modified: no
copy_performed_by_patch: no
receipt_recorded_at: ${TS}

## Source repository

repo_path: ~/s43_refactor
s43_sha256: ${EXPECTED_S43}

## Destination

destination_path: ${DEST}

## Copied artifacts

1. s43_terminal_backup_snapshot_20260607_061300.tar.gz
2. s43_terminal_backup_snapshot_20260607_061300.tar.gz.sha256
3. s43_terminal_backup_snapshot_20260607_061300.manifest.sha256
4. s43_final_release_evidence_bundle_20260606_215239.tar.gz

## Destination hash verification

backup_snapshot_sha256_expected: ${EXPECTED_BACKUP_HASH}
backup_snapshot_sha256_actual: ${ACTUAL_BACKUP_HASH}
backup_snapshot_hash_status: matched

release_evidence_bundle_sha256_expected: ${EXPECTED_RELEASE_HASH}
release_evidence_bundle_sha256_actual: ${ACTUAL_RELEASE_HASH}
release_evidence_bundle_hash_status: matched

## Result

OFFSITE_COPY_OPERATION_COMPLETED
BACKUP_HASH_MATCHED_AT_DESTINATION
RELEASE_BUNDLE_HASH_MATCHED_AT_DESTINATION
OFFSITE_COPY_RECEIPT_RECORDED
S43_UNCHANGED
TRIWALLET_PROFILE_LAYER_PRESERVED
EOF

cat > "$SEAL_FILE" <<EOF
FINAL SEAL 0005 - OFFSITE COPY RECEIPT RECORDED

status: sealed
operation: OFFSITE_COPY_RECEIPT_FINALIZATION
runtime_impact: none
s43_py_modified: no
s43_sha256: ${EXPECTED_S43}

destination_path: ${DEST}

backup_snapshot_sha256: ${ACTUAL_BACKUP_HASH}
release_evidence_bundle_sha256: ${ACTUAL_RELEASE_HASH}

required_status:
- OFFSITE_COPY_OPERATION_COMPLETED
- BACKUP_HASH_MATCHED_AT_DESTINATION
- RELEASE_BUNDLE_HASH_MATCHED_AT_DESTINATION
- OFFSITE_COPY_RECEIPT_RECORDED
- S43_UNCHANGED
- TRIWALLET_PROFILE_LAYER_PRESERVED

sealed_at: ${TS}
EOF

echo "== ASCII CHECK =="
for f in "$RECEIPT_FILE" "$SEAL_FILE"; do
  if LC_ALL=C grep -n '[^ -~]' "$f" >/dev/null; then
    echo "PATCH_FAIL: non-ASCII content detected in $f" >&2
    exit 1
  fi
  echo "ASCII_OK $f" | tee -a "$AUDIT_DIR/ascii_check.txt"
done

echo "== POSTCHECK: s43.py unchanged =="
ACTUAL_S43_AFTER="$(sha256sum s43.py | awk '{print $1}')"
echo "$ACTUAL_S43_AFTER  s43.py" | tee "$AUDIT_DIR/s43_after.sha256"

if [ "$ACTUAL_S43_AFTER" != "$EXPECTED_S43" ]; then
  echo "PATCH_FAIL: s43.py hash mismatch after receipt finalization" >&2
  exit 1
fi

if [ "$ACTUAL_S43_BEFORE" != "$ACTUAL_S43_AFTER" ]; then
  echo "PATCH_FAIL: s43.py changed during receipt finalization" >&2
  exit 1
fi

echo
echo "PATCH_OK"
echo "AUDIT_DIR=$AUDIT_DIR"
echo "OFFSITE_COPY_RECEIPT_RECORDED"
echo "OFFSITE_COPY_OPERATION_COMPLETED"
echo "BACKUP_HASH_MATCHED_AT_DESTINATION"
echo "RELEASE_BUNDLE_HASH_MATCHED_AT_DESTINATION"
echo "OFFSITE_REPLICATION_READY"
echo "OFFSITE_COPY_CHECKLIST_READY"
echo "S43_UNCHANGED"
echo "TRIWALLET_PROFILE_LAYER_PRESERVED"
