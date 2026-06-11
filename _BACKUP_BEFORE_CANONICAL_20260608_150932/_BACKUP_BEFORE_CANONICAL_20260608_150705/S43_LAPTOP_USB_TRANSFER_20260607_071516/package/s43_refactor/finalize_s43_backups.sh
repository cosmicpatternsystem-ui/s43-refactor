#!/usr/bin/env bash
set -u

PROJECT_DIR="$(pwd)"
TS="$(date +%Y%m%d-%H%M%S)"
REPORT="BACKUP_VALIDATION_REPORT_${TS}.md"
MANIFEST="BACKUP_MANIFEST_${TS}.tsv"

ACTIVE="s43.py"
STABLE_SRC="s43.py.bak_guard_phase1c_1780471331"
RESTORE_SRC="s43.py.baseline_restored_phase1c_dryrun_ok"
BROKEN_SRC="s43.py.syntax_broken_guard_injected_backup"

STABLE_ALIAS="s43.py.STABLE_BASELINE_CONFIRMED"
RESTORE_ALIAS="s43.py.RESTORE_CONFIRMED"
BROKEN_ALIAS="s43.py.BROKEN_REFERENCE"

echo "== S43 Backup Finalizer =="
echo "Project: $PROJECT_DIR"
echo "Timestamp: $TS"
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
  if [ ! -f "$f" ]; then
    echo "MISSING"
    return 0
  fi

  if python -m py_compile "$f" >/tmp/s43_pycompile_ok_$$.log 2>/tmp/s43_pycompile_err_$$.log; then
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
  local exists="no"

  if [ -f "$file" ]; then
    exists="yes"
  fi

  local lines
  local size
  local sha
  local comp

  lines="$(lines_of "$file")"
  size="$(size_of "$file")"
  sha="$(sha_of "$file")"
  comp="$(compile_status "$file")"

  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$role" "$file" "$exists" "$lines" "$size" "$sha" "$comp" >> "$MANIFEST"
}

echo "Step 1/4: Creating final aliases..."
copy_alias_no_overwrite "$STABLE_SRC" "$STABLE_ALIAS"
copy_alias_no_overwrite "$RESTORE_SRC" "$RESTORE_ALIAS"
copy_alias_no_overwrite "$BROKEN_SRC" "$BROKEN_ALIAS"
echo

echo "Step 2/4: Building manifest..."
printf 'ROLE\tFILE\tEXISTS\tLINES\tSIZE_BYTES\tSHA256\tPY_COMPILE\n' > "$MANIFEST"

write_file_row "ACTIVE" "$ACTIVE"
write_file_row "STABLE_SOURCE" "$STABLE_SRC"
write_file_row "RESTORE_SOURCE" "$RESTORE_SRC"
write_file_row "BROKEN_SOURCE" "$BROKEN_SRC"
write_file_row "STABLE_ALIAS" "$STABLE_ALIAS"
write_file_row "RESTORE_ALIAS" "$RESTORE_ALIAS"
write_file_row "BROKEN_ALIAS" "$BROKEN_ALIAS"

echo "Manifest written: $MANIFEST"
echo

echo "Step 3/4: Comparing important hashes..."

ACTIVE_SHA="$(sha_of "$ACTIVE")"
STABLE_SHA="$(sha_of "$STABLE_SRC")"
RESTORE_SHA="$(sha_of "$RESTORE_SRC")"
STABLE_ALIAS_SHA="$(sha_of "$STABLE_ALIAS")"
RESTORE_ALIAS_SHA="$(sha_of "$RESTORE_ALIAS")"

ACTIVE_LINES="$(lines_of "$ACTIVE")"
ACTIVE_SIZE="$(size_of "$ACTIVE")"

STABLE_MATCH="UNKNOWN"
RESTORE_MATCH="UNKNOWN"
ALIAS_MATCH="UNKNOWN"

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

echo "Active vs Stable Source SHA match:  $STABLE_MATCH"
echo "Active vs Restore Source SHA match: $RESTORE_MATCH"
echo "Stable Source vs Stable Alias match: $ALIAS_MATCH"
echo

echo "Step 4/4: Writing markdown report..."

cat > "$REPORT" <<MD
# S43 Backup Validation Report

## Generated
- Timestamp: $TS
- Project Dir: $PROJECT_DIR

## Policy
- This report was generated without modifying \`s43.py\`.
- Final aliases are created with \`cp -p\`.
- Existing aliases are not overwritten.
- Python syntax validation is performed with \`python -m py_compile\`.

## Active File
- File: \`$ACTIVE\`
- Lines: $ACTIVE_LINES
- Size bytes: $ACTIVE_SIZE
- SHA256: \`$ACTIVE_SHA\`

## Final Naming

| Role | Final Name |
|---|---|
| Active main file | \`s43.py\` |
| Stable baseline alias | \`$STABLE_ALIAS\` |
| Restore-confirmed alias | \`$RESTORE_ALIAS\` |
| Broken forensic reference | \`$BROKEN_ALIAS\` |

## Source Mapping

| Role | Source |
|---|---|
| Stable source | \`$STABLE_SRC\` |
| Restore-confirmed source | \`$RESTORE_SRC\` |
| Broken reference source | \`$BROKEN_SRC\` |

## Hash Comparison

| Check | Result |
|---|---|
| Active vs Stable Source | $STABLE_MATCH |
| Active vs Restore Source | $RESTORE_MATCH |
| Stable Source vs Stable Alias | $ALIAS_MATCH |

## Manifest
Detailed manifest file:

\`$MANIFEST\`

## Recommended Freeze Decision

If:
- \`s43.py\` has \`PY_COMPILE=PASS\`
- \`$STABLE_ALIAS\` has \`PY_COMPILE=PASS\`
- \`$RESTORE_ALIAS\` has \`PY_COMPILE=PASS\`
- Active hash matches at least one confirmed stable/restored backup

Then the project backup state is considered:

\`VALIDATED / NAMED / FREEZE-SAFE\`

MD

echo "Report written: $REPORT"
echo

echo "== Quick Manifest Preview =="
column -t -s $'\t' "$MANIFEST" 2>/dev/null || cat "$MANIFEST"
echo

echo "== Report Preview =="
sed -n '1,80p' "$REPORT"
echo

echo "DONE."
