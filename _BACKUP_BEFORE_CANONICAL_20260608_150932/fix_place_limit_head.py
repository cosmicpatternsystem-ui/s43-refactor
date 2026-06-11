from pathlib import Path
import shutil, time

p = Path("s43.py")
bak = Path(f"s43.py.bak_fix_place_limit_head_{int(time.time())}")
shutil.copy2(p, bak)

lines = p.read_text(encoding="utf-8").splitlines()

start = None
end = None

for i, line in enumerate(lines):
    if line.strip().startswith("async def place_limit("):
        start = i
        break

if start is None:
    raise SystemExit("ERROR: async def place_limit not found")

for j in range(start + 1, min(len(lines), start + 260)):
    if lines[j].strip().startswith("last_exc: Optional[Exception] = None"):
        end = j
        break

if end is None:
    raise SystemExit("ERROR: last_exc boundary not found")

replacement = [
    "    async def place_limit(self, symbol: str, side: str, qty: float, price: float, notional_irt: float, **kwargs) -> dict:",
    "        sym = _canon_symbol(symbol)",
    "",
    "        try:",
    "            side_l0 = str(side or \"\").lower()",
    "            if side_l0.startswith(\"buy\"):",
    "                m = self._regime_multiplier(sym, float(notional_irt))",
    "                m = float(clamp(float(m), 0.0, 1.0))",
    "                if m != 1.0:",
    "                    qty = float(qty) * float(m)",
    "                    notional_irt = float(notional_irt) * float(m)",
    "        except Exception:",
    "            pass",
    "",
    "        if self.cfg.dry_run:",
    "            self._logger.info(",
    "                \"[DRY_RUN] %s %s qty=%.8f px=%.0f notional=%.0f\",",
    "                side, sym, qty, price, notional_irt",
    "            )",
    "            if self._rec:",
    "                self._rec.record_order(",
    "                    time.time(), self._wallet, sym, side, float(qty), float(price), float(notional_irt),",
    "                    ok=True, order_id=\"DRY\", raw={\"dry_run\": True}",
    "                )",
    "            return {\"ok\": True, \"dry_run\": True}",
    "",
    "        r = getattr(self, \"_risk\", None)",
    "        if r is not None:",
    "            try:",
    "                hb = getattr(r, \"hard_blocks_all_orders\", None)",
    "                side_lk = str(side or \"\").lower().strip()",
    "                if callable(hb) and bool(hb(side=side_lk, reduce_only=side_lk.startswith(\"sell\"))):",
    "                    reason = str(getattr(r, \"safe_reason\", \"\") or \"HARD_BLOCK\")",
    "                    self._logger.critical(",
    "                        \"event=HARD_BLOCK wallet=%s sym=%s reason=%s\",",
    "                        self._wallet, sym, reason",
    "                    )",
    "                    try:",
    "                        _phase54_audit_log(\"raise_TradingHalt\", line=11365)",
    "                    except Exception:",
    "                        pass",
    "                    raise TradingHalt(f\"HARD_BLOCK:{reason}\")",
    "            except TradingHalt:",
    "                raise",
    "            except Exception as e:",
    "                if not bool(getattr(self.cfg, \"dry_run\", False)):",
    "                    try:",
    "                        _phase54_audit_log(\"raise_TradingHalt\", line=11370)",
    "                    except Exception:",
    "                        pass",
    "                    raise TradingHalt(f\"HARD_BLOCK:RISK_ERR:{type(e).__name__}\") from e",
    "",
    "        try:",
    "            rd = None",
    "            if r is not None:",
    "                g = getattr(r, \"get_runtime_risk\", None)",
    "                if callable(g):",
    "                    rd = g(self._wallet, sym)",
    "",
    "            side_l = str(side or \"\").lower()",
    "            is_entry = side_l.startswith(\"buy\")",
    "            if rd is not None and is_entry:",
    "                if not bool(getattr(rd, \"allow_entries\", True)):",
    "                    try:",
    "                        _phase54_audit_log(\"raise_TemporaryPause\", line=11317)",
    "                    except Exception:",
    "                        pass",
    "                    raise TemporaryPause(f\"RISK_L{int(getattr(rd,'level',5))}_NO_ENTRY\")",
    "",
    "                mult = float(getattr(rd, \"size_mult\", 1.0) or 1.0)",
    "                mult = float(clamp(mult, 0.0, 1.0))",
    "",
    "                _skip_mult = False",
    "                try:",
    "                    _skip_mult = bool(_CTX_SKIP_RUNTIME_RISK_MULT.get())",
    "                except Exception:",
    "                    _skip_mult = False",
    "",
    "                if (not _skip_mult) and mult < 0.999:",
    "                    qty = float(qty) * mult",
    "                    notional_irt = float(notional_irt) * mult",
    "                    try:",
    "                        self._logger.info(",
    "                            \"event=RISK_SIZE_MULT wallet=%s sym=%s level=%s mult=%.3f\",",
    "                            self._wallet, sym, str(getattr(rd, 'level', '?')), mult",
    "                        )",
    "                    except Exception:",
    "                        pass",
    "        except TemporaryPause:",
    "            raise",
    "        except Exception:",
    "            pass",
    "",
    "        if qty <= 0 or price <= 0:",
    "            raise ValueError(f\"Invalid order params qty={qty} price={price}\")",
    "",
    "        qty2, px2 = await self._norm.normalize(sym, float(qty), float(price))",
    "        if qty2 <= 0 or px2 <= 0:",
    "            raise ValueError(f\"Normalized order invalid qty={qty2} price={px2}\")",
    "",
    "        cid: Optional[str] = None",
    "        if self._oj is not None:",
    "            cid = self._oj.new_cid(self._wallet, sym, side)",
    "            self._oj.mark_pending(",
    "                cid, wallet=self._wallet, symbol=sym, side=side,",
    "                qty=float(qty2), price=float(px2), notional_irt=float(notional_irt)",
    "            )",
    "            self._logger.info(",
    "                \"event=ORDER_INTENT cid=%s wallet=%s side=%s sym=%s qty=%.8f px=%.0f\",",
    "                cid, self._wallet, str(side).lower(), sym, float(qty2), float(px2)",
    "            )",
    "        else:",
    "            try:",
    "                _phase54_audit_log(\"raise_TradingHalt\", line=11418)",
    "            except Exception:",
    "                pass",
    "            raise TradingHalt(\"ORDERS_JOURNAL_DISABLED\")",
    "",
]

lines[start:end] = replacement

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"patched place_limit head: lines {start+1}..{end}; backup={bak}")
