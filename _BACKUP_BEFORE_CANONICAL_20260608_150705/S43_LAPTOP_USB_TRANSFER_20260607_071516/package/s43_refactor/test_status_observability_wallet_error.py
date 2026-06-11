import io
import re
import unittest
from contextlib import redirect_stdout

import s43


class StatusObservabilityWalletErrorTest(unittest.TestCase):
    def test_failed_non_disabled_wallet_emits_wallet_balance_error_event(self):
        out = io.StringIO()

        with redirect_stdout(out):
            s43._run_raz_entry(["--status"], script_path="s43.py")

        text = out.getvalue()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        wallet_failures = []
        obs_events = []

        for line in lines:
            if line.startswith("wallet="):
                wallet_match = re.search(r"\bwallet=([^\s]+)", line)
                if not wallet_match:
                    continue

                wallet_name = wallet_match.group(1)
                is_disabled = bool(re.search(r"\bdisabled=1\b", line))
                is_failed = bool(re.search(r"\bbalance_ok=0\b", line))

                if is_failed and not is_disabled:
                    error_type_match = re.search(r"\bbalance_error_type=([^\s]+)", line)
                    error_class_match = re.search(r"\bbalance_error_class=([^\s]+)", line)

                    wallet_failures.append(
                        {
                            "wallet": wallet_name,
                            "line": line,
                            "error_type": error_type_match.group(1) if error_type_match else "",
                            "error_class": error_class_match.group(1) if error_class_match else "",
                        }
                    )

            if line.startswith("OBS event=wallet_balance_error"):
                wallet_match = re.search(r"\bwallet=([^\s]+)", line)
                error_type_match = re.search(r"\berror_type=([^\s]*)", line)
                error_class_match = re.search(r"\berror_class=([^\s]*)", line)

                obs_events.append(
                    {
                        "wallet": wallet_match.group(1) if wallet_match else "",
                        "line": line,
                        "error_type": error_type_match.group(1) if error_type_match else "",
                        "error_class": error_class_match.group(1) if error_class_match else "",
                    }
                )

        if not wallet_failures:
            self.skipTest(
                "No non-disabled wallet balance failure observed in this runtime status output."
            )

        obs_by_wallet = {}
        for event in obs_events:
            obs_by_wallet.setdefault(event["wallet"], []).append(event)

        missing = []
        mismatched = []

        for failure in wallet_failures:
            wallet_name = failure["wallet"]
            wallet_events = obs_by_wallet.get(wallet_name, [])

            if not wallet_events:
                missing.append(failure)
                continue

            if failure["error_type"]:
                if not any(event["error_type"] == failure["error_type"] for event in wallet_events):
                    mismatched.append(
                        {
                            "wallet": wallet_name,
                            "expected_error_type": failure["error_type"],
                            "events": wallet_events,
                            "wallet_line": failure["line"],
                        }
                    )

            if failure["error_class"]:
                if not any(event["error_class"] == failure["error_class"] for event in wallet_events):
                    mismatched.append(
                        {
                            "wallet": wallet_name,
                            "expected_error_class": failure["error_class"],
                            "events": wallet_events,
                            "wallet_line": failure["line"],
                        }
                    )

        self.assertFalse(
            missing,
            "Missing OBS wallet_balance_error event for failed wallets:\n"
            + "\n".join(item["line"] for item in missing)
            + "\n\nFull output:\n"
            + text,
        )

        self.assertFalse(
            mismatched,
            "OBS wallet_balance_error event metadata mismatch:\n"
            + repr(mismatched)
            + "\n\nFull output:\n"
            + text,
        )


if __name__ == "__main__":
    unittest.main()
