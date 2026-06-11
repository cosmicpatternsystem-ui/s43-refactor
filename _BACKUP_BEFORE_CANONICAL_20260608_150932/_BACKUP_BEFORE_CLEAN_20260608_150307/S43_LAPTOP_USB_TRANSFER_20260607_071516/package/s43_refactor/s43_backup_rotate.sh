#!/data/data/com.termux/files/usr/bin/bash
set -e

BACKUP_DIR="release_backups"
MAX_BACKUPS="${MAX_BACKUPS:-10}"

echo "== S43 Backup Rotation =="

if [ ! -d "$BACKUP_DIR" ]; then
  echo "ERROR: $BACKUP_DIR not found."
  exit 1
fi

count="$(find "$BACKUP_DIR" -maxdepth 1 -type f -name 's43.py.final_*' | wc -l | tr -d ' ')"

echo "Found release backups: $count"
echo "Max backups to keep: $MAX_BACKUPS"

if [ "$count" -gt "$MAX_BACKUPS" ]; then
  remove_count=$((count - MAX_BACKUPS))
  echo "Removing old backups: $remove_count"

  find "$BACKUP_DIR" -maxdepth 1 -type f -name 's43.py.final_*' -printf '%T@ %p\n' \
| sort -nr \
| tail -n "$remove_count" \
| cut -d' ' -f2- \
| while IFS= read -r file; do
rm -f "$file"
echo "Removed: $file"
done
else
  echo "No rotation needed."
fi

echo "Backup rotation complete."
