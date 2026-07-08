import unittest

import intelligence.strategies
from intelligence.strategies.registry import StrategyRegistry


class StrategyRegistryTests(unittest.TestCase):
    def test_list_strategies_contains_builtin_strategies(self):
        strategies = StrategyRegistry.list_strategies()
        self.assertIn("sma_strategy", strategies)
        self.assertIn("momentum_strategy", strategies)

    def test_get_strategy_returns_registered_instance(self):
        strategy = StrategyRegistry.get_strategy("momentum_strategy")
        self.assertEqual(strategy.name(), "momentum_strategy")

    def test_get_strategy_raises_for_unknown_strategy(self):
        with self.assertRaises(ValueError):
            StrategyRegistry.get_strategy("unknown_strategy")


class MomentumStrategyTests(unittest.TestCase):
    def setUp(self):
        self.strategy = StrategyRegistry.get_strategy("momentum_strategy")

    def test_execute_returns_buy_for_upward_momentum(self):
        result = self.strategy.execute([{"price": 100.0}, {"price": 120.0}])
        self.assertEqual(result["signal"], "buy")
        self.assertEqual(result["status"], "ok")

    def test_execute_returns_sell_for_downward_momentum(self):
        result = self.strategy.execute([{"price": 120.0}, {"price": 100.0}])
        self.assertEqual(result["signal"], "sell")
        self.assertEqual(result["status"], "ok")

    def test_execute_returns_hold_for_flat_momentum(self):
        result = self.strategy.execute([{"price": 100.0}, {"price": 100.0}])
        self.assertEqual(result["signal"], "hold")
        self.assertEqual(result["status"], "ok")

    def test_execute_returns_hold_for_empty_data(self):
        result = self.strategy.execute([])
        self.assertEqual(result["signal"], "hold")
        self.assertEqual(result["reason"], "no_data")
        self.assertEqual(result["status"], "ok")


if __name__ == "__main__":
    unittest.main()
