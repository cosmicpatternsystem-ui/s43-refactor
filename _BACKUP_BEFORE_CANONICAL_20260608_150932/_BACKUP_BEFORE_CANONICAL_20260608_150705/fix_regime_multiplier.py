from pathlib import Path
import shutil, time

p = Path("s43.py")
bak = Path(f"s43.py.bak_fix_regime_multiplier_{int(time.time())}")
shutil.copy2(p, bak)

lines = p.read_text(encoding="utf-8").splitlines()

start = None
end = None

for i, line in enumerate(lines):
    if line.strip().startswith("def _regime_multiplier("):
        start = i
        break

if start is None:
    raise SystemExit("ERROR: def _regime_multiplier not found")

for j in range(start + 1, min(len(lines), start + 160)):
    if lines[j].strip().startswith("async def place_limit("):
        end = j
        break

if end is None:
    raise SystemExit("ERROR: async def place_limit boundary not found")

replacement = [
    "    def _regime_multiplier(self, symbol: str, notional_irt: float) -> float:",
    "        sym = _canon_symbol(symbol)",
    "        reg = AlphaModel.get_regime(sym)",
    "        st = str(reg.get(\"state\") or \"\").upper()",
    "        strength = float(reg.get(\"strength\") or 0.0)",
    "        mult = 1.0",
    "",
    "        if st == \"VOLATILE\":",
    "            mult *= 0.50",
    "        elif st == \"RANGING\":",
    "            mult *= 0.85",
    "        elif st == \"TRENDING\":",
    "            if strength >= 0.55:",
    "                mult *= 1.10",
    "",
    "        try:",
    "            kf = 1.0",
    "            r = getattr(self, \"_risk\", None)",
    "            mem = getattr(r, \"memory\", None) if r is not None else None",
    "            if mem is not None and hasattr(mem, \"kelly_fraction\"):",
    "                kf = float(mem.kelly_fraction())",
    "            kf = float(clamp(kf, 0.25, 1.25))",
    "            damp = float(0.55 + 0.45 * kf)",
    "            full = float(kf)",
    "            mult *= float(clamp(full / max(1e-9, damp), 0.70, 1.30))",
    "        except Exception:",
    "            pass",
    "",
    "        try:",
    "            spr = float(reg.get(\"spread_bps\") or 0.0)",
    "            max_spr = float(getattr(self.cfg, \"alpha_max_spread_bps\", 35.0) or 35.0)",
    "            if spr > max_spr * 0.75:",
    "                mult *= 0.85",
    "        except Exception:",
    "            pass",
    "",
    "        try:",
    "            mult = float(clamp(mult, 0.30, 1.35))",
    "        except Exception:",
    "            mult = 1.0",
    "",
    "        return float(mult)",
    "",
]

lines[start:end] = replacement

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"patched _regime_multiplier: lines {start+1}..{end}; backup={bak}")
