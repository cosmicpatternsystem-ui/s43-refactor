from intelligence.backtester import Backtester

bt = Backtester()
result = bt.run_strategy("sma_strategy")
print(f"Backtest Result: {result}")
