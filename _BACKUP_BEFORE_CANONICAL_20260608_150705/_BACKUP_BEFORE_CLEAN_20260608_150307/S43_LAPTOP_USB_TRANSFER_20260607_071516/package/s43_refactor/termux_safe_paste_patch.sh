#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

PROJECT_DIR="${HOME}/s43_refactor"
BIN_DIR="${PROJECT_DIR}/bin"
mkdir -p "$BIN_DIR"

cat > "${BIN_DIR}/termux_write_file.py" <<'PY'
#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print("usage: termux_write_file.py <target>", file=sys.stderr)
        sys.exit(2)

    target = Path(sys.argv[1]).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    data = sys.stdin.read()

    tmp = target.with_suffix(target.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

    os.replace(tmp, target)
    print(str(target))

if __name__ == "__main__":
    main()
PY

chmod +x "${BIN_DIR}/termux_write_file.py"

cat > "${BIN_DIR}/termux_write_sh" <<'SH2'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: termux_write_sh <target-file>" >&2
  exit 2
fi

TARGET="$1"
python3 "${HOME}/s43_refactor/bin/termux_write_file.py" "$TARGET"
chmod 700 "$TARGET"
SH2

chmod +x "${BIN_DIR}/termux_write_sh"

cat > "${BIN_DIR}/termux_write_text" <<'SH3'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "usage: termux_write_text <target-file>" >&2
  exit 2
fi

TARGET="$1"
python3 "${HOME}/s43_refactor/bin/termux_write_file.py" "$TARGET"
chmod 600 "$TARGET" 2>/dev/null || true
SH3

chmod +x "${BIN_DIR}/termux_write_text"

cat > "${BIN_DIR}/termux_paste_guard" <<'SH4'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

echo "======================================"
echo "TERMUX SAFE PASTE GUARD"
echo "======================================"
echo "1) For long content, do NOT paste directly into bash logic."
echo "2) Use: termux_write_sh <file>   for shell scripts"
echo "3) Use: termux_write_text <file> for text/config files"
echo "4) Finish input with Ctrl-D"
echo "5) Then run: bash -n <script> before execution"
echo "======================================"
SH4

chmod +x "${BIN_DIR}/termux_paste_guard"

PROFILE_FILE="${HOME}/.bashrc"
if ! grep -q 's43_refactor/bin' "$PROFILE_FILE" 2>/dev/null; then
  {
    echo ''
    echo '# S43 Termux Safe Paste Tools'
    echo 'export PATH="$HOME/s43_refactor/bin:$PATH"'
  } >> "$PROFILE_FILE"
fi

echo
echo "Installed:"
echo "  ${BIN_DIR}/termux_write_file.py"
echo "  ${BIN_DIR}/termux_write_sh"
echo "  ${BIN_DIR}/termux_write_text"
echo "  ${BIN_DIR}/termux_paste_guard"
echo
echo "Run:"
echo "  source ~/.bashrc"
echo
echo "Then use:"
echo "  termux_paste_guard"
echo "  termux_write_sh ~/some_script.sh"
echo "  termux_write_text ~/some_file.txt"
