#!/usr/bin/env bash
set -euo pipefail

BEGIN_MARKER='### BEGIN SHELL ###'
END_MARKER='### END SHELL ###'

AUTO_YES=0
KEEP_FILE=0
QUIET=0
INPUT_FILE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --yes)
      AUTO_YES=1
      ;;
    --keep)
      KEEP_FILE=1
      ;;
    --quiet)
      QUIET=1
      ;;
    -h|--help)
      cat <<HELP
Usage:
  bash safe_paste_runner.sh [--yes] [--keep] [--quiet] [FILE]

Description:
  Extract and run only the shell block between:

    $BEGIN_MARKER
    ...
    $END_MARKER

Options:
  --yes      Run without confirmation
  --keep     Keep extracted temp script file
  --quiet    Reduce output
  -h, --help Show help
HELP
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      printf 'ERROR: unknown option: %s\n' "$1" >&2
      exit 1
      ;;
    *)
      if [ -n "$INPUT_FILE" ]; then
        printf 'ERROR: only one input file is allowed\n' >&2
        exit 1
      fi
      INPUT_FILE="$1"
      ;;
  esac
  shift
done

WORKDIR="${TMPDIR:-$PWD}"
TMP_INPUT="$(mktemp "$WORKDIR/.safe_paste_input_XXXXXX")"
TMP_SCRIPT="$(mktemp "$WORKDIR/.safe_paste_script_XXXXXX.sh")"

trap '
rm -f "$TMP_INPUT"
if [ "'"$KEEP_FILE"'" -eq 0 ]; then
  rm -f "$TMP_SCRIPT"
fi
' EXIT

if [ -n "$INPUT_FILE" ]; then
  if [ ! -f "$INPUT_FILE" ]; then
    printf 'ERROR: input file not found: %s\n' "$INPUT_FILE" >&2
    exit 1
  fi
  cat "$INPUT_FILE" > "$TMP_INPUT"
else
  if [ -t 0 ] && [ "$QUIET" -eq 0 ]; then
    printf 'Paste full input, then press Ctrl-D...\n'
  fi
  cat > "$TMP_INPUT"
fi

if [ ! -s "$TMP_INPUT" ]; then
  printf 'ERROR: no input received\n' >&2
  exit 1
fi

BEGIN_LINE="$(grep -nF "$BEGIN_MARKER" "$TMP_INPUT" | head -n1 | cut -d: -f1 || true)"
END_LINE="$(grep -nF "$END_MARKER" "$TMP_INPUT" | tail -n1 | cut -d: -f1 || true)"

if [ -z "${BEGIN_LINE:-}" ]; then
  printf 'ERROR: begin marker not found: %s\n' "$BEGIN_MARKER" >&2
  exit 1
fi

if [ -z "${END_LINE:-}" ]; then
  printf 'ERROR: end marker not found: %s\n' "$END_MARKER" >&2
  exit 1
fi

if [ "$END_LINE" -le "$BEGIN_LINE" ]; then
  printf 'ERROR: end marker appears before begin marker\n' >&2
  exit 1
fi

START_LINE=$((BEGIN_LINE + 1))
STOP_LINE=$((END_LINE - 1))

if [ "$STOP_LINE" -lt "$START_LINE" ]; then
  printf 'ERROR: shell block is empty\n' >&2
  exit 1
fi

sed -n "${START_LINE},${STOP_LINE}p" "$TMP_INPUT" > "$TMP_SCRIPT"
chmod +x "$TMP_SCRIPT"

if [ "$QUIET" -eq 0 ]; then
  printf '%s\n' '----- extracted shell script -----'
  nl -ba "$TMP_SCRIPT"
  printf '%s\n' '----------------------------------'
fi

if [ "$AUTO_YES" -ne 1 ]; then
  printf 'Execute extracted shell block? [y/N]: '
  read -r ANSWER || true
  case "${ANSWER:-}" in
    y|Y|yes|YES)
      ;;
    *)
      printf 'ERROR: execution cancelled\n' >&2
      exit 1
      ;;
  esac
fi

if command -v bash >/dev/null 2>&1; then
  exec bash "$TMP_SCRIPT"
else
  exec sh "$TMP_SCRIPT"
fi
