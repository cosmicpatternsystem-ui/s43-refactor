import unittest
from pathlib import Path


class TestPhase7AStatusSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = Path("s43.py").read_text(encoding="utf-8", errors="ignore")

    def test_has_refresh_balance_anchor(self):
        self.assertIn(
            "async def _refresh_balance_if_needed(self, w: WalletRuntime) -> float:",
            self.src,
        )

    def test_has_status_once_anchor(self):
        self.assertIn(
            "async def _status_once() -> None:",
            self.src,
        )

    def test_status_related_tokens_exist(self):
        # smoke-level only; no production behavior change
        tokens = [
            "_refresh_balance_if_needed",
            "_status_once",
        ]
        for token in tokens:
            with self.subTest(token=token):
                self.assertIn(token, self.src)


if __name__ == "__main__":
    unittest.main()
