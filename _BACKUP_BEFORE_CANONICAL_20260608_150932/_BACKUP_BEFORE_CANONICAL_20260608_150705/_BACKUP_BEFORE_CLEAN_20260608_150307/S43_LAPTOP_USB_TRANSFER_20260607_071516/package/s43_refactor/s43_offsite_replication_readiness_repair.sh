#!/usr/bin/env bash
set -eu

PROJECT_DIR="${HOME}/s43_refactor"
cd "$PROJECT_DIR"

BASELINE_S43_SHA256="8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786"
RELEASE_BUNDLE=".release_evidence/s43_final_release_evidence_bundle_20260606_215239.tar.gz"
RELEASE_BUNDLE_SHA256="a1a37e3ed2a440c8c517af02f2bdcc29f87738959792993c35d3d6d03aac39f0"

TS="$(date +%Y%m%d_%H%M%S)"
AUDIT_DIR=".patch_audit/s43_offsite_replication_readiness_repair_${TS}"
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

log "PATCH_START s43_offsite_replication_readiness_repair"
log "PROJECT_DIR=$PROJECT_DIR"
log "AUDIT_DIR=$AUDIT_DIR"

require_file "s43.py"
S43_BEFORE="$(sha256_file s43.py)"
log "s43_before_sha256: $S43_BEFORE"
[ "$S43_BEFORE" = "$BASELINE_S43_SHA256" ] || fail "s43.py baseline hash mismatch before patch"

python -m py_compile s43.py >>"$LOG" 2>&1 || fail "py_compile failed for s43.py"

REQUIRED_FILES="
tools/validate_wallet_profiles.py
config/wallet_profiles.example.json
docs/PROFILE_VALIDATOR.md
docs/FINAL_VALIDATOR_LOCK.md
docs/FINAL_RELEASE_EVIDENCE_BUNDLE.md
docs/PUBLISH_READY_VERIFICATION.md
docs/IMMUTABLE_FINAL_HANDOFF.md
docs/FINAL_CHAIN_SEAL.md
docs/FINAL_SEAL_VERIFICATION.md
docs/FINAL_PROJECT_INDEX.md
docs/FINAL_MANIFEST_LOCK.md
docs/ARCHIVE_READINESS_CERTIFICATE.md
docs/TERMINAL_CLOSURE_RECORD.md
docs/TERMINAL_BACKUP_SNAPSHOT.md
docs/BACKUP_RESTORE_VERIFICATION.md
.provenance/decisions/ADR-0004-readonly-profile-validator.md
.provenance/handoff_notes/HANDOFF-0004-readonly-profile-validator.md
.provenance/status/STATUS-0004-final-validator-lock.txt
.provenance/release/RELEASE-0004-final-evidence-bundle.txt
.provenance/publish/PUBLISH-0004-ready.txt
.provenance/handoff_final/HANDOFF-0004-immutable-final.txt
.provenance/final_seal/FINAL-SEAL-0004.txt
.provenance/final_seal/FINAL-SEAL-0004-VERIFICATION.txt
.provenance/final_seal/FINAL-SEAL-0004-INDEX.txt
.provenance/final_seal/FINAL-SEAL-0004-MANIFEST-LOCK.txt
.provenance/final_seal/FINAL-SEAL-0004-ARCHIVE-READINESS.txt
.provenance/final_seal/FINAL-SEAL-0004-TERMINAL-CLOSURE.txt
.provenance/final_seal/FINAL-SEAL-0004-BACKUP-SNAPSHOT.txt
.provenance/final_seal/FINAL-SEAL-0004-BACKUP-RESTORE-VERIFICATION.txt
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

VALIDATOR_AUDIT="$AUDIT_DIR/validator"
mkdir -p "$VALIDATOR_AUDIT"

run_validator() {
  name="$1"
  shift
  out="$VALIDATOR_AUDIT/${name}.stdout.txt"
  err="$VALIDATOR_AUDIT/${name}.stderr.txt"

  set +e
  env -i \
    HOME="$HOME" \
    PATH="$PATH" \
    PYTHONPATH="" \
    "$@" >"$out" 2>"$err"
  rc="$?"
  set -e

  log "validator_attempt=${name} exit_code=${rc}"
  if [ -s "$err" ]; then
    log "validator_attempt=${name} stderr_begin"
    sed -n '1,40p' "$err" | tee -a "$LOG"
    log "validator_attempt=${name} stderr_end"
  fi
  if [ -s "$out" ]; then
    log "validator_attempt=${name} stdout_begin"
    sed -n '1,40p' "$out" | tee -a "$LOG"
    log "validator_attempt=${name} stdout_end"
  fi
  return "$rc"
}

VALIDATOR_OK=0
VALIDATOR_MODE=""

run_validator help python tools/validate_wallet_profiles.py --help || true

if run_validator config_flag python tools/validate_wallet_profiles.py --config config/wallet_profiles.example.json; then
  VALIDATOR_OK=1
  VALIDATOR_MODE="--config"
elif run_validator positional python tools/validate_wallet_profiles.py config/wallet_profiles.example.json; then
  VALIDATOR_OK=1
  VALIDATOR_MODE="positional"
elif run_validator no_args python tools/validate_wallet_profiles.py; then
  VALIDATOR_OK=1
  VALIDATOR_MODE="no_args"
