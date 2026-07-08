import importlib.util
import sys
import types

ga = types.ModuleType("governance_audit")
ga.audit_event = lambda n, p=None: print(f"AUDIT: {n} | {p}")
ga.audit_exception = lambda n, e=None, p=None: None
ga.mask_sensitive_text = lambda v: v
sys.modules["governance_audit"] = ga

spec = importlib.util.spec_from_file_location("s43", "s43.py")
s43 = importlib.util.module_from_spec(spec)
sys.modules["s43"] = s43
spec.loader.exec_module(s43)

engine = s43.ExecutionEngine.__new__(s43.ExecutionEngine)
engine._g11_safety_gates_enabled = True
engine._g11_wallet_cycle_guard = {"enabled": True, "window": 10, "max_repeats": 3}
engine._g11_wallet_history = []

kwargs = {
    "from_wallet": "wallet_A",
    "to_wallet": "wallet_B",
}

for i in range(1, 6):
    try:
        engine._g11_pre_submit_guard("USDTIRT", "BUY", 10.0, 100000.0, 1000000.0, **kwargs)
        print(f"attempt {i}: PASS")
    except s43.TradingHalt as exc:
        print(f"attempt {i}: HALTED: {exc}")
        raise SystemExit(0)

raise SystemExit("FAILED: expected TradingHalt but guard never triggered")
