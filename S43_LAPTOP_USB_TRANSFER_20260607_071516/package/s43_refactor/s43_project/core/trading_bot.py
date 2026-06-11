from .logger import Logger
from .trading_bot_ops import TradingBotOps
from .temporary_pause import TemporaryPause
from .trading_bot_base import TradingBotBase
from .bot_config import BotConfig
from .janitor import Janitor
from .wallet_runtime import WalletRuntime

class TradingBot(TradingBotBase, TradingBotOps):
    def __init__(self, cfg: BotConfig, logger: Logger):
        super().__init__(cfg, logger)
        try:
            try:
                try:
                    from collections import deque
                except:
                    pass
            except:
                pass
            self._log_throttle: Dict[str, float] = {}
            self._warn_events = __import__("collections").deque(maxlen=int(_env_int("WARN_EVENTS_MAX", 8000) or 8000))
        except Exception:
            self._log_throttle = {}
            try:
                try:
                    try:
                        from collections import deque
                    except:
                        pass
                except:
                    pass
                self._warn_events = __import__("collections").deque(maxlen=8000)
            except Exception:
                self._warn_events = []
        try:
            p = str(getattr(cfg, "last_known_prices_path", "") or "").strip()
            if not p:
                base = os.path.dirname(os.path.abspath(__file__))
                p = os.path.join(base, "cache", "last_known_prices.json")
            WalletRuntime.configure_last_known_prices(p)
            WalletRuntime.load_last_known_prices()
        except Exception:
            pass
        self._janitor_task: Optional[asyncio.Task] = None
        self._internal_tasks_started = False
        try:
            ev = None
            try:
                ev = GLOBAL_SHUTDOWN.bind_asyncio_event()
            except Exception:
                ev = None
            if ev is None:
                ev = asyncio.Event()
            self._ensure_internal_services_started(ev)
        except Exception:
            pass
    def _ensure_internal_services_started(self, stop_ev: asyncio.Event) -> List[asyncio.Task]:
        out: List[asyncio.Task] = []
        try:
            if getattr(self, "_internal_tasks_started", False):
                t = getattr(self, "_janitor_task", None)
                if isinstance(t, asyncio.Task) and not t.done():
                    out.append(t)
                return out
        except Exception:
            pass
        try:
            asyncio.get_running_loop()
        except Exception:
            return out
        try:
            t = asyncio.create_task(self._janitor_loop(stop_ev), name="rtp_janitor")
            self._janitor_task = t
            self._internal_tasks_started = True
            out.append(t)
        except Exception:
            return out
        return out
    async def _janitor_loop(self, stop_ev: asyncio.Event) -> None:
        try:
            sweep_sec = float(_env_float("JANITOR_SWEEP_SEC", 30.0) or 30.0)
        except Exception:
            sweep_sec = 30.0
        sweep_sec = max(5.0, float(sweep_sec))
        try:
            mem_sec = float(_env_float("MEM_SCRUB_SEC", 45.0) or 45.0)
        except Exception:
            mem_sec = 45.0
        mem_sec = max(10.0, float(mem_sec))
        jan = Janitor(self)
        next_mem = time.time() + mem_sec
        for _omega_guard in range(150000):
            t0 = time.time()
            try:
                await jan._sweep()
                await self._janitor_sweep_locked_wallets(jan)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                try:
                    await _pp200_heal(e, tag="JANITOR_LOOP_ERR", ctx={"svc": "JanitorLoop"}, sleep_sec=0.0, logger=getattr(self, "_log", None))
                except Exception:
                    pass
            try:
                if time.time() >= float(next_mem):
                    try:
                        gc.collect()
                    except Exception:
                        pass
                    next_mem = time.time() + mem_sec
            except Exception:
                pass
            dt = time.time() - t0
            await _sleep_or_stop(stop_ev, max(0.2, sweep_sec - dt))
    async def _janitor_sweep_locked_wallets(self, jan: "Janitor") -> None:
        now = time.time()
        try:
            unlock_sec = float(_env_float("JANITOR_UNLOCK_LOCKED_SEC", 180.0) or 180.0)
        except Exception:
            unlock_sec = 180.0
        unlock_sec = max(30.0, float(unlock_sec))
        try:
            rawp = str(os.getenv("BOT_CID_PREFIXES", "SOV,RAZ,PP") or "")
            prefixes = tuple([p.strip().upper() for p in rawp.split(",") if p.strip()])
        except Exception:
            prefixes = ("SOV", "RAZ", "PP")
        for _wname, w in (getattr(self, "wallets", {}) or {}).items():
            wname = str(getattr(w, "name", _wname) or _wname)
            try:
                status = str(getattr(w, "last_engine_status", "") or "").upper()
            except Exception:
                status = ""
            try:
                oo = int(getattr(w, "open_orders_exch", 0) or 0)
            except Exception:
                oo = 0
            try:
                pc = int(len(getattr(w, "positions", {}) or {}))
            except Exception:
                pc = 0
            if oo <= 0:
                for a in ("_locked_since_ts", "locked_since_ts"):
                    try:
                        setattr(w, a, 0.0)
                    except Exception:
                        pass
                if status == "LOCKED":
                    try:
                        setattr(w, "last_engine_status", "OK")
                        setattr(w, "last_engine_reason", "UNLOCK_NO_ORDERS")
                    except Exception:
                        pass
                continue
            if not (status == "LOCKED" or (oo > 0 and pc == 0)):
                continue
            try:
                locked_since = float(getattr(w, "_locked_since_ts", 0.0) or getattr(w, "locked_since_ts", 0.0) or 0.0)
            except Exception:
                locked_since = 0.0
            if not locked_since:
                try:
                    setattr(w, "_locked_since_ts", float(now))
                except Exception:
                    pass
                locked_since = float(now)
            age = max(0.0, float(now - locked_since))
            if age < unlock_sec:
                continue
            try:
                _obs_trace(w, "SYSJANITOR_UNLOCK_LOCKED", reason="timeout", meta={"age_sec": age, "oo": int(oo), "pc": int(pc)})
            except Exception:
                pass
            try:
                asyncio.create_task(
                    jan._cancel_stale_orders(w, prefixes=prefixes, reason="LOCKED_TIMEOUT"),
                    name=f"sysjanitor_cancel_{wname}",
                )
            except Exception:
                pass
            try:
                setattr(w, "_locked_since_ts", float(now))
            except Exception:
                pass
    async def cycle_wallet_execution(
        self,
        w: WalletRuntime,
        now: Optional[float] = None,
        deadline: Optional[float] = None,
    ) -> None:
        now0 = float(time.time() if now is None else now)
        try:
            if bool(getattr(self, "_engine_halted", False)):
                try:
                    await _autonomy_refresh_wallet_token(self, w)
                except Exception:
                    pass
                return
        except Exception:
            pass
        try:
            if bool(getattr(w, "wallet_disabled", False)):
                try:
                    await _autonomy_refresh_wallet_token(self, w)
                except Exception:
                    pass
                return
        except Exception:
            pass
        cash_irt = 0.0
        try:
            _wdu = float(getattr(w, "_balance_disabled_until", 0.0) or 0.0)
            _now = time.time()
            if _wdu > _now:
                try:
                    self._log.warning(
                        "event=WALLET_BALANCE_COOLDOWN wallet=%s retry_in=%.1f fail_count=%s",
                        getattr(w, "name", "?"),
                        float(_wdu - _now),
                        int(getattr(w, "_balance_fail_count", 0) or 0),
                    )
                except Exception:
                    pass
                return
            cash_irt = float(await self._refresh_balance_if_needed(w))
            try:
                setattr(w, "_balance_fail_count", 0)
                setattr(w, "_balance_disabled_until", 0.0)
            except Exception:
                pass
        except asyncio.CancelledError:
            raise
        except (TradingHalt, Exception) as e:
            try:
                _fc = int(getattr(w, "_balance_fail_count", 0) or 0) + 1
                setattr(w, "_balance_fail_count", _fc)
                setattr(w, "_balance_disabled_until", time.time() + 120.0)
            except Exception:
                _fc = int(getattr(w, "_balance_fail_count", 0) or 0)
            try:
                self._log.warning("event=WALLET_BAL_REFRESH_FAIL wallet=%s err=%s", getattr(w, "name", "?"), e)
            except Exception:
                pass
            try:
                self._log.warning(
                    "event=WALLET_ISOLATED wallet=%s phase=runtime_balance reason=%s fail_count=%s cooldown_sec=120",
                    getattr(w, "name", "?"),
                    str(e),
                    _fc,
                )
            except Exception:
                pass
            return
        try:
            try:
                setattr(w, "steps_open", int(await self._refresh_orders_if_needed(w)))
            except Exception:
                pass
        except Exception:
            pass
        syms: List[str] = []
        try:
            quote = str(getattr(getattr(self, "cfg", None), "quote", "IRT") or "IRT").upper().strip() or "IRT"
        except Exception:
            quote = "IRT"
        seen = set()
        def _add_sym(x: str) -> None:
            try:
                cs = _canon_pair(x, quote)
            except Exception:
                cs = str(x or "").strip().upper()
            if not cs or cs in seen:
                return
            seen.add(cs)
            syms.append(cs)
        try:
            for ps, p in (getattr(w, "positions", None) or {}).items():
                try:
                    if p is None:
                        continue
                    if float(getattr(p, "qty", 0.0) or 0.0) <= 0.0:
                        continue
                except Exception:
                    pass
                _add_sym(str(ps))
        except Exception:
            pass
        try:
            for s in (getattr(w, "focus_symbols", None) or []):
                _add_sym(str(s))
        except Exception:
            pass
        try:
            fs = str(getattr(w, "focus_symbol", "") or "").strip()
            if fs:
                _add_sym(fs)
        except Exception:
            pass
        try:
            fsb = str(getattr(self, "_focus_symbol", "") or "").strip()
            if fsb:
                _add_sym(fsb)
        except Exception:
            pass
        try:
            snap = self.snapshot() if hasattr(self, "snapshot") else {}
            if isinstance(snap, dict):
                foc = snap.get("focus") or {}
                if isinstance(foc, dict):
                    fsb2 = str(foc.get("symbol") or foc.get("focus_symbol") or foc.get("focus") or "").strip()
                    if fsb2:
                        _add_sym(fsb2)
        except Exception:
            pass
        try:
            for r in (self.get_top8_snapshot() or []):
                if not isinstance(r, dict):
                    continue
                s = r.get("symbol") or r.get("sym") or r.get("pair")
                if s:
                    _add_sym(str(s))
        except Exception:
            pass
        try:
            pri = list(getattr(getattr(self, "cfg", None), "symbol_priority", None) or [])
            for s in pri:
                _add_sym(str(s))
        except Exception:
            pass
        try:
            for s in (getattr(getattr(w, "cfg", None), "symbols", None) or []):
                _add_sym(str(s))
        except Exception:
            pass
        try:
            for s in (getattr(getattr(self, "cfg", None), "symbols", None) or []):
                _add_sym(str(s))
        except Exception:
            pass
        try:
            for s in (getattr(self, "supported_symbols", None) or []):
                _add_sym(str(s))
        except Exception:
            pass
        if not syms:
            try:
                majors = ["BTC", "USDT", "PAXG", "ETH", "BNB", "SOL", "XRP", "TON", "DOGE"]
                for b in majors:
                    _add_sym(f"{b}{quote}")
            except Exception:
                pass
        try:
            setattr(w, "_hb_priority_syms", list(syms[:12]))
        except Exception:
            pass
        if not syms:
            try:
                w.last_engine_status = "Hold"
                w.last_engine_reason = "NO_SYMBOLS"
                w.last_engine_ts = float(time.time())
            except Exception:
                pass
            try:
                _record_why_no_trade(
                    self,
                    wallet=str(getattr(w, "name", "") or getattr(w, "id", "") or ""),
                    sym="",
                    status="ENTRY_SKIP",
                    reason="NO_SYMBOLS",
                    meta={"entry_attempt": True, "stage": "HB"},
                )
            except Exception:
                pass
            return
        try:
            max_syms = int(getattr(self.cfg, "max_symbols_per_cycle", 4) or 4)
        except Exception:
            max_syms = 4
        max_syms = max(1, min(24, int(max_syms)))
        syms = syms[:max_syms]
        try:
            wc = int(getattr(self.cfg, "wallet_cycle_workers", 3) or 3)
        except Exception:
            wc = 3
        wc = max(1, min(10, int(wc)))
        sem = asyncio.Semaphore(wc)
        async def _run_one(sym: str) -> None:
            async with sem:
                if deadline is not None:
                    try:
                        if float(time.time()) > float(deadline):
                            return
                    except Exception:
                        pass
                await self._process_symbol_heartbeat(w, sym, float(cash_irt))
        for sym in syms:
            try:
                await _run_one(sym)
            except asyncio.CancelledError:
                raise
            except TradingHalt:
                raise
            except TemporaryPause:
                raise
            except Exception as r:
                try:
                    self._log.debug("event=HB_FAIL wallet=%s err=%s", getattr(w, "name", "?"), r)
                except Exception:
                    pass
        try:
            if hasattr(w, "exec") and hasattr(w.exec, "deep_prune_ghost_orders"):
                await w.exec.deep_prune_ghost_orders(getattr(w, 'positions', None))
        except Exception:
            pass
        try:
            if not str(getattr(w, "last_engine_status", "") or "").strip():
                setattr(w, "last_engine_status", "Run")
            if not str(getattr(w, "last_engine_reason", "") or "").strip():
                setattr(w, "last_engine_reason", "HB")
            setattr(w, "last_engine_ts", float(time.time()))
        except Exception:
            pass
    def _bump_warn_event(self, event: str) -> None:
        try:
            self._warn_events.append((float(time.time()), str(event or "").upper()))
        except Exception:
            pass
    def _warn_breakdown(self, window_sec: float = 600.0) -> List[Tuple[str, int]]:
        try:
            now = float(time.time())
        except Exception:
            now = 0.0
        counts: Dict[str, int] = {}
        try:
            for ts, ev in list(self._warn_events):
                try:
                    if (now - float(ts)) > float(window_sec or 600.0):
                        continue
                except Exception:
                    continue
                e = str(ev or "").upper() or "UNCLASSIFIED"
                counts[e] = int(counts.get(e, 0) or 0) + 1
        except Exception:
            return []
        try:
            return sorted(counts.items(), key=lambda x: int(x[1]), reverse=True)
        except Exception:
            return list(counts.items())
    def _log_throttled(self, key: str, min_interval_sec: float) -> bool:
        try:
            now = float(time.time())
        except Exception:
            now = 0.0
        try:
            last = float(self._log_throttle.get(str(key), 0.0) or 0.0)
            if last and now and (now - last) < float(min_interval_sec or 0.0):
                return False
            self._log_throttle[str(key)] = now
            return True
        except Exception:
            return True