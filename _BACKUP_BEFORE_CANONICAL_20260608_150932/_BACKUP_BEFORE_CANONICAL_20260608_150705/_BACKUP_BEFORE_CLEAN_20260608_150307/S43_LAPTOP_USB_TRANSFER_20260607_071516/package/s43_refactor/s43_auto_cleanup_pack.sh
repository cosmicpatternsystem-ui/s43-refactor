#!/usr/bin/env bash

echo "=== S43 AUTO CLEANUP + PACK START ==="

ts=$(date +%Y%m%d_%H%M%S)

echo
echo "---- STEP 1: Create archive folders ----"

mkdir -p archive/snapshots
mkdir -p archive/reports
mkdir -p archive/logs
mkdir -p archive/old_tools
mkdir -p archive_packed_backup

echo
echo "---- STEP 2: Move old snapshot files ----"

find . -maxdepth 1 -type f \( \
-name 's43.py.bak*' -o \
-name 's43.py.before*' -o \
-name 's43.py.pre_*' -o \
-name 's43.py.fix*.bak*' -o \
-name 'snap_before_patch_*.py' -o \
-name 's43_before_*.py' -o \
-name 's43_backup_before_*.py' -o \
-name 's43_broken_before_restore_*.py' -o \
-name 's43_final_repaired*.py' -o \
-name 's43_dev_next*.py' -o \
-name 's43_FINAL_*.py' \
\) -exec mv {} archive/snapshots/ \;

echo
echo "---- STEP 3: Move report files ----"

mv s43_final_status_* archive/reports/ 2>/dev/null
mv *audit*.txt archive/reports/ 2>/dev/null
mv *status*.txt archive/reports/ 2>/dev/null
mv *.log archive/logs/ 2>/dev/null

echo
echo "---- STEP 4: Move old helper tools ----"

mv s43_*audit*.py archive/old_tools/ 2>/dev/null
mv s43_*review*.py archive/old_tools/ 2>/dev/null
mv s43_extract_*.py archive/old_tools/ 2>/dev/null
mv s43_apply_*.py archive/old_tools/ 2>/dev/null

echo
echo "---- STEP 5: Verify active release file ----"

if [ ! -f s43.py ]; then
  echo "ERROR: s43.py not found in current directory."
  exit 1
fi

python -m py_compile s43.py
if [ $? -ne 0 ]; then
  echo "ERROR: s43.py compile failed."
  exit 1
fi

echo "OK: s43.py compile passed"

latest_release=$(ls -t release_backups/s43.py.final_* 2>/dev/null | head -n 1)

if [ -n "$latest_release" ] && cmp -s s43.py "$latest_release"; then
  echo "OK: active s43.py matches latest release backup"
else
  echo "WARN: active s43.py does not match latest release backup or backup not found"
fi

echo
echo "---- STEP 6: Create compressed archive pack ----"

pack_file="S43_ARCHIVE_PACK_${ts}.tar.gz"
manifest_file="S43_ARCHIVE_PACK_MANIFEST_${ts}.txt"

tar -czf "$pack_file" archive

if [ ! -s "$pack_file" ]; then
  echo "ERROR: pack file was not created or is empty."
  exit 1
fi

echo "Created pack:"
ls -lh "$pack_file"

echo
echo "---- STEP 7: Verify compressed pack ----"

if tar -tzf "$pack_file" >/dev/null; then
  echo "OK: tar.gz integrity verified"
else
  echo "ERROR: tar.gz integrity check failed."
  exit 1
fi

echo
echo "---- STEP 8: Write pack manifest ----"

{
  echo "S43 AUTO CLEANUP PACK MANIFEST"
  echo "Created: $(date)"
  echo
  echo "Active file:"
  ls -lh s43.py
  echo
  echo "Latest release backup:"
  if [ -n "$latest_release" ]; then
    ls -lh "$latest_release"
  else
    echo "No release backup found"
  fi
  echo
  echo "Pack file:"
  ls -lh "$pack_file"
  echo
  echo "SHA256:"
  sha256sum s43.py
  if [ -n "$latest_release" ]; then
    sha256sum "$latest_release"
  fi
  sha256sum "$pack_file"
  echo
  echo "Archive tree:"
  find archive -maxdepth 3 -type f | sort
} > "$manifest_file"

echo "Created manifest:"
ls -lh "$manifest_file"

echo
echo "---- STEP 9: Move pack and preserve original archive folder ----"

mv "$pack_file" archive_packed_backup/
mv "$manifest_file" archive_packed_backup/

preserved_dir="archive_packed_backup/archive_original_${ts}"
mv archive "$preserved_dir"

echo "Original archive moved to:"
echo "$preserved_dir"

echo
echo "---- STEP 10: Final project status ----"

echo "Project size:"
du -sh .

echo
echo "Root files:"
ls -lh

echo
echo "Packed backup contents:"
ls -lh archive_packed_backup

echo
echo "=== S43 AUTO CLEANUP + PACK COMPLETE ==="
