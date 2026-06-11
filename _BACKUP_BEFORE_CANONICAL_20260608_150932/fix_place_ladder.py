from pathlib import Path
import shutil, time

p = Path("s43.py")
bak = Path(f"s43.py.bak_fix_place_ladder_{int(time.time())}")
shutil.copy2(p, bak)

lines = p.read_text(encoding="utf-8").splitlines()

start = None
end = None

for i, line in enumerate(lines):
    if line.startswith("    async def place_ladder("):
        start = i
        break

if start is None:
    raise SystemExit("ERROR: place_ladder start not found")

for j in range(start + 1, min(len(lines), start + 220)):
    if lines[j].startswith("    async def deep_prune_ghost_orders("):
        end = j
        break

if end is None:
    raise SystemExit("ERROR: deep_prune_ghost_orders boundary not found")

replacement = [
    "    async def place_ladder(self, symbol: str, side: str, qty: float, base_price: float, notional_irt: float) -> dict:",
    "        sym = _canon_symbol(symbol)",
    "        steps = int(getattr(self.cfg, \"ladder_steps\", 1) or 1)",
    "",
    "        if not bool(getattr(self.cfg, \"laddering\", False)) or steps <= 1:",
    "            return await self.place_limit(sym, side, qty, base_price, notional_irt)",
    "",
    "        bps = float(getattr(self.cfg, \"ladder_bps\", 0.0) or 0.0)",
    "        pause_ms = int(getattr(self.cfg, \"ladder_pause_ms\", 0) or 0)",
    "",
    "        if qty <= 0 or base_price <= 0:",
    "            raise ValueError(f\"Invalid ladder params qty={qty} base_price={base_price}\")",
    "",
    "        child_orders = []",
    "        remaining = float(qty)",
    "",
    "        for i in range(steps):",
    "            q_i = remaining if i == steps - 1 else remaining / float(steps - i)",
    "            remaining -= q_i",
    "",
    "            step_bps = (bps * float(i)) / 10000.0",
    "            px_i = (",
    "                base_price * (1.0 - step_bps)",
    "                if str(side).lower() == \"buy\"",
    "                else base_price * (1.0 + step_bps)",
    "            )",
    "",
    "            resp = await self.place_limit(",
    "                sym,",
    "                side,",
    "                q_i,",
    "                px_i,",
    "                (notional_irt * (q_i / max(qty, 1e-12)))",
    "            )",
    "            child_orders.append(resp)",
    "",
    "            if pause_ms > 0 and i < steps - 1:",
    "                await asyncio.sleep(pause_ms / 1000.0)",
    "",
    "        any_sent = False",
    "        all_good = True",
    "        all_dup = True",
    "",
    "        for o in (child_orders or []):",
    "            if not isinstance(o, dict):",
    "                all_good = False",
    "                all_dup = False",
    "                continue",
    "",
    "            ok0 = bool(o.get(\"ok\"))",
    "            if not ok0:",
    "                try:",
    "                    ok0 = int(float(o.get(\"status\") or o.get(\"code\") or 0)) in (200, 201)",
    "                except Exception:",
    "                    ok0 = False",
    "",
    "            dup0 = bool(o.get(\"skipped\")) and str(o.get(\"reason\") or \"\").upper() == \"DUPLICATE_PREVENTED\"",
    "",
    "            if ok0:",
    "                any_sent = True",
    "                all_dup = False",
    "            elif dup0:",
    "                pass",
    "            else:",
    "                all_good = False",
    "                all_dup = False",
    "",
    "        if child_orders and all_dup:",
    "            return {",
    "                \"ok\": False,",
    "                \"skipped\": True,",
    "                \"reason\": \"DUPLICATE_PREVENTED\",",
    "                \"ladder\": True,",
    "                \"steps\": steps,",
    "                \"children\": child_orders,",
    "            }",
    "",
    "        ok = bool(all_good and any_sent)",
    "        return {\"ok\": ok, \"ladder\": True, \"steps\": steps, \"children\": child_orders}",
]

lines[start:end] = replacement

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"patched place_ladder: lines {start+1}..{end}; backup={bak}")
