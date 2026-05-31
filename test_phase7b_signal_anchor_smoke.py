import unittest
from pathlib import Path


class TestPhase7BSignalAnchorSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = Path("s43.py").read_text(encoding="utf-8", errors="ignore")

    def test_has_signal_class_anchor(self):
        self.assertIn("class Signal:", self.src)

    def test_has_signal_evaluate_anchor(self):
        self.assertIn(
            "def evaluate(self, symbol: str, book: OrderBookTop) -> Signal:",
            self.src,
        )

    def test_has_veto_anchor(self):
        self.assertIn("if float(delta) <= float(veto_thr):", self.src)
        self.assertIn('meta["veto"] = True', self.src)

    def test_has_risk_and_phoenix_anchors(self):
        anchors = [
            "class RiskDecision:",
            "class RiskEscalationLayer:",
            "class PhoenixDecision:",
            "class PhoenixEngine:",
        ]
        for anchor in anchors:
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, self.src)


if __name__ == "__main__":
    unittest.main()
