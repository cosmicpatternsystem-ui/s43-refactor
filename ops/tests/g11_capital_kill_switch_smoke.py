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

try:
    engine._g11_pre_submit_guard(
        "USDTIRT",
        "BUY",
        1.0,
        1.0,
        500_000_001.0,
        from_wallet="wallet_A",
        to_wallet="wallet_B",
    )
    raise SystemExit("FAILED: expected TradingHalt for oversized order")
except s43.TradingHalt as exc:
    print(f"HALTED: {exc}")

    if "G11_CAPITAL_PROTECTION" not in str(exc):
        raise SystemExit(f"FAILED: unexpected halt reason: {exc}")

    print("OK: CapitalKillSwitch halted oversized order")
    raise SystemExit(0)
