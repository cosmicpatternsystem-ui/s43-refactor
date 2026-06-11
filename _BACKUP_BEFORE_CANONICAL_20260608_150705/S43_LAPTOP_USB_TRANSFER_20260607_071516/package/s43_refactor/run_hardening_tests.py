#!/usr/bin/env python3
"""
Phase 6 hardening test runner.

Purpose:
- Run only explicitly allowlisted hardening tests.
- Avoid accidental discovery of unrelated/untracked tests.
- Keep s43.py unchanged.
- Provide a stable local/CI entrypoint.
"""

import subprocess
import sys
import unittest

SAFE_TEST_MODULES = [
    "test_status_observability_summary",
    "test_status_observability_wallet_error",
    "test_status_observability_obs_format",
    "test_status_observability_failure_consistency",
    "test_phase7a_status_smoke",
    "test_phase7b_signal_anchor_smoke",
    "test_phase7c_veto_behavior",
]

SAFE_SCRIPT_TESTS = [
    "test_reporting_summary_regression.py",
]

def run_unittest_modules() -> bool:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for module_name in SAFE_TEST_MODULES:
        suite.addTests(loader.loadTestsFromName(module_name))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_script_tests() -> bool:
    ok = True
    for script in SAFE_SCRIPT_TESTS:
        print(f"\n=== running script test: {script} ===", flush=True)
        completed = subprocess.run([sys.executable, script])
        if completed.returncode != 0:
            ok = False
    return ok

def main() -> int:
    unittest_ok = run_unittest_modules()
    script_ok = run_script_tests()
    return 0 if (unittest_ok and script_ok) else 1

if __name__ == "__main__":
    raise SystemExit(main())
