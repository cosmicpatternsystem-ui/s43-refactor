from pathlib import Path
import re

p = Path("test_phase7c_consumer_nodata_usdtpx_guard.py")
s = p.read_text()

# 1) rename test function
s = s.replace(
    "def test_consumer_parisa_veto_sets_hold_rejects_and_returns_before_collective_boost(",
    "def test_consumer_nodata_usdtpx_sets_hold_rejects_and_returns_before_entry_multiplier(",
)

# 2) replace reason code
s = s.replace('"PARISA_VETO"', '"NO_DATA:USDT_PX"')
s = s.replace("'PARISA_VETO'", "'NO_DATA:USDT_PX'")

# 3) status Run -> Hold where applicable
s = s.replace('assert last_engine_status == "Run"', 'assert last_engine_status == "Hold"')
s = s.replace("assert last_engine_status == 'Run'", "assert last_engine_status == 'Hold'")
s = s.replace('self.assertEqual(w.last_engine_status, "Run")', 'self.assertEqual(w.last_engine_status, "Hold")')
s = s.replace("self.assertEqual(w.last_engine_status, 'Run')", "self.assertEqual(w.last_engine_status, 'Hold')")

# 4) neutralize veto payload if any obvious veto-return exists
s = re.sub(
    r"return\s+([0-9.]+|\([^)]*\))\s*,\s*\{[^{}]*[\"']veto[\"']\s*:\s*True[^{}]*\}",
    "return 1.0, {}",
    s,
)

# 5) add simple spy around entry_multiplier monkeypatch if pattern exists
needle = "w.cortex.entry_multiplier = fake_entry_multiplier"
if needle in s and "entry_multiplier_called = False" not in s:
    s = s.replace(
        needle,
        "entry_multiplier_called = False\n\n"
        "                def fake_entry_multiplier(*args, **kwargs):\n"
        "                    nonlocal entry_multiplier_called\n"
        "                    entry_multiplier_called = True\n"
        "                    return 1.0, {}\n\n"
        "                w.cortex.entry_multiplier = fake_entry_multiplier",
        1,
    )

# 6) add assertion before unittest.main or EOF
if "assert entry_multiplier_called is False" not in s:
    m = re.search(r"\nif __name__ == ['\"]__main__['\"]:\s*\n\s*unittest\.main\(\)\s*$", s)
    if m:
        s = s[:m.start()] + "\n                self.assertFalse(entry_multiplier_called)\n\n" + s[m.start():]
    else:
        s += "\n                self.assertFalse(entry_multiplier_called)\n"

# 7) attempt to invalidate simple USDT literals/assignments
patterns = [
    (r'(^\s*[A-Za-z0-9_]*USDT[A-Za-z0-9_]*\s*=\s*)[0-9][^\n]*$', r'\1None'),
    (r'(^\s*[A-Za-z0-9_]*usdt[A-Za-z0-9_]*\s*=\s*)[0-9][^\n]*$', r'\1None'),
    (r'(^\s*["\']?USDT["\']?\s*:\s*)[0-9][^\n,}]*', r'\1None'),
    (r'(^\s*["\']?usdt["\']?\s*:\s*)[0-9][^\n,}]*', r'\1None'),
]
for pat, repl in patterns:
    ns = re.sub(pat, repl, s, flags=re.M)
    if ns != s:
        s = ns

p.write_text(s)
print(f"patched {p}")
