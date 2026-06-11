import io
import re
import unittest
from contextlib import redirect_stdout

import s43


class StatusObservabilitySummaryTest(unittest.TestCase):
    def test_status_emits_wallet_reporting_summary_observability_event(self):
        out = io.StringIO()

        with redirect_stdout(out):
            s43._run_raz_entry(["--status"], script_path="s43.py")

        text = out.getvalue()

        summary_match = re.search(
            r"summary wallets=(\d+) disabled=(\d+) balance_ok=(\d+) balance_failed=(\d+)",
            text,
        )
        self.assertIsNotNone(
            summary_match,
            "summary line not found in output:\n" + text,
        )

        obs_match = re.search(
            r"OBS event=wallet_reporting_summary wallets=(\d+) disabled=(\d+) balance_ok=(\d+) balance_failed=(\d+)",
            text,
        )
        self.assertIsNotNone(
            obs_match,
            "observability summary event not found in output:\n" + text,
        )

        self.assertEqual(obs_match.groups(), summary_match.groups())


if __name__ == "__main__":
    unittest.main()
