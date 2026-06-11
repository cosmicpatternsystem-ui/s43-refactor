import io
import re
import unittest
from contextlib import redirect_stdout

import s43


class StatusObservabilityFailureConsistencyTest(unittest.TestCase):
    def test_failed_non_disabled_wallets_have_matching_obs_error_events(self):
        out = io.StringIO()
        with redirect_stdout(out):
            s43._run_raz_entry(["--status"], script_path="s43.py")

        text = out.getvalue()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        failed_wallets = []
        obs_error_wallets = set()

        for line in lines:
            if line.startswith("wallet="):
                wallet_match = re.search(r"\bwallet=([^\s]+)", line)
                if not wallet_match:
                    continue

                wallet_name = wallet_match.group(1)
                is_disabled = bool(re.search(r"\bdisabled=1\b", line))
                is_failed = bool(re.search(r"\bbalance_ok=0\b", line))

                if is_failed and not is_disabled:
                    failed_wallets.append(
                        {
                            "wallet": wallet_name,
                            "line": line,
                        }
                    )

            if line.startswith("OBS event=wallet_balance_error"):
                wallet_match = re.search(r"\bwallet=([^\s]+)", line)
                if wallet_match:
                    obs_error_wallets.add(wallet_match.group(1))

        if not failed_wallets:
            self.skipTest(
                "No non-disabled wallet balance failure observed in this runtime status output."
            )

        missing = [
            item for item in failed_wallets if item["wallet"] not in obs_error_wallets
        ]

        self.assertFalse(
            missing,
            "Observed non-disabled wallet failure without matching OBS wallet_balance_error event:\n"
            + "\n".join(item["line"] for item in missing)
            + "\n\nFull output:\n"
            + text,
        )


if __name__ == "__main__":
    unittest.main()
