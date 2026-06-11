#!/usr/bin/env bash
set -u

PROJECT_DIR="$(pwd)"
TS="$(date +%Y%m%d-%H%M%S)"
TMP_DIR=".s43_tmp_compile_${TS}"
REPORT="BACKUP_VALIDATION_REPORT_V2_${TS}.md"
MANIFEST="BACKUP_MANIFEST_V2_${TS}.tsv"

ACTIVE="s43.py"
STABLE_SRC="s43.py.bak_guard_phase1c_1780471331"
RESTORE_SRC="s43.py.baseline_restored_phase1c_dryrun_ok"
BROKEN_SRC="s43.py.syntax_broken_guard_injected_backup"

STABLE_ALIAS="s43.py.STABLE_BASELINE_CONFIRMED"
RESTORE_ALIAS="s43.py.RESTORE_CONFIRMED"
BROKEN_ALIAS="s43.py.BROKEN_REFERENCE"

EXPECTED_STABLE_LINES="29958"
EXPECTED_STABLE_SIZE="2620287"
EXPECTED_STABLE_SHA="c5b0b5cf1e20dc253d91867d833cf5a02f53324b07f491f4acb891caad45b334"

mkdir -p "$TMP_DIR"

echo "== S43 Backup Finalizer V2 =="
echo "Project: $PROJECT_DIR"
echo "Timestamp: $TS"
echo "Temp dir: $TMP_DIR"
echo

sha_of() {
  if [ -f "$1" ]; then
    sha256sum "$1" | awk '{print $1}'
  else
    echo "MISSING"
  fi
}

lines_of() {
  if [ -f "$1" ]; then
    wc -l < "$1" | tr -d ' '
  else
    echo "MISSING"
  fi
}

size_of() {
  if [ -f "$1" ]; then
    stat -c '%s' "$1" 2>/dev/null || wc -c < "$1" | tr -d ' '
  else
    echo "MISSING"
  fi
}

compile_status() {
  local f="$1"
  local base
  base="$(basename "$f")"

  if [ ! -f "$f" ]; then
    echo "MISSING"
    return 0
  fi

  if python -m py_compile "$f" >"$TMP_DIR/${base}.pycompile.out" 2>"$TMP_DIR/${base}.pycompile.err"; then
    echo "PASS"
  else
    echo "FAIL"
  fi
}

copy_alias_no_overwrite() {
  local src="$1"
  local dst="$2"

  if [ ! -f "$src" ]; then
    echo "SKIP: source missing: $src -> $dst"
    return 0
  fi

  if [ -f "$dst" ]; then
    local s1
    local s2
    s1="$(sha_of "$src")"
    s2="$(sha_of "$dst")"

    if [ "$s1" = "$s2" ]; then
      echo "OK: alias already exists and matches: $dst"
    else
      echo "WARN: alias exists but SHA differs: $dst"
      echo "      existing alias was NOT overwritten"
    fi
    return 0
  fi

  cp -p "$src" "$dst"
  echo "CREATED: $dst from $src"
}

write_file_row() {
  local role="$1"
  local file="$2"
  local expected_kind="$3"
  local exists="no"

  if [ -f "$file" ]; then
    exists="yes"
  fi

  local lines
  local size
  local sha
  local comp
  local stable_fingerprint

  lines="$(lines_of "$file")"
  size="$(size_of "$file")"
  sha="$(sha_of "$file")"
  comp="$(compile_status "$file")"

  stable_fingerprint="N/A"

  if [ "$expected_kind" = "STABLE" ]; then
    if [ "$lines" = "$EXPECTED_STABLE_LINES" ] && [ "$size" = "$EXPECTED_STABLE_SIZE" ] && [ "$sha" = "$EXPECTED_STABLE_SHA" ]; then
      stable_fingerprint="MATCH"
    else
      stable_fingerprint="MISMATCH"
    fi
  fi

  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$role" "$file" "$exists" "$lines" "$size" "$sha" "$comp" "$stable_fingerprint" >> "$MANIFEST"
}

echo "Step 1/5: Verifying aliases..."
copy_alias_no_overwrite "$STABLE_SRC" "$STABLE_ALIAS"
copy_alias_no_overwrite "$RESTORE_SRC" "$RESTORE_ALIAS"
copy_alias_no_overwrite "$BROKEN_SRC" "$BROKEN_ALIAS"
echo

echo "Step 2/5: Building V2 manifest..."
printf 'ROLE\tFILE\tEXISTS\tLINES\tSIZE_BYTES\tSHA256\tPY_COMPILE\tSTABLE_FINGERPRINT\n' > "$MANIFEST"

write_file_row "ACTIVE" "$ACTIVE" "STABLE"
write_file_row "STABLE_SOURCE" "$STABLE_SRC" "STABLE"
write_file_row "RESTORE_SOURCE" "$RESTORE_SRC" "STABLE"
write_file_row "BROKEN_SOURCE" "$BROKEN_SRC" "BROKEN"
write_file_row "STABLE_ALIAS" "$STABLE_ALIAS" "STABLE"
write_file_row "RESTORE_ALIAS" "$RESTORE_ALIAS" "STABLE"
write_file_row "BROKEN_ALIAS" "$BROKEN_ALIAS" "BROKEN"

echo "Manifest written: $MANIFEST"
echo