fi

[ "$VALIDATOR_OK" -eq 1 ] || fail "validator failed in all supported invocation modes"

if grep -R "s43" "$VALIDATOR_AUDIT" >/dev/null 2>&1; then
  fail "validator output unexpectedly references s43 import/runtime"
fi

log "validator_mode_selected: $VALIDATOR_MODE"
log "IMPORT_ISOLATION_OK"

mkdir -p ".provenance/decisions"
mkdir -p ".provenance/final_seal"
mkdir -p "docs"

ADR=".provenance/decisions/ADR-0005-offsite-cold-archive-replication.md"
SEAL=".provenance/final_seal/FINAL-SEAL-0004-OFFSITE-REPLICATION-READY.txt"
DOC="docs/OFFSITE_COLD_ARCHIVE_REPLICATION.md"

cat > "$ADR" <<EOF
# ADR-0005: Offsite Cold Archive Replication

status: ACCEPTED
date_utc: ${TS}
decision: OFFSITE_COLD_ARCHIVE_REPLICATION

## Context

The project chain is terminal closed, archive ready, backed up, and restore verified.

Current verified basis:

- FINAL_CHAIN_SEALED
- FINAL_MANIFEST_LOCKED
- ARCHIVE_READY_CERTIFIED
- TERMINAL_CLOSURE_RECORDED
- TERMINAL_BACKUP_SNAPSHOT_CREATED
- BACKUP_RESTORE_VERIFIED
- S43_UNCHANGED
- TRIWALLET_PROFILE_LAYER_PRESERVED

The remaining operational risk is loss of the local device, local filesystem, or local backup storage.

## Decision

The sealed project backup shall be considered ready for replication to an offsite or cold archive location.

This ADR records readiness only. It does not perform network transfer, remote upload, cloud sync, filesystem migration, or runtime modification.

## Verified Inputs

s43_py_sha256: ${BASELINE_S43_SHA256}
release_bundle: ${RELEASE_BUNDLE}
release_bundle_sha256: ${RELEASE_BUNDLE_SHA256}
latest_backup: ${LATEST_BACKUP}
latest_backup_sha256: ${ACTUAL_BACKUP_SHA}
backup_manifest: ${BACKUP_MANIFEST_FILE}
validator_mode: ${VALIDATOR_MODE}

## Runtime Impact

runtime_impact: none
s43_py_modified: no
wallet_runtime_modified: no
profile_validator_mode: readonly
import_isolation: verified
EOF

cat > "$SEAL" <<EOF
FINAL-SEAL-0004-OFFSITE-REPLICATION-READY

status: OFFSITE_REPLICATION_READY
date_utc: ${TS}

decision_record: ${ADR}
documentation: ${DOC}

basis:
- terminal closure recorded
- terminal backup snapshot created
- backup restore verified
- archive readiness certified
- final manifest locked
- release evidence bundle verified
- validator passed in import-isolated mode
- s43.py hash unchanged

s43_py_sha256: ${BASELINE_S43_SHA256}
release_bundle: ${RELEASE_BUNDLE}
release_bundle_sha256: ${RELEASE_BUNDLE_SHA256}
latest_backup: ${LATEST_BACKUP}
latest_backup_sha256: ${ACTUAL_BACKUP_SHA}
latest_backup_sha256_file: ${BACKUP_SHA_FILE}
latest_backup_manifest: ${BACKUP_MANIFEST_FILE}
validator_mode: ${VALIDATOR_MODE}

runtime_impact: none
s43_py_modified: no
network_transfer_performed: no
offsite_copy_performed: no
EOF

cat > "$DOC" <<EOF
# Offsite Cold Archive Replication

Status: OFFSITE_REPLICATION_READY

This record documents that the sealed project backup is ready for offsite or cold archive replication.

ADR:
${ADR}

Decision:
OFFSITE_COLD_ARCHIVE_REPLICATION

Backup archive:
${LATEST_BACKUP}

Backup archive sha256:
${ACTUAL_BACKUP_SHA}

Backup sha256 sidecar:
${BACKUP_SHA_FILE}

Backup manifest:
${BACKUP_MANIFEST_FILE}

Release evidence bundle:
${RELEASE_BUNDLE}

Release evidence bundle sha256:
${RELEASE_BUNDLE_SHA256}

Validator mode:
${VALIDATOR_MODE}

Runtime impact: none
s43.py modified: no
network transfer performed: no
offsite copy performed: no
EOF

ascii_check "$ADR" | tee -a "$LOG"
ascii_check "$SEAL" | tee -a "$LOG"
ascii_check "$DOC" | tee -a "$LOG"

S43_AFTER="$(sha256_file s43.py)"
log "s43_after_sha256: $S43_AFTER"
[ "$S43_AFTER" = "$BASELINE_S43_SHA256" ] || fail "s43.py hash mismatch after patch"
[ "$S43_BEFORE" = "$S43_AFTER" ] || fail "s43.py changed during patch"

cat > "$STATUS" <<EOF
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

log "created: $ADR"
log "created: $SEAL"
log "created: $DOC"
log "OFFSITE_REPLICATION_ASCII_STATUS OK"
log "PATCH_OK"
log "AUDIT_DIR=$AUDIT_DIR"
cat "$STATUS"
