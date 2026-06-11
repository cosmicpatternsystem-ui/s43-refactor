from .alpha_model import AlphaModel
from .order_journal import OrderJournal
from .logger import Logger
from .order_normalizer import OrderNormalizer
from .temporary_pause import TemporaryPause
from .exchange_client import ExchangeClient
from .bot_config import BotConfig
from .position import Position
from .tick_recorder import TickRecorder
from .api_error import ApiError

class ExecutionEngine:
    def __init__(self, cfg: BotConfig, ex: ExchangeClient, normalizer: OrderNormalizer, logger: logging.Logger,
                 recorder: Optional[TickRecorder] = None, wallet_name: str = "W1", order_journal: Optional['OrderJournal'] = None):
        self.cfg = cfg
        self._ex = ex
        self._norm = normalizer
        self._logger = logger
        self._rec = recorder
        self._wallet = wallet_name
        self._oj = order_journal
        self._submit_lock = asyncio.Lock()
        self.max_retries = _env_int("ORDER_MAX_RETRIES", 2)
        self.base_backoff = _env_float("ORDER_BACKOFF_SEC", 0.5)
        self.ghost_order_count: int = 0
        self._last_deep_prune_ts: float = 0.0
    def _regime_multiplier(self, symbol: str, notional_irt: float) -> float:
        sym = _canon_symbol(symbol)
        reg = AlphaModel.get_regime(sym)
        st = str(reg.get("state") or "").upper()
        strength = float(reg.get("strength") or 0.0)
        mult = 1.0
        if st == "VOLATILE":
            mult *= 0.50
        elif st == "RANGING":
            mult *= 0.85
        elif st == "TRENDING":
            if strength >= 0.55:
                try:
                    kf = 1.0
                    r = getattr(self, "_risk", None)
                    mem = getattr(r, "memory", None) if r is not None else None
                    if mem is not None and hasattr(mem, "kelly_fraction"):
                        kf = float(mem.kelly_fraction())
                    kf = float(clamp(kf, 0.25, 1.25))
                    damp = float(0.55 + 0.45 * kf)
                    full = float(kf)
                    mult *= float(clamp(full / max(1e-9, damp), 0.70, 1.30))
                except Exception:
                    pass
        try:
            spr = float(reg.get("spread_bps") or 0.0)
            max_spr = float(getattr(self.cfg, "alpha_max_spread_bps", 35.0) or 35.0)
            if spr > max_spr * 0.75:
                mult *= 0.85
        except Exception:
            pass
        try:
            mult = float(clamp(mult, 0.30, 1.35))
        except Exception:
            mult = 1.0
        return float(mult)
    async def place_limit(self, symbol: str, side: str, qty: float, price: float, notional_irt: float, **kwargs) -> dict:
        sym = _canon_symbol(symbol)
        try:
            side_l0 = str(side or "").lower()
            if side_l0.startswith("buy"):
                m = self._regime_multiplier(sym, float(notional_irt))
                m = float(clamp(float(m), 0.0, 1.0))
                if m != 1.0:
                    qty = float(qty) * float(m)
                    notional_irt = float(notional_irt) * float(m)
        except Exception:
            pass
        if self.cfg.dry_run:
            self._logger.info("[DRY_RUN] %s %s qty=%.8f px=%.0f notional=%.0f", side, sym, qty, price, notional_irt)
            if self._rec:
                self._rec.record_order(time.time(), self._wallet, sym, side, float(qty), float(price), float(notional_irt),
                                       ok=True, order_id="DRY", raw={"dry_run": True})
            return {"ok": True, "dry_run": True}
        r = getattr(self, "_risk", None)
        if r is not None:
            try:
                hb = getattr(r, "hard_blocks_all_orders", None)
                side_lk = str(side or "").lower().strip()
                if callable(hb) and bool(hb(side=side_lk, reduce_only=side_lk.startswith("sell"))):
                    reason = str(getattr(r, "safe_reason", "") or "HARD_BLOCK")
                    self._logger.critical("event=HARD_BLOCK wallet=%s sym=%s reason=%s", self._wallet, sym, reason)
                    raise TradingHalt(f"HARD_BLOCK:{reason}")
            except TradingHalt:
                raise
            except Exception as e:
                if not bool(getattr(self.cfg, "dry_run", False)):
                    raise TradingHalt(f"HARD_BLOCK:RISK_ERR:{type(e).__name__}") from e
        try:
            rd = None
            if r is not None:
                g = getattr(r, "get_runtime_risk", None)
                if callable(g):
                    rd = g(self._wallet, sym)
            side_l = str(side or "").lower()
            is_entry = side_l.startswith("buy")
            if rd is not None and is_entry:
                if not bool(getattr(rd, "allow_entries", True)):
                    raise TemporaryPause(f"RISK_L{int(getattr(rd,'level',5))}_NO_ENTRY")
                mult = float(getattr(rd, "size_mult", 1.0) or 1.0)
                mult = float(clamp(mult, 0.0, 1.0))
                _skip_mult = False
                try:
                    _skip_mult = bool(_CTX_SKIP_RUNTIME_RISK_MULT.get())
                except Exception:
                    _skip_mult = False
                if (not _skip_mult) and mult < 0.999:
                    qty = float(qty) * mult
                    notional_irt = float(notional_irt) * mult
                    try:
                        self._logger.info("event=RISK_SIZE_MULT wallet=%s sym=%s level=%s mult=%.3f",
                                          self._wallet, sym, str(getattr(rd,'level','?')), mult)
                    except Exception:
                        pass
        except TemporaryPause:
            raise
        except Exception:
            pass
        if qty <= 0 or price <= 0:
            raise ValueError(f"Invalid order params qty={qty} price={price}")
        qty2, px2 = await self._norm.normalize(sym, float(qty), float(price))
        if qty2 <= 0 or px2 <= 0:
            raise ValueError(f"Normalized order invalid qty={qty2} price={px2}")
        cid: Optional[str] = None
        if self._oj is not None:
            cid = self._oj.new_cid(self._wallet, sym, side)
            self._oj.mark_pending(cid, wallet=self._wallet, symbol=sym, side=side,
                                 qty=float(qty2), price=float(px2), notional_irt=float(notional_irt))
            self._logger.info("event=ORDER_INTENT cid=%s wallet=%s side=%s sym=%s qty=%.8f px=%.0f",
                             cid, self._wallet, str(side).lower(), sym, float(qty2), float(px2))
        else:
            raise TradingHalt("ORDERS_JOURNAL_DISABLED")
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                async with self._submit_lock:
                    if attempt == 0:
                        order_key = f"{str(side).lower()}_{px2}_{qty2}_{sym}"
                        if getattr(self, "_last_order_key", None) == order_key and (time.time() - getattr(self, "_last_order_time", 0.0)) < 5.0:
                            try:
                                self._logger.warning("Duplicate order prevented for %s", sym)
                            except Exception:
                                pass
                            if self._oj is not None:
                                try:
                                    self._oj.mark_resolved(cid, final_state="SKIPPED_DUP", note=str(order_key))
                                except Exception:
                                    pass
                            return {"ok": False, "skipped": True, "reason": "DUPLICATE_PREVENTED", "cid": cid}
                        self._last_order_key = order_key
                        self._last_order_time = time.time()
                    order_kwargs = dict(kwargs)
                    order_kwargs.pop("cid", None)
                    order_kwargs.setdefault("notional_irt", float(notional_irt))
                    order_kwargs.setdefault("fill_type", "limit")
                    order_kwargs.setdefault("market", "spot")
                    order_kwargs.setdefault("reduce_only", str(side or "").lower().startswith("sell"))
                    try:
                        self._logger.info(
                            "event=PRE_ORDER_TRACE wallet=%s sym=%s side=%s qty=%.12f px=%.12f notional=%.2f dry_run=%s reduce_only=%s attempt=%s cid=%s",
                            self._wallet,
                            sym,
                            str(side).lower(),
                            float(qty2),
                            float(px2),
                            float(notional_irt),
                            bool(getattr(self.cfg, "dry_run", False)),
                            order_kwargs.get("reduce_only"),
                            attempt,
                            cid,
                        )
                    except Exception:
                        pass
                    resp = await self._ex.place_order(sym, side, float(qty2), float(px2), cid=cid, **order_kwargs)
                if resp is None:
                    raise ApiError("Order submission returned None")
                ok = bool(resp.get("ok")) or (resp.get("status") in (200, 201))
                if ok:
                    oid = str(resp.get("order_id") or resp.get("id") or "")
                    if self._oj is not None:
                        try:
                            self._oj.mark_ack(cid, exchange_order_id=oid, raw=resp)
                        except Exception:
                            pass
                    if self._rec:
                        self._rec.record_order(time.time(), self._wallet, sym, side, float(qty2), float(px2),
                                               float(notional_irt), ok=True, order_id=oid, raw=resp)
                    try:
                        if isinstance(resp, dict) and cid:
                            if ("cid" not in resp) and ("client_id" not in resp) and ("clientId" not in resp) and ("client_order_id" not in resp) and ("clientOrderId" not in resp):
                                resp = dict(resp)
                                resp["cid"] = str(cid)
                    except Exception:
                        pass
                    return resp
                if self._oj is not None:
                    try:
                        self._oj.mark_resolved(cid, final_state="REJECTED", note=str(resp)[:300])
                    except Exception:
                        pass
                try:
                    if isinstance(resp, dict) and cid:
                        if ("cid" not in resp) and ("client_id" not in resp) and ("clientId" not in resp) and ("client_order_id" not in resp) and ("clientOrderId" not in resp):
                            resp = dict(resp)
                            resp["cid"] = str(cid)
                except Exception:
                    pass
                return resp
            except (TradingHalt, TemporaryPause):
                raise
            except asyncio.TimeoutError as e:
                last_exc = e
                try:
                    self._logger.error("event=ORDER_TIMEOUT wallet=%s sym=%s cid=%s", self._wallet, sym, cid)
                except Exception:
                    pass
                if attempt < self.max_retries:
                    try:
                        await asyncio.sleep(float(self.base_backoff) * (2 ** attempt))
                    except Exception:
                        pass
                    continue
                break
            except Exception as e:
                last_exc = e
                try:
                    self._logger.error("event=ORDER_POST_FAIL side=%s sym=%s cid=%s attempt=%d/%d err=%s",
                                       side, sym, cid, attempt + 1, self.max_retries + 1, e, exc_info=True)
                except Exception:
                    pass
                if attempt < self.max_retries:
                    try:
                        await asyncio.sleep(float(self.base_backoff) * (2 ** attempt))
                    except Exception:
                        pass
        if self._rec:
            self._rec.record_order(time.time(), self._wallet, sym, side, float(qty2), float(px2), float(notional_irt),
                                   ok=False, order_id=None, raw={"error": str(last_exc), "cid": cid})
        if self._oj is not None:
            try:
                self._oj.mark_uncertain(cid, err=str(last_exc))
            except Exception:
                pass
        if isinstance(last_exc, (asyncio.TimeoutError, aiohttp.ClientError, OSError)) and (not self.cfg.dry_run):
            raise TradingHalt(f"ORDER_DESYNC cid={cid} side={side} sym={sym}") from last_exc
        raise ApiError(f"Order failed after retries: {last_exc}")
    async def place_ladder(self, symbol: str, side: str, qty: float, base_price: float, notional_irt: float) -> dict:
        sym = _canon_symbol(symbol)
        steps = int(getattr(self.cfg, "ladder_steps", 1) or 1)
        if not bool(getattr(self.cfg, "laddering", False)) or steps <= 1:
            return await self.place_limit(sym, side, qty, base_price, notional_irt)
        bps = float(getattr(self.cfg, "ladder_bps", 0.0) or 0.0)
        pause_ms = int(getattr(self.cfg, "ladder_pause_ms", 0) or 0)
        if qty <= 0 or base_price <= 0:
            raise ValueError(f"Invalid ladder params qty={qty} base_price={base_price}")
        child_orders = []
        remaining = float(qty)
        for i in range(steps):
            q_i = remaining if i == steps - 1 else remaining / float(steps - i)
            remaining -= q_i
            step_bps = (bps * float(i)) / 10000.0
            px_i = base_price * (1.0 - step_bps) if str(side).lower() == "buy" else base_price * (1.0 + step_bps)
            resp = await self.place_limit(sym, side, q_i, px_i, (notional_irt * (q_i / max(qty, 1e-12))))
            child_orders.append(resp)
            if pause_ms > 0 and i < steps - 1:
                await asyncio.sleep(pause_ms / 1000.0)
        any_sent = False
        all_good = True
        all_dup = True
        for o in (child_orders or []):
            if not isinstance(o, dict):
                all_good = False
                all_dup = False
                continue
            ok0 = bool(o.get("ok"))
            if not ok0:
                try:
                    ok0 = int(float(o.get("status") or o.get("code") or 0)) in (200, 201)
                except Exception:
                    ok0 = False
            dup0 = bool(o.get("skipped")) and str(o.get("reason") or "").upper() == "DUPLICATE_PREVENTED"
            if ok0:
                any_sent = True
                all_dup = False
            elif dup0:
                pass
            else:
                all_good = False
                all_dup = False
        if child_orders and all_dup:
            return {"ok": False, "skipped": True, "reason": "DUPLICATE_PREVENTED", "ladder": True, "steps": steps, "children": child_orders}
        ok = bool(all_good and any_sent)
        return {"ok": ok, "ladder": True, "steps": steps, "children": child_orders}
    async def deep_prune_ghost_orders(self, positions: Optional[Dict[str, 'Position']] = None, *, force: bool = False) -> int:
        """Aggressive ghost/orphan order pruning (Termux-safe).

        Strategy:
        - Fetch open orders from exchange.
        - Identify bot-owned orders by CID prefixes / wallet tag.
        - Cross-check against local OrderJournal pending records and WalletState totals.
        - Cancel orders that are clearly orphaned or too old/far from book.
        - Persist first_seen/last_seen so Android throttling doesn't 'forget' ghosts.
        """
        now = float(time.time())
        positions = positions or {}
        if (not force) and (now - float(getattr(self, "_last_deep_prune_ts", 0.0) or 0.0)) < float(_env_float("DEEP_PRUNE_INTERVAL_SEC", 600.0) or 600.0):
            return 0
        self._last_deep_prune_ts = float(now)
        if bool(getattr(self.cfg, "dry_run", False)):
            self.ghost_order_count = 0
            return 0
        try:
            if not isinstance(getattr(self, "_ghost_seen", None), dict):
                setattr(self, "_ghost_seen", {})
            if not bool(getattr(self, "_ghost_state_loaded", False)):
                base = str(getattr(self.cfg, "state_path", "") or "").strip()
                if base:
                    path = f"{base}.{str(self._wallet or 'W1')}.ghost.json"
                else:
                    path = f"ghost_orders_{str(self._wallet or 'W1')}.json"
                setattr(self, "_ghost_state_path", path)
                try:
                    if os.path.isfile(path):
                        with open(path, "r", encoding="utf-8") as f:
                            obj = json.load(f)
                        if isinstance(obj, dict) and isinstance(obj.get("orders"), dict):
                            setattr(self, "_ghost_seen", dict(obj.get("orders") or {}))
                except Exception:
                    pass
                setattr(self, "_ghost_state_loaded", True)
        except Exception:
            pass
        ghost_seen: Dict[str, dict] = getattr(self, "_ghost_seen", {}) or {}
        known_oids: set = set()
        known_cids: set = set()
        try:
            if self._oj is not None:
                pend = self._oj.pending() or {}
                for _cid, rec in (pend or {}).items():
                    if _cid:
                        known_cids.add(str(_cid))
                    if not isinstance(rec, dict):
                        continue
                    oid = rec.get("exchange_order_id") or rec.get("order_id") or rec.get("id")
                    if oid:
                        known_oids.add(str(oid))
        except Exception:
            pass
        resps = []
        try:
            for st in ("open", "new", "active"):
                try:
                    r = await self._ex.list_orders(status=st)
                    if r is not None:
                        resps.append(r)
                except Exception:
                    pass
            if not resps:
                try:
                    r = await self._ex.list_orders()
                    if r is not None:
                        resps.append(r)
                except Exception:
                    pass
        except Exception:
            resps = []
        orders: List[dict] = []
        try:
            for r in (resps or []):
                orders.extend(OrderJournal._extract_orders(r))
        except Exception:
            orders = []
        seen = set()
        uniq: List[dict] = []
        for o in (orders or []):
            if not isinstance(o, dict):
                continue
            try:
                oid0 = OrderJournal._order_id(o)
            except Exception:
                oid0 = None
            k = str(oid0 or "").strip()
            if not k or k in seen:
                continue
            seen.add(k)
            uniq.append(o)
        orders = uniq
        prefixes = tuple(str(os.getenv("BOT_CID_PREFIXES", "raz_,sov_,bot_") or "raz_,sov_,bot_").split(","))
        max_cancel = int(_env_int("DEEP_PRUNE_MAX_CANCEL", 7) or 7)
        cash_free = cash_total = 0.0
        assets_free: Dict[str, float] = {}
        assets_total: Dict[str, float] = {}
        try:
            _wdu = float(getattr(self, "_balance_disabled_until", 0.0) or 0.0)
        except Exception:
            _wdu = 0.0
        if _wdu > time.time():
            try:
                print(f"ISOCHK_COOLDOWN phase=deep_prune until={int(_wdu)} fail_count={int(getattr(self, '_balance_fail_count', 0) or 0)}", flush=True)
            except Exception:
                pass
            raise TradingHalt("BALANCE_COOLDOWN")
        try:
            bal = await self._ex.get_balance()
            try:
                setattr(self, "_balance_fail_count", 0)
                setattr(self, "_balance_disabled_until", 0.0)
            except Exception:
                pass
        except Exception as e:
            try:
                _fc = int(getattr(self, "_balance_fail_count", 0) or 0) + 1
                setattr(self, "_balance_fail_count", _fc)
                setattr(self, "_balance_disabled_until", time.time() + 120.0)
                print(f"ISOCHK phase=deep_prune err={type(e).__name__}:{e} fail_count={_fc}", flush=True)
            except Exception:
                pass
            raise
        q = str(getattr(self.cfg, "quote", "IRT") or "IRT")
        cash_free, cash_total, assets_free, assets_total, _ok = _parse_wallet_balance_response_v2(bal, quote=q)
        if not _ok: raise TradingHalt("BALANCE_FETCH_FAILED: PARSE_OK_FALSE")
        mid_cache: Dict[str, float] = {}
        depth_budget = int(_env_int("DEEP_PRUNE_DEPTH_BUDGET", 3) or 3)
        async def _mid(sym: str) -> float:
            nonlocal depth_budget
            sym = _canon_symbol(sym)
            if sym in mid_cache:
                return float(mid_cache[sym] or 0.0)
            if depth_budget <= 0:
                return 0.0
            depth_budget -= 1
            try:
                d = await self._ex.get_depth(sym, priority=True)
                bids = d.get("bids") or d.get("buy") or d.get("bid") or []
                asks = d.get("asks") or d.get("sell") or d.get("ask") or []
                bb = float(bids[0][0]) if bids and isinstance(bids[0], (list, tuple)) and len(bids[0]) >= 1 else 0.0
                ba = float(asks[0][0]) if asks and isinstance(asks[0], (list, tuple)) and len(asks[0]) >= 1 else 0.0
                m = (bb + ba) * 0.5 if bb > 0 and ba > 0 else (bb or ba)
                mid_cache[sym] = float(m or 0.0)
                return float(m or 0.0)
            except Exception:
                mid_cache[sym] = 0.0
                return 0.0
        def _is_bot_cid(cid: str) -> bool:
            cid_l = str(cid or "").lower().strip()
            if not cid_l:
                return False
            for pfx in prefixes:
                pfx = str(pfx or "").strip().lower()
                if pfx and cid_l.startswith(pfx):
                    return True
            try:
                if str(self._wallet).lower() in cid_l:
                    return True
            except Exception:
                pass
            return False
        def _side(o: dict) -> str:
            try:
                s = str(o.get("side") or o.get("type") or o.get("direction") or "").upper().strip()
            except Exception:
                s = ""
            if s.startswith("S"):
                return "SELL"
            if s.startswith("B"):
                return "BUY"
            return s or "?"
        def _qty(o: dict) -> float:
            for k in ("amount", "qty", "quantity", "origQty", "orig_amount", "size"):
                if o.get(k) is not None:
                    try:
                        return float(o.get(k) or 0.0)
                    except Exception:
                        continue
            return 0.0
        def _px(o: dict) -> float:
            for k in ("price", "rate", "limit_price", "p"):
                if o.get(k) is not None:
                    try:
                        return float(o.get(k) or 0.0)
                    except Exception:
                        continue
            return 0.0
        ttl_sec = float(_env_float("GHOST_PRUNE_TTL_SEC", 600.0) or 600.0)
        min_age_sec = float(_env_float("GHOST_PRUNE_MIN_AGE_SEC", 25.0) or 25.0)
        far_bps = float(_env_float("GHOST_PRUNE_FAR_BPS", 250.0) or 250.0)
        far_min_age = float(_env_float("GHOST_PRUNE_FAR_MIN_AGE_SEC", 180.0) or 180.0)
        keep_sec = float(_env_float("GHOST_PRUNE_KEEP_SEC", 86400.0) or 86400.0)
        canceled = 0
        live_oids = set()
        for o in (orders or []):
            if canceled >= max_cancel:
                break
            oid = None
            sym = None
            cid = ""
            try:
                oid = OrderJournal._order_id(o)
            except Exception:
                oid = None
            try:
                sym = _canon_symbol(o.get("symbol") or o.get("market") or o.get("pair") or "")
            except Exception:
                sym = None
            try:
                cid = str(o.get("client_id") or o.get("clientId") or o.get("cid") or o.get("clientOrderId") or "")
            except Exception:
                cid = ""
            if not oid or not sym:
                continue
            oid_s = str(oid)
            live_oids.add(oid_s)
            if not _is_bot_cid(cid):
                continue
            rec = ghost_seen.get(oid_s)
            if not isinstance(rec, dict):
                rec = {"first_seen": now, "last_seen": now, "sym": sym, "cid": cid}
            rec["last_seen"] = now
            rec["sym"] = sym
            rec["cid"] = cid
            rec["side"] = _side(o)
            rec["price"] = _px(o)
            rec["qty"] = _qty(o)
            ghost_seen[oid_s] = rec
            if oid_s in known_oids or (cid and cid in known_cids):
                continue
            try:
                if isinstance(positions, dict) and sym in positions and abs(float(getattr(positions.get(sym), "qty", 0.0) or 0.0)) > 0.0:
                    continue
            except Exception:
                pass
            age = float(now) - float(rec.get("first_seen") or now)
            if age < min_age_sec:
                continue
            side = rec.get("side") or _side(o)
            px = float(rec.get("price") or 0.0)
            qty = float(rec.get("qty") or 0.0)
            base_ccy, quote_ccy = None, None
            try:
                base_ccy, quote_ccy = _split_pair(sym)
                base_ccy = str(base_ccy or "").upper().strip()
                quote_ccy = str(quote_ccy or "").upper().strip()
            except Exception:
                base_ccy = None
                quote_ccy = None
            orphan = False
            orphan_reason = ""
            try:
                if str(side).upper().startswith("SELL") and base_ccy:
                    have = float((assets_total or {}).get(base_ccy, 0.0) or 0.0)
                    if have <= max(0.0000001, qty * 0.05):
                        orphan = True
                        orphan_reason = "NO_BASE_TOTAL"
                elif str(side).upper().startswith("BUY"):
                    need = float(qty) * float(px)
                    if need > 0.0 and float(cash_total or 0.0) <= max(1.0, need * 0.05):
                        orphan = True
                        orphan_reason = "NO_QUOTE_TOTAL"
            except Exception:
                pass
            far = False
            dist_bps = 0.0
            try:
                if px > 0.0:
                    mid = await _mid(sym)
                    if mid > 0.0:
                        dist_bps = abs((px / mid) - 1.0) * 10000.0
                        if dist_bps >= far_bps and age >= far_min_age:
                            far = True
            except Exception:
                far = False
            should_cancel = bool(orphan) or (age >= ttl_sec) or (far and age >= far_min_age)
            if not should_cancel:
                continue
            try:
                await self._ex.cancel_order(oid)
                canceled += 1
                try:
                    self._logger.warning("event=CANCEL_GHOST wallet=%s sym=%s oid=%s cid=%s reason=%s age=%.1fs dist=%.1fbps", self._wallet, sym, oid_s, _short(cid, 40), (orphan_reason or "TTL"), age, dist_bps)
                except Exception:
                    pass
            except Exception:
                pass
        self.ghost_order_count = int(canceled)
        try:
            new_map: Dict[str, dict] = {}
            for oid_s, rec in (ghost_seen or {}).items():
                try:
                    ls = float(rec.get("last_seen") or 0.0)
                except Exception:
                    ls = 0.0
                if oid_s in live_oids or (now - ls) <= keep_sec:
                    new_map[str(oid_s)] = rec
            ghost_seen = new_map
            setattr(self, "_ghost_seen", ghost_seen)
            path = str(getattr(self, "_ghost_state_path", "") or "")
            if path:
                payload = {"ts": now, "wallet": str(self._wallet), "orders": ghost_seen}
                try:
                    _atomic_write_json(path, payload, fsync=bool(_env_bool("STATE_FSYNC", False)))
                except Exception:
                    try:
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(payload, f)
                    except Exception:
                        pass
        except Exception:
            pass
        if canceled > 0:
            try:
                self._logger.warning("event=DEEP_PRUNE wallet=%s canceled=%d", self._wallet, int(canceled))
            except Exception:
                pass
        return int(canceled)