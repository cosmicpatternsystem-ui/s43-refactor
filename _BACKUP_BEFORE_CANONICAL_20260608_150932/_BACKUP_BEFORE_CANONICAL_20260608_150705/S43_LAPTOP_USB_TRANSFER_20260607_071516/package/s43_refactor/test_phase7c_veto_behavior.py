import importlib
import types
import unittest


class TestPhase7CVetoBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s43 = importlib.import_module("s43")
        cls.DecisionCortex = getattr(cls.s43, "DecisionCortex")

    def _make_cortex(self, delta):
        cortex = object.__new__(self.DecisionCortex)

        cortex.cfg = types.SimpleNamespace(
            collective_intelligence=True,
            collective_min_raz_conf=0.50,
            parisa_vote_thr=0.25,
            parisa_veto_thr=-0.35,
            collective_multiplier=2.0,
        )

        def fake_parisa_delta(symbol, book, depth_data=None):
            return float(delta), [("phase7c", "forced_delta")]

        cortex.parisa_delta = fake_parisa_delta
        return cortex

    def _buy_signal(self):
        return types.SimpleNamespace(
            action="BUY",
            confidence=0.95,
        )

    def _book(self):
        return types.SimpleNamespace(
            bid=100.0,
            ask=101.0,
            mid=100.5,
        )

    def test_veto_triggers_when_delta_equals_threshold(self):
        cortex = self._make_cortex(delta=-0.35)

        multiplier, meta = self.DecisionCortex.entry_multiplier(
            cortex,
            "BTCUSDT",
            self._buy_signal(),
            self._book(),
        )

        self.assertEqual(multiplier, 1.0)
        self.assertIs(meta.get("veto"), True)
        self.assertEqual(meta.get("parisa_delta"), -0.35)
        self.assertEqual(meta.get("parisa_veto_thr"), -0.35)
        self.assertIn("parisa_contrib", meta)
        self.assertNotEqual(meta.get("boost"), True)

    def test_veto_triggers_when_delta_below_threshold(self):
        cortex = self._make_cortex(delta=-0.50)

        multiplier, meta = self.DecisionCortex.entry_multiplier(
            cortex,
            "BTCUSDT",
            self._buy_signal(),
            self._book(),
        )

        self.assertEqual(multiplier, 1.0)
        self.assertIs(meta.get("veto"), True)
        self.assertEqual(meta.get("parisa_delta"), -0.50)
        self.assertEqual(meta.get("parisa_veto_thr"), -0.35)
        self.assertIn("parisa_contrib", meta)
        self.assertNotEqual(meta.get("boost"), True)

    def test_positive_delta_still_uses_boost_path_sanity_check(self):
        cortex = self._make_cortex(delta=0.30)

        multiplier, meta = self.DecisionCortex.entry_multiplier(
            cortex,
            "BTCUSDT",
            self._buy_signal(),
            self._book(),
        )

        self.assertEqual(multiplier, 2.0)
        self.assertIs(meta.get("boost"), True)
        self.assertNotEqual(meta.get("veto"), True)
        self.assertEqual(meta.get("parisa_delta"), 0.30)
        self.assertEqual(meta.get("parisa_vote_thr"), 0.25)


if __name__ == "__main__":
    unittest.main()
