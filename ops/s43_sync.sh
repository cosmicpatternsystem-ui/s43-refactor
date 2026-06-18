#!/bin/bash
FILE="s43.py"
echo "[$(date)] Checking $FILE..."

# ۱. تست کامپایل
python3 -m py_compile $FILE
if [ $? -ne 0 ]; then
    echo "ERROR: Syntax error! Sync aborted."
    exit 1
fi

# ۲. بررسی تغییرات
if [[ -z $(git status -s $FILE) ]]; then
    echo "No changes in $FILE. Skipping."
    exit 0
fi

# ۳. ارسال به گیت‌هاب
git add $FILE
git commit -m "auto(g11): manual-triggered sync $(date +'%Y-%m-%d %H:%M')"
git push origin master
echo "SUCCESS: $FILE is now on GitHub."
