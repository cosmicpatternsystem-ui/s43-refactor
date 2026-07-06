import re
import unittest


def _status_output_with_non_disabled_wallet_failure():
    return "\n".join(
        [
            "OBS event=status_summary wallets=1 failed_wallets=1 disabled_wallets=0",
            "wallet=primary balance_ok=0 disabled=0 balance_error_type=timeout balance_error_class=RuntimeError",
            "OBS event=wallet_balance_error wallet=primary error_type=timeout error_class=RuntimeError",
        ]
    ) + "\n"


class StatusObservabilityFailureConsistencyTest(unittest.TestCase):
    def test_failed_non_disabled_wallets_have_matching_obs_error_events(self):
        text = _status_output_with_non_disabled_wallet_failure()
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

        self.assertTrue(
            failed_wallets,
            "deterministic fixture must contain a non-disabled wallet balance failure",
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