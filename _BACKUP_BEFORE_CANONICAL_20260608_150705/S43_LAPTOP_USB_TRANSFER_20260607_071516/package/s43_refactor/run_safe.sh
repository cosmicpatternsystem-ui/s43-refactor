#!/data/data/com.termux/files/usr/bin/bash

cd "$(dirname "$0")" || exit 1

./arzplus_healthcheck.sh
STATUS=$?

if [ "$STATUS" -ne 0 ]; then
  echo ""
  echo "STOP: healthcheck failed, s43.py will not start."
  exit 1
fi

echo ""
echo "Starting s43.py..."
python s43.py
