from pathlib import Path
import re

p = Path("test_phase7c_consumer_nodata_usdtpx_guard.py")
s = p.read_text()

old_block = '''                  cortex=types.SimpleNamespace(
                      entry_multiplier=Mock(
                          return_value=(
                              2.0,
                              {
                                  "veto": True,
                                  "parisa_delta": -0.50,
                                  "parisa_veto_thr": -0.35,
                                  "parisa_contrib": ["stub"],
                              },
                          )
                      )
                  ),'''

new_block = '''                  cortex=types.SimpleNamespace(
                      entry_multiplier=None
                  ),'''

if old_block in s:
    s = s.replace(old_block, new_block)

anchor = '''              w = types.SimpleNamespace(
                  name="test_wallet",
                  dyn_max_notional_frac=1.0,
                  cfg=types.SimpleNamespace(
                      buy_threshold=0.20,
                      sell_threshold=0.20,
                      collective_max_notional_frac=1.0,
                  ),
                  positions={},
                  alpha=types.SimpleNamespace(
                      evaluate=Mock(return_value=sig),
                  ),
                  cortex=types.SimpleNamespace(
                      entry_multiplier=None
                  ),
                  last_engine_status=None,
                  last_engine_reason=None,
                  last_engine_ts=None,
                  last_event=None,
                  sanity_halt=False,
              )'''

replace_anchor = '''              w = types.SimpleNamespace(
                  name="test_wallet",
                  dyn_max_notional_frac=1.0,
                  cfg=types.SimpleNamespace(
                      buy_threshold=0.20,
                      sell_threshold=0.20,
                      collective_max_notional_frac=1.0,
                  ),
                  positions={},
                  alpha=types.SimpleNamespace(
                      evaluate=Mock(return_value=sig),
                  ),
                  cortex=types.SimpleNamespace(
                      entry_multiplier=None
                  ),
                  last_engine_status=None,
                  last_engine_reason=None,
                  last_engine_ts=None,
                  last_event=None,
                  sanity_halt=False,
              )

              entry_multiplier_called = False

              def fake_entry_multiplier(*args, **kwargs):
                  nonlocal entry_multiplier_called
                  entry_multiplier_called = True
                  return 1.0, {}'''

if anchor in s and "entry_multiplier_called = False" not in s:
    s = s.replace(anchor, replace_anchor, 1)

# wire spy after w exists
if 'w.cortex.entry_multiplier = fake_entry_multiplier' not in s:
    s = s.replace(
        '              bot.feed = types.SimpleNamespace(',
        '              w.cortex.entry_multiplier = fake_entry_multiplier\n\n              bot.feed = types.SimpleNamespace(',
        1,
    )

# Make sure test expects NOT called
s = s.replace(
    '                  self.assertTrue(\n'
    '                      w.cortex.entry_multiplier.called,\n'
    '                      "Did not reach PARISA entry_multiplier; "\n'
    '                      f"last_event={getattr(w, \'last_event\', None)!r}, "\n'
    '                      f"last_engine_status={getattr(w, \'last_engine_status\', None)!r}, "\n'
    '                      f"last_engine_reason={getattr(w, \'last_engine_reason\', None)!r}",\n'
    '                  )',
    '                  self.assertFalse(\n'
    '                      entry_multiplier_called,\n'
    '                      "entry_multiplier should not be called on NO_DATA:USDT_PX; "\n'
    '                      f"last_event={getattr(w, \'last_event\', None)!r}, "\n'
    '                      f"last_engine_status={getattr(w, \'last_engine_status\', None)!r}, "\n'
    '                      f"last_engine_reason={getattr(w, \'last_engine_reason\', None)!r}",\n'
    '                  )'
)

# remove duplicate assertion if present
s = s.replace('                  self.assertFalse(entry_multiplier_called)\n', '')

# In nodata path, reject meta should not require veto/parisa payload
s = re.sub(
    r'\n\s*self\.assertIs\(reject_meta\.get\("veto"\), True\)\s*'
    r'\n\s*self\.assertEqual\(reject_meta\.get\("parisa_delta"\), -0\.50\)\s*'
    r'\n\s*self\.assertEqual\(reject_meta\.get\("parisa_veto_thr"\), -0\.35\)\s*'
    r'\n\s*self\.assertEqual\(reject_meta\.get\("parisa_contrib"\), \["stub"\]\)\s*',
    '\n                  self.assertNotEqual(reject_meta.get("reason"), "PARISA_VETO")\n',
    s
)

# In nodata path, collective boost wording should not mention veto
s = s.replace(
    '"COLLECTIVE_BOOST was reached after veto. infos=%r" % info_messages,',
    '"COLLECTIVE_BOOST was reached after NO_DATA:USDT_PX. infos=%r" % info_messages,'
)

# Add explicit missing-USDT fixtures near feed setup
usdt_inject_anchor = '              bot.feed = types.SimpleNamespace(\n                  fetch_spot=_fetch_spot,\n                  _spot_cache={sym: 100.0},\n              )'
usdt_inject_block = '''              bot.feed = types.SimpleNamespace(
                  fetch_spot=_fetch_spot,
                  _spot_cache={sym: 100.0},
              )

              # Force missing USDT price across common aliases/caches.
              bot.usdt_px = None
              bot._usdt_px = None
              bot.last_usdt_px = None
              bot._last_usdt_px = None
              bot.usdt_irt = None
              bot._usdt_irt = None
              bot.feed._spot_cache["USDTIRT"] = None
              bot.feed._spot_cache["USDT"] = None
              bot.feed._spot_cache["USDTTMN"] = None'''

if usdt_inject_anchor in s and "Force missing USDT price across common aliases/caches." not in s:
    s = s.replace(usdt_inject_anchor, usdt_inject_block, 1)

p.write_text(s)
print(f"rewired {p}")