echo "Step 3/5: Comparing important hashes..."

ACTIVE_SHA="$(sha_of "$ACTIVE")"
STABLE_SHA="$(sha_of "$STABLE_SRC")"
RESTORE_SHA="$(sha_of "$RESTORE_SRC")"
STABLE_ALIAS_SHA="$(sha_of "$STABLE_ALIAS")"
RESTORE_ALIAS_SHA="$(sha_of "$RESTORE_ALIAS")"

ACTIVE_LINES="$(lines_of "$ACTIVE")"
ACTIVE_SIZE="$(size_of "$ACTIVE")"
ACTIVE_COMPILE="$(compile_status "$ACTIVE")"

STABLE_MATCH="UNKNOWN"
RESTORE_MATCH="UNKNOWN"
ALIAS_MATCH="UNKNOWN"
FINGERPRINT_MATCH="UNKNOWN"

if [ "$ACTIVE_SHA" != "MISSING" ] && [ "$STABLE_SHA" != "MISSING" ]; then
  if [ "$ACTIVE_SHA" = "$STABLE_SHA" ]; then
    STABLE_MATCH="YES"
  else
    STABLE_MATCH="NO"
  fi
fi

if [ "$ACTIVE_SHA" != "MISSING" ] && [ "$RESTORE_SHA" != "MISSING" ]; then
  if [ "$ACTIVE_SHA" = "$RESTORE_SHA" ]; then
    RESTORE_MATCH="YES"
  else
    RESTORE_MATCH="NO"
  fi
fi

if [ "$STABLE_SHA" != "MISSING" ] && [ "$STABLE_ALIAS_SHA" != "MISSING" ]; then
  if [ "$STABLE_SHA" = "$STABLE_ALIAS_SHA" ]; then
    ALIAS_MATCH="YES"
  else
    ALIAS_MATCH="NO"
  fi
fi

if [ "$ACTIVE_LINES" = "$EXPECTED_STABLE_LINES" ] && [ "$ACTIVE_SIZE" = "$EXPECTED_STABLE_SIZE" ] && [ "$ACTIVE_SHA" = "$EXPECTED_STABLE_SHA" ]; then
  FINGERPRINT_MATCH="YES"
else
  FINGERPRINT_MATCH="NO"
fi

echo "Active vs Stable Source SHA match:   $STABLE_MATCH"
echo "Active vs Restore Source SHA match:  $RESTORE_MATCH"
echo "Stable Source vs Stable Alias match: $ALIAS_MATCH"
echo "Active stable fingerprint match:     $FINGERPRINT_MATCH"
echo "Active py_compile:                   $ACTIVE_COMPILE"
echo

echo "Step 4/5: Writing V2 markdown report..."

cat > "$REPORT" <<MD
# S43 Backup Validation Report V2

## Generated
- Timestamp: $TS
- Project Dir: $PROJECT_DIR
- Temp Compile Dir: $TMP_DIR

## Policy
- This report was generated without modifying \`s43.py\`.
- Final aliases are created with \`cp -p\`.
- Existing aliases are not overwritten.
- Python syntax validation is performed with \`python -m py_compile\`.
- Termux-safe local temp directory is used instead of \`/tmp\`.

## Expected Stable Fingerprint
- Lines: $EXPECTED_STABLE_LINES
- Size bytes: $EXPECTED_STABLE_SIZE
- SHA256: \`$EXPECTED_STABLE_SHA\`

## Active File
- File: \`$ACTIVE\`
- Lines: $ACTIVE_LINES
- Size bytes: $ACTIVE_SIZE
- SHA256: \`$ACTIVE_SHA\`
- PY_COMPILE: $ACTIVE_COMPILE
- Stable Fingerprint Match: $FINGERPRINT_MATCH

## Final Naming

| Role | Final Name |
|---|---|
| Active main file | \`s43.py\` |
| Stable baseline alias | \`$STABLE_ALIAS\` |
| Restore-confirmed alias | \`$RESTORE_ALIAS\` |
| Broken forensic reference | \`$BROKEN_ALIAS\` |

## Hash Comparison

| Check | Result |
|---|---|
| Active vs Stable Source | $STABLE_MATCH |
| Active vs Restore Source | $RESTORE_MATCH |
| Stable Source vs Stable Alias | $ALIAS_MATCH |
| Active Stable Fingerprint | $FINGERPRINT_MATCH |

## Manifest
Detailed manifest file:

\`$MANIFEST\`

## Decision

If:
- Active PY_COMPILE is \`PASS\`
- Active Stable Fingerprint is \`YES\`
- Active vs Stable Source is \`YES\`
- Active vs Restore Source is \`YES\`

Then status is:

\`VALIDATED / NAMED / FREEZE-SAFE / TERMUX-COMPATIBLE\`

MD

echo "Report written: $REPORT"
echo

echo "Step 5/5: Preview..."
echo

echo "== Quick Manifest Preview V2 =="
column -t -s $'\t' "$MANIFEST" 2>/dev/null || cat "$MANIFEST"
echo

echo "== Report Preview V2 =="
sed -n '1,90p' "$REPORT"
echo

echo "== Compile Error Preview If Any =="
find "$TMP_DIR" -type f -name '*.err' -size +0c -maxdepth 1 2>/dev/null -print -exec sed -n '1,40p' {} \;
echo

echo "DONE V2."
