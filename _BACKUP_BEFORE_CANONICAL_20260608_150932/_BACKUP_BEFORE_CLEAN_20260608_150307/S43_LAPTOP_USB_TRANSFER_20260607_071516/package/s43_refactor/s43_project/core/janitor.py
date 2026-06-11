from .logger import Logger
from .trading_bot import TradingBot

class Janitor:
    def __init__(self, bot: "TradingBot"):
        self.bot = bot
        self._log = logging.getLogger("Janitor")
        self._running = False
    def stop(self) -> None:
        self._running = False
    async def start(self) -> None:
        self._running = True
        try:
            sweep_sec = float(_env_float("JANITOR_SWEEP_SEC", 30.0) or 30.0)
        except Exception:
            sweep_sec = 30.0
        sweep_sec = max(5.0, float(sweep_sec))
        self._log.info("event=JANITOR_START sweep_sec=%s", sweep_sec)
        for _omega_guard in range(150000):
            t0 = time.time()
            try:
                await self._sweep()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                try:
                    await _pp200_heal(e, tag="JANITOR_SWEEP_ERR", ctx={"svc": "Janitor"}, sleep_sec=0.0, logger=self._log)
                except Exception:
                    pass
                try:
                    self._log.error("event=JANITOR_SWEEP_ERR err=%s", e)
                except Exception:
                    pass
            dt = time.time() - t0
            await asyncio.sleep(max(0.2, sweep_sec - dt))
    async def _sweep(self) -> None:
        now = time.time()
        try:
            bot_ttl_sec = float(_env_float("ORDER_TTL_SEC", 60.0) or 60.0)
        except Exception:
            bot_ttl_sec = 60.0
        bot_ttl_sec = max(10.0, float(bot_ttl_sec))
        try:
            orphan_age_sec = float(_env_float("ORPHAN_BOT_ORDER_MAX_AGE_SEC", 900.0) or 900.0)
        except Exception:
            orphan_age_sec = 900.0
        orphan_age_sec = max(60.0, float(orphan_age_sec))
        try:
            desync_fail_n = int(_env_int("ORDERS_SYNC_FAIL_OPEN_N", 3) or 3)
        except Exception:
            desync_fail_n = 3
        desync_fail_n = max(1, int(desync_fail_n))
        try:
            rawp = str(os.getenv("BOT_CID_PREFIXES", "SOV,RAZ,PP") or "")
            prefixes = tuple([p.strip().upper() for p in rawp.split(",") if p.strip()])
        except Exception:
            prefixes = ("SOV", "RAZ", "PP")
        for _wname, w in (getattr(self.bot, "wallets", {}) or {}).items():
            try:
                if bool(getattr(w, "sanity_halt", False)):
                    since = float(getattr(w, "sanity_since_ts", 0.0) or getattr(w, "_sanity_since_ts", 0.0) or 0.0)
                    if since and (now - since) > 120.0:
                        self._log.warning("event=JANITOR_SANITY_RESET wallet=%s age_s=%s", getattr(w, "name", _wname), (now - since))
                        w.sanity_halt = False
                        w.sanity_reason = ""
                        try:
                            w.sanity_until_ts = 0.0
                        except Exception:
                            pass
                        try:
                            w.sanity_since_ts = 0.0
                        except Exception:
                            pass
                        try:
                            setattr(w, "_sanity_since_ts", 0.0)
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                streak = int(getattr(w, "_orders_sync_fail_streak", 0) or 0)
                if streak >= desync_fail_n:
                    try:
                        w.open_orders_exch = 0
                    except Exception:
                        pass
                    try:
                        w.locked_since_ts = 0.0
                    except Exception:
                        pass
                    try:
                        setattr(w, "_locked_since_ts", 0.0)
                    except Exception:
                        pass
                    try:
                        w.sanity_halt = True
                        if not str(getattr(w, "sanity_reason", "") or "").strip():
                            w.sanity_reason = "ORDER_SYNC_FAILOPEN_STATE"
                        if not float(getattr(w, "sanity_since_ts", 0.0) or 0.0):
                            w.sanity_since_ts = float(now)
                    except Exception:
                        pass
                    try:
                        _obs_trace(w, "FAILOPEN_STATE", reason=f"orders_sync_fail_streak={streak}", meta={"streak": streak})
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                ord_cnt = int(getattr(w, "open_orders_exch", 0) or 0)
            except Exception:
                ord_cnt = 0
            if ord_cnt <= 0:
                continue
            oldest = None
            try:
                oldest = float(getattr(w, "open_orders_oldest_age_sec", 0.0) or 0.0)
            except Exception:
                oldest = None
            pos_qty = 0.0
            try:
                for p in (getattr(w, "positions", {}) or {}).values():
                    pos_qty += abs(float(getattr(p, "qty", 0.0) or 0.0))
            except Exception:
                pos_qty = 0.0
            need_cancel = False
            reason = ""
            if oldest is not None and oldest >= bot_ttl_sec:
                need_cancel = True
                reason = f"BOT_TTL>{int(bot_ttl_sec)}s"
            if (not need_cancel) and (pos_qty <= 0.0) and (oldest is not None) and (oldest >= orphan_age_sec):
                need_cancel = True
                reason = f"ORPHAN>{int(orphan_age_sec)}s"
            if need_cancel:
                try:
                    self._log.critical("event=JANITOR_CANCEL wallet=%s ord=%s oldest_s=%s reason=%s", getattr(w, "name", _wname), ord_cnt, oldest, reason)
                except Exception:
                    pass
                try:
                    asyncio.create_task(self._cancel_stale_orders(w, prefixes=prefixes, reason=reason), name=f"janitor_cancel_{getattr(w,'name',_wname)}")
                except Exception:
                    pass
    async def _cancel_stale_orders(self, w, prefixes=(), reason: str = "") -> None:
        try:
            if hasattr(w, "ex") and hasattr(w.ex, "cancel_all_orders"):
                try:
                    await asyncio.wait_for(w.ex.cancel_all_orders(), timeout=15.0)
                except Exception:
                    pass
            orders = []
            if hasattr(w, "ex") and hasattr(w.ex, "list_orders"):
                for st in ("open", "new", "active"):
                    try:
                        r = await w.ex.list_orders(status=st)
                        if r is not None:
                            if isinstance(r, dict):
                                v = r.get("data") or r.get("orders") or r.get("items") or []
                                if isinstance(v, list):
                                    orders.extend([o for o in v if isinstance(o, dict)])
                            elif isinstance(r, list):
                                orders.extend([o for o in r if isinstance(o, dict)])
                    except Exception:
                        continue
            def _is_bot(o) -> bool:
                try:
                    cid = str(o.get("client_id") or o.get("clientId") or o.get("cid") or "").strip().upper()
                except Exception:
                    cid = ""
                if not cid:
                    return False
                for p in (prefixes or ()):
                    if cid.startswith(p):
                        return True
                return False
            def _oid(o) -> str | None:
                try:
                    return str(o.get("id") or o.get("order_id") or o.get("orderId") or o.get("uuid") or "").strip() or None
                except Exception:
                    return None
            bot_first = [o for o in orders if _is_bot(o)]
            rest = [o for o in orders if o not in bot_first]
            ordered = bot_first + rest
            for o in ordered:
                oid = _oid(o)
                if not oid:
                    continue
                try:
                    await asyncio.wait_for(w.ex.cancel_order(oid), timeout=10.0)
                except Exception:
                    continue
            try:
                w.open_orders_exch = 0
            except Exception:
                pass
            try:
                w.locked_since_ts = 0.0
            except Exception:
                pass
            try:
                setattr(w, "_locked_since_ts", 0.0)
            except Exception:
                pass
            try:
                _obs_trace(w, "JANITOR_CANCEL_DONE", reason=str(reason or ""), meta={"wallet": str(getattr(w,'name',''))})
            except Exception:
                pass
        except asyncio.CancelledError:
            raise
        except Exception:
            return