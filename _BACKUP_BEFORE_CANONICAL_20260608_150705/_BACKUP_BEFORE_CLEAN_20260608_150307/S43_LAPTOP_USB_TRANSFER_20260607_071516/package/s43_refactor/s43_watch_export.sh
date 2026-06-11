#!/data/data/com.termux/files/usr/bin/bash
set -e

cd "$HOME/s43_refactor"

last_hash=""

echo "S43 watch export started."
echo "Watching: $HOME/s43_refactor/s43.py"
echo "Exporting to: /sdcard/Download"
echo "Interval: 30 seconds"

while true; do
  if [ -f "s43.py" ]; then
    current_hash="$(sha256sum s43.py | awk '{print $1}')"
    if [ "$current_hash" != "$last_hash" ]; then
      ./s43_checkpoint.sh
      last_hash="$current_hash"
    fi
  fi
  sleep 30
done
