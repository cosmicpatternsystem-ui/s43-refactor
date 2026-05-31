#!/usr/bin/env python3
"""
Phase 6 hardening test runner.

Purpose:
- Run only explicitly allowlisted hardening tests.
- Avoid accidental discovery of unrelated/untracked tests.
- Keep s43.py unchanged.
- Provide a stable local/CI entrypoint.
"""

import sys
import unittest


SAFE_TEST_MODULES = [
    "test_status_observability_summary",
    "test_status_observability_wallet_error",
    "test_status_observability_obs_format",
    "test_status_observability_failure_consistency",
]


def main() -> int:
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for module_name in SAFE_TEST_MODULES:
        suite.addTests(loader.loadTestsFromName(module_name))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
