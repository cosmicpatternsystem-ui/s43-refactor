from pathlib import Path
import re

p = Path("test_phase7c_consumer_nodata_usdtpx_guard.py")
s = p.read_text()

# 1) remove wrongly injected top-level/class-level assertion lines
s = re.sub(r'^\s*self\.assertFalse\(entry_multiplier_called\)\s*$', '', s, flags=re.M)

# 2) normalize remaining PARISA_VETO mentions to NO_DATA:USDT_PX
s = s.replace("event=PARISA_VETO", "event=NO_DATA:USDT_PX")
s = s.replace("PARISA_VETO warning log was not emitted.", "NO_DATA:USDT_PX warning log was not emitted.")
s = s.replace("consumer-side PARISA_VETO", "consumer-side NO_DATA:USDT_PX")

# 3) insert the assertion inside the test method, ideally before finally:
target_def = "def test_consumer_nodata_usdtpx_sets_hold_rejects_and_returns_before_entry_multiplier("
if "self.assertFalse(entry_multiplier_called)" not in s and target_def in s:
    m_def = s.find(target_def)
    m_finally = s.find("\n            finally:", m_def)
    if m_finally != -1:
        s = s[:m_finally] + "\n                self.assertFalse(entry_multiplier_called)\n" + s[m_finally:]
    else:
        # fallback: insert after last known reason assertion in the test
        anchor = 'self.assertEqual(w.last_engine_reason, "NO_DATA:USDT_PX")'
        pos = s.find(anchor, m_def)
        if pos != -1:
            line_end = s.find("\n", pos)
            s = s[:line_end+1] + "                self.assertFalse(entry_multiplier_called)\n" + s[line_end+1:]

p.write_text(s)
print(f"fixed {p}")
