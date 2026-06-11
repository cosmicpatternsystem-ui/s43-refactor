import asyncio
import importlib
import sys
import time

async def main():
    s43 = importlib.import_module("s43")
    CLS = getattr(s43, "RazTraderEnhanced", None)
    TemporaryPause = getattr(s43, "TemporaryPause", None)
    TradingHalt = getattr(s43, "TradingHalt", None)

    trader = CLS.__new__(CLS)
    
    # Setup necessary mock attributes
    class MockClient:
        def __init__(self, mode): self.mode = mode
        async def request(self, *args, **kwargs):
            if self.mode == "transient":
                raise TemporaryPause("SIMULATED_TRANSIENT", pause_sec=0.1)
            raise RuntimeError("SIMULATED_PERMANENT")

    class Sig:
        def __init__(self):
            self.symbol = "BTCIRT"
            self.action = "buy"
            self.filtered_confidence = 0.95

    signal = Sig()
    # اصلاح ورودی به دیکشنری مطابق خط 9356
    position_size_dict = {"position_size": 1.0}

    # --- Test 1: Transient ---
    trader.api_client = MockClient("transient")
    try:
        await CLS._execute_trade(trader, signal, position_size_dict)
        print("FAIL transient: expected TemporaryPause")
    except TemporaryPause:
        print("PASS transient: TemporaryPause preserved")
    except Exception as e:
        print(f"FAIL transient: got {type(e).__name__}: {e}")

    # --- Test 2: Permanent ---
    trader.api_client = MockClient("permanent")
    try:
        await CLS._execute_trade(trader, signal, position_size_dict)
        print("FAIL permanent: expected TradingHalt")
    except TradingHalt:
        print("PASS permanent: TradingHalt generated")
    except Exception as e:
        print(f"FAIL permanent: got {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
