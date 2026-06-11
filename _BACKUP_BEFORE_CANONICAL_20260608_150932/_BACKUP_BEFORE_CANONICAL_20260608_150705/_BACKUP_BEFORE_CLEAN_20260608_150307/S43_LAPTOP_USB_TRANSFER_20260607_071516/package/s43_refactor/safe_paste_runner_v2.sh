#!/usr/bin/env bash
set -euo pipefail

BEGIN_MARKER='### BEGIN SHELL ###'
END_MARKER='### END SHELL ###'

AUTO_YES=0
KEEP_FILE=0
QUIET=0
DRY_RUN=0
PRINT_ONLY=0
STRICT_SINGLE_BLOCK=0
SHOW_METADATA=0
TIMEOUT_SEC=""
INPUT_FILE=""
SAVE_PATH=""
LOG_PATH=""

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
    --dry-run)
      DRY_RUN=1
      ;;
    --print-only|--no-exec)
      PRINT_ONLY=1
      ;;
    --strict-single-block)
      STRICT_SINGLE_BLOCK=1
      ;;
    --show-metadata)
      SHOW_METADATA=1
      ;;
    --save)
      shift
      if [ "$#" -eq 0 ]; then
        printf 'ERROR: --save requires a file path\n' >&2
        exit 1
      fi
      SAVE_PATH="$1"
      ;;
    --log)
      shift
      if [ "$#" -eq 0 ]; then
        printf 'ERROR: --log requires a file path\n' >&2
        exit 1
      fi
      LOG_PATH="$1"
      ;;
    --timeout)
      shift
      if [ "$#" -eq 0 ]; then
        printf 'ERROR: --timeout requires seconds\n' >&2
        exit 1
      fi
      TIMEOUT_SEC="$1"
      case "$TIMEOUT_SEC" in
        ''|*[!0-9]*)
          printf 'ERROR: --timeout must be a non-negative integer\n' >&2
          exit 1
          ;;
      esac
      ;;
    -h|--help)
      cat <<HELP
Usage:
  bash safe_paste_runner_v2.sh [options] [FILE]

Description:
  Extract and process only the shell block between:

    $BEGIN_MARKER
    ...
    $END_MARKER

Options:
  --yes                  Run without confirmation
  --keep                 Keep extracted temp script file
  --quiet                Reduce output
  --dry-run              Validate and preview, do not execute
  --print-only           Print extracted block, do not execute
  --no-exec              Alias for --print-only
  --save FILE            Save extracted script to FILE
  --log FILE             Append runtime output to FILE
  --timeout SEC          Run command with timeout in seconds
  --strict-single-block  Require exactly one begin and one end marker
  --show-metadata        Print metadata summary
  -h, --help             Show help
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

BEGIN_COUNT="$(grep -cF "$BEGIN_MARKER" "$TMP_INPUT" || true)"
END_COUNT="$(grep -cF "$END_MARKER" "$TMP_INPUT" || true)"

BEGIN_LINE="$(grep -nF "$BEGIN_MARKER" "$TMP_INPUT" | head -n1 | cut -d: -f1 || true)"
END_LINE="$(grep -nF "$END_MARKER" "$TMP_INPUT" | tail -n1 | cut -d: -f1 || true)"

if [ "$STRICT_SINGLE_BLOCK" -eq 1 ]; then
  if [ "${BEGIN_COUNT:-0}" -ne 1 ]; then
    printf 'ERROR: strict mode requires exactly one begin marker, found: %s\n' "${BEGIN_COUNT:-0}" >&2
    exit 1
  fi
  if [ "${END_COUNT:-0}" -ne 1 ]; then
    printf 'ERROR: strict mode requires exactly one end marker, found: %s\n' "${END_COUNT:-0}" >&2
    exit 1
  fi
fi

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

SCRIPT_LINES="$(wc -l < "$TMP_SCRIPT" | tr -d ' ')"
SCRIPT_BYTES="$(wc -c < "$TMP_SCRIPT" | tr -d ' ')"

if command -v sha256sum >/dev/null 2>&1; then
  SCRIPT_SHA256="$(sha256sum "$TMP_SCRIPT" | awk '{print $1}')"
else
  SCRIPT_SHA256="unavailable"
fi

if [ -n "$SAVE_PATH" ]; then
  cp -f "$TMP_SCRIPT" "$SAVE_PATH"
  chmod +x "$SAVE_PATH" || true
fi

if [ "$QUIET" -eq 0 ]; then
  printf '%s\n' '----- extracted shell script -----'
  nl -ba "$TMP_SCRIPT"
  printf '%s\n' '----------------------------------'
fi

if [ "$SHOW_METADATA" -eq 1 ]; then
  printf 'Metadata:\n'
  printf '  begin_marker_count: %s\n' "${BEGIN_COUNT:-0}"
  printf '  end_marker_count:   %s\n' "${END_COUNT:-0}"
  printf '  begin_line:         %s\n' "${BEGIN_LINE:-}"
  printf '  end_line:           %s\n' "${END_LINE:-}"
  printf '  script_lines:       %s\n' "$SCRIPT_LINES"
  printf '  script_bytes:       %s\n' "$SCRIPT_BYTES"
  printf '  script_sha256:      %s\n' "$SCRIPT_SHA256"
  if [ -n "$SAVE_PATH" ]; then
    printf '  saved_to:           %s\n' "$SAVE_PATH"
  fi
  if [ -n "$LOG_PATH" ]; then
    printf '  log_file:           %s\n' "$LOG_PATH"
  fi
  if [ -n "$TIMEOUT_SEC" ]; then
    printf '  timeout_sec:        %s\n' "$TIMEOUT_SEC"
  fi
fi

if [ "$DRY_RUN" -eq 1 ] || [ "$PRINT_ONLY" -eq 1 ]; then
  exit 0
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

RUNNER_SHELL="sh"
if command -v bash >/dev/null 2>&1; then
  RUNNER_SHELL="bash"
fi

if [ -n "$TIMEOUT_SEC" ] && [ "$TIMEOUT_SEC" -gt 0 ]; then
  if command -v timeout >/dev/null 2>&1; then
    if [ -n "$LOG_PATH" ]; then
      exec timeout "$TIMEOUT_SEC" "$RUNNER_SHELL" "$TMP_SCRIPT" 2>&1 | tee -a "$LOG_PATH"
    else
      exec timeout "$TIMEOUT_SEC" "$RUNNER_SHELL" "$TMP_SCRIPT"
    fi
  else
    printf 'ERROR: timeout command is not available on this system\n' >&2
    exit 1
  fi
else
  if [ -n "$LOG_PATH" ]; then
    exec "$RUNNER_SHELL" "$TMP_SCRIPT" 2>&1 | tee -a "$LOG_PATH"
  else
    exec "$RUNNER_SHELL" "$TMP_SCRIPT"
  fi
fi
