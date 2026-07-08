import io
import re
import unittest
from contextlib import redirect_stdout

import s43


class StatusObservabilityObsFormatTest(unittest.TestCase):
    def test_status_obs_lines_have_known_shape(self):
        out = io.StringIO()

        with redirect_stdout(out):
            s43._run_raz_entry(["--status"], script_path="s43.py")

        text = out.getvalue()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        obs_lines = [line for line in lines if line.startswith("OBS ")]

        self.assertTrue(
            obs_lines,
            "Expected at least one OBS line in --status output.\n\nFull output:\n" + text,
        )

        allowed_events = {
            "wallet_reporting_summary",
            "wallet_balance_error",
        }

        seen_summary = 0

        for line in obs_lines:
            event_match = re.search(r"\bevent=([^\s]+)", line)
            self.assertIsNotNone(
                event_match,
                "OBS line is missing event= field:\n" + line + "\n\nFull output:\n" + text,
            )

            event_name = event_match.group(1)
            self.assertIn(
                event_name,
                allowed_events,
                "OBS line contains unexpected event name:\n" + line + "\n\nFull output:\n" + text,
            )

            if event_name == "wallet_reporting_summary":
                seen_summary += 1

                for required_field in ("wallets", "disabled", "balance_ok", "balance_failed"):
                    self.assertRegex(
                        line,
                        rf"\b{required_field}=\d+\b",
                        "wallet_reporting_summary is missing numeric field "
                        + required_field
                        + ":\n"
                        + line
                        + "\n\nFull output:\n"
                        + text,
                    )

            if event_name == "wallet_balance_error":
                self.assertRegex(
                    line,
                    r"\bwallet=([^\s]+)\b",
                    "wallet_balance_error is missing wallet= field:\n"
                    + line
                    + "\n\nFull output:\n"
                    + text,
                )

                self.assertRegex(
                    line,
                    r"\berror_type=([^\s]+)\b",
                    "wallet_balance_error is missing error_type= field:\n"
                    + line
                    + "\n\nFull output:\n"
                    + text,
                )

                self.assertRegex(
                    line,
                    r"\berror_class=([^\s]+)\b",
                    "wallet_balance_error is missing error_class= field:\n"
                    + line
                    + "\n\nFull output:\n"
                    + text,
                )

        self.assertEqual(
            seen_summary,
            1,
            "Expected exactly one wallet_reporting_summary OBS line.\n\nFull output:\n" + text,
        )


if __name__ == "__main__":
    unittest.main()
