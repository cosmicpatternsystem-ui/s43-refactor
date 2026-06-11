from pathlib import Path

p = Path("s43.py")
src = p.read_text(encoding="utf-8")
lines = src.splitlines(keepends=True)

changed = 0

# ------------------------------------------------------------
# Part 1: Patch portfolio DASH_PORTFOLIO_BALANCE raise only
# ------------------------------------------------------------
target = 'raise TradingHalt("BALANCE_FETCH_FAILED: DASH_PORTFOLIO_BALANCE") from e'
hits = [i for i, line in enumerate(lines) if target in line]

if len(hits) != 1:
    raise SystemExit(f"PATCH13_3_FAIL: expected exactly 1 DASH_PORTFOLIO_BALANCE raise, found {len(hits)}")

i = hits[0]
indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]

replacement = [
    f'{indent}try:\n',
    f'{indent}    logging.warning(\n',
    f'{indent}        "ISOCHK_GLOBAL phase=portfolio_data err=%s",\n',
    f'{indent}        f"{{type(e).__name__}}: {{e}}",\n',
    f'{indent}    )\n',
    f'{indent}except Exception:\n',
    f'{indent}    pass\n',
    f'{indent}return {{\n',
    f'{indent}    "capital": 0.0,\n',
    f'{indent}    "exposure": 0.0,\n',
    f'{indent}    "positions": []\n',
    f'{indent}}}\n',
]

lines[i:i+1] = replacement
changed += 1

# Rebuild after part 1
src = ''.join(lines)
lines = src.splitlines(keepends=True)

# ------------------------------------------------------------
# Part 2: Locate _refresh_balance_if_needed function boundaries
# ------------------------------------------------------------
def_line = None
for idx, line in enumerate(lines):
    if line.startswith("    async def _refresh_balance_if_needed(self, w: WalletRuntime) -> float:"):
        def_line = idx
        break

if def_line is None:
    raise SystemExit("PATCH13_3_FAIL: _refresh_balance_if_needed function header not found")

# Function ends at next class-level method: line starting with exactly 4 spaces + def/async def
end_line = None
for idx in range(def_line + 1, len(lines)):
    line = lines[idx]
    if line.startswith("    def ") or line.startswith("    async def "):
        end_line = idx
        break

if end_line is None:
    raise SystemExit("PATCH13_3_FAIL: could not locate end of _refresh_balance_if_needed")

func = lines[def_line:end_line]
func_text = ''.join(func)

# Safety: ensure target raises exist inside this function before patch
required_inside = [
    'raise TradingHalt(f"BALANCE_FETCH_FAILED: TRANSIENT: {type(e).__name__}:{e}") from e',
    'raise TradingHalt(f"BALANCE_FETCH_FAILED: HTTP_FAIL: {type(e).__name__}:{e}") from e',
    'raise TradingHalt(f"BALANCE_FETCH_FAILED: API_FAIL: {type(e).__name__}:{e}") from e',
    'raise TradingHalt("BALANCE_FETCH_FAILED: EXC") from e',
    'raise TradingHalt("BALANCE_FETCH_FAILED: ARZPLUS_FAST_PARSE_FAIL") from e',
    'else: raise TradingHalt("BALANCE_FETCH_FAILED: PARSE_OK_FALSE")',
]

for s in required_inside:
    if s not in func_text:
        raise SystemExit(f"PATCH13_3_FAIL: target not found inside _refresh_balance_if_needed:\n{s}")

# ------------------------------------------------------------
# Part 3: Inject helper after now = time.time()
# ------------------------------------------------------------
if "_balance_refresh_degraded(" not in func_text:
    injected = False
    for j, line in enumerate(func):
        if line.strip() == "now = time.time()":
            indent_now = line[:len(line) - len(line.lstrip())]
            helper_indent = indent_now
            body_indent = helper_indent + "    "
            helper = [
                f'{helper_indent}def _balance_refresh_degraded(reason: str) -> float:\n',
                f'{body_indent}try:\n',
                f'{body_indent}    w.last_balance_ok = False\n',
                f'{body_indent}except Exception:\n',
                f'{body_indent}    pass\n',
                f'{body_indent}try:\n',
                f'{body_indent}    w.last_balance_ts = now\n',
                f'{body_indent}except Exception:\n',
                f'{body_indent}    pass\n',
                f'{body_indent}try:\n',
                f'{body_indent}    w.last_balance_err = str(reason)[:300]\n',
                f'{body_indent}except Exception:\n',
                f'{body_indent}    pass\n',
                f'{body_indent}try:\n',
                f'{body_indent}    self._log.warning("event=BALANCE_REFRESH_DEGRADED wallet=%s reason=%s", getattr(w, "name", None), str(reason)[:300])\n',
                f'{body_indent}except Exception:\n',
                f'{body_indent}    pass\n',
                f'{body_indent}return float(getattr(w, "cash_irt", 0.0) or 0.0)\n',
            ]
            func[j+1:j+1] = helper
            injected = True
            changed += 1
            break
    if not injected:
        raise SystemExit("PATCH13_3_FAIL: now = time.time() not found for helper injection")
else:
    print("PATCH13_3_INFO: helper already present, skipping injection")

# ------------------------------------------------------------
# Part 4: Replace target raises only inside this function
# ------------------------------------------------------------
func_text = ''.join(func)

replace_pairs = [
    (
        'raise TradingHalt(f"BALANCE_FETCH_FAILED: TRANSIENT: {type(e).__name__}:{e}") from e',
        'return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: TRANSIENT: {type(e).__name__}:{e}")',
    ),
    (
        'raise TradingHalt(f"BALANCE_FETCH_FAILED: HTTP_FAIL: {type(e).__name__}:{e}") from e',
        'return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: HTTP_FAIL: {type(e).__name__}:{e}")',
    ),
    (
        'raise TradingHalt(f"BALANCE_FETCH_FAILED: API_FAIL: {type(e).__name__}:{e}") from e',
        'return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: API_FAIL: {type(e).__name__}:{e}")',
    ),
    (
        'raise TradingHalt("BALANCE_FETCH_FAILED: EXC") from e',
        'return _balance_refresh_degraded("BALANCE_FETCH_FAILED: EXC")',
    ),
    (
        'raise TradingHalt("BALANCE_FETCH_FAILED: ARZPLUS_FAST_PARSE_FAIL") from e',
        'return _balance_refresh_degraded("BALANCE_FETCH_FAILED: ARZPLUS_FAST_PARSE_FAIL")',
    ),
    (
        'else: raise TradingHalt("BALANCE_FETCH_FAILED: PARSE_OK_FALSE")',
        'else: return _balance_refresh_degraded("BALANCE_FETCH_FAILED: PARSE_OK_FALSE")',
    ),
]

for old, new in replace_pairs:
    count = func_text.count(old)
    if count < 1:
        raise SystemExit(f"PATCH13_3_FAIL: replacement target disappeared:\n{old}")
    func_text = func_text.replace(old, new)
    changed += count

new_func = func_text.splitlines(keepends=True)

# Put patched function back
lines[def_line:end_line] = new_func

out = ''.join(lines)
p.write_text(out, encoding="utf-8")

print(f"PATCH13_3_OK changed_units={changed}")
print("PATCH13_3_NOTE: patched portfolio_data and _refresh_balance_if_needed only")
