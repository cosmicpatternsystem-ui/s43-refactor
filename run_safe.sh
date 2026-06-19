#!/usr/bin/env bash

set -u

cd "$(dirname "$0")" || exit 1

usage() {
  cat <<'EOF'
Usage:
  bash run_safe.sh start      Run healthcheck, then start s43.py
  bash run_safe.sh hardening  Run allowlisted hardening tests
  bash run_safe.sh policy     Run policy/roadmap smoke checks
  bash run_safe.sh release    Run release readiness contract checks
  bash run_safe.sh all        Run hardening, policy, and release gates
EOF
}

check_file() {
  if [ ! -f "$1" ]; then
    echo "FAIL: required file missing: $1"
    return 1
  fi
}

python_cmd() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    echo "python"
    return 0
  fi

  echo "FAIL: neither python3 nor python was found" >&2
  return 1
}

run_start() {
  ./arzplus_healthcheck.sh
  status=$?

  if [ "$status" -ne 0 ]; then
    echo ""
    echo "STOP: healthcheck failed, s43.py will not start."
    return 1
  fi

  echo ""
  echo "Starting s43.py..."
  py="$(python_cmd)" || return 1
  "$py" s43.py
}

run_hardening() {
  py="$(python_cmd)" || return 1
  "$py" run_hardening_tests.py
}

run_policy() {
  check_file "S43_ROADMAP_CHANGE_CONTROL_POLICY.md" || return 1
  check_file "S43_ROADMAP_DECISION_LOG.md" || return 1

  if [ ! -f "ROADMAP_vNEXT.md" ] && [ ! -f "ROADMAP_CANONICAL.md" ]; then
    echo "FAIL: required roadmap file missing: ROADMAP_vNEXT.md or ROADMAP_CANONICAL.md"
    return 1
  fi
}

run_release() {
  check_file "S43_ROADMAP_CHANGE_CONTROL_POLICY.md" || return 1
  check_file "S43_ROADMAP_DECISION_LOG.md" || return 1
  check_file "run_hardening_tests.py" || return 1
  check_file ".github/workflows/hardening-tests.yml" || return 1
  check_file ".github/workflows/policy-smokes.yml" || return 1
  check_file ".github/workflows/release-readiness.yml" || return 1
}

run_all() {
  run_hardening || return 1
  run_policy || return 1
  run_release || return 1
}

command="${1:-start}"

case "$command" in
  start)
    run_start
    ;;
  hardening)
    run_hardening
    ;;
  policy)
    run_policy
    ;;
  release)
    run_release
    ;;
  all)
    run_all
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "FAIL: unknown command: $command"
    echo ""
    usage
    exit 2
    ;;
esac
