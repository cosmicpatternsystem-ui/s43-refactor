from .phoenix_decision import PhoenixDecision
from .order_book_top import OrderBookTop
from .risk_manager import RiskManager
from .order_journal import OrderJournal
from .logger import Logger
from .sovereign_engine import SovereignEngine
from .risk_decision import RiskDecision
from .clock_arbiter import ClockArbiter
from .temporary_pause import TemporaryPause
from .exchange_client import ExchangeClient
from .__volatility_analyzer import _VolatilityAnalyzer
from .dashboard_manager import DashboardManager
from .bot_config import BotConfig
from .trading_bot import TradingBot
from .position import Position
from .wallet_runtime import WalletRuntime

class TradingBotOps:
    async def refresh_market_focus(self) -> List[str]:
        try:
            if bool(getattr(self, "_sniper_only", False)):
                majors = ["BTCIRT", "ETHIRT", "USDTIRT", "PAXGIRT", "BNBIRT", "SOLIRT", "XRPIRT"]
                base = list(getattr(getattr(self, "cfg", None), "symbols", None) or []) + majors
                out: List[str] = []
                seen: Set[str] = set()
                for s in base:
                    cs = _canon_symbol(s)
                    if cs and cs not in seen:
                        seen.add(cs)
                        out.append(cs)
                return out
        except Exception:
            pass
        termux = _env_bool("TERMUX_MODE", False)
        use_momentum = bool(termux and _env_bool("TERMUX_MOMENTUM_SCANNER", True))
        try:
            min_vol = float(os.environ.get("TERMUX_MIN_VOL_24H_IRT", "20000000" if use_momentum else "50000000"))
        except Exception:
            min_vol = 20_000_000.0 if use_momentum else 50_000_000.0
        candidates: List[dict] = []
        if use_momentum:
            try:
                raw_data = {}
                try:
                    internal = getattr(self, "_market_snapshot", None)
                    its = float(getattr(self, "_market_snapshot_local_ts", 0.0) or 0.0)
                    max_age = float(os.getenv("FOCUS_SCAN_USE_INTERNAL_MAX_AGE_SEC", "30") or 30.0)
                    if isinstance(internal, dict) and internal and its > 0.0 and (time.time() - its) <= max_age:
                        raw_data = internal
                except Exception:
                    raw_data = {}
                if not raw_data:
                    raw_data = await self.public.get_market_snapshot()
            except Exception as e:
                raw_data = {}
                try:
                    snap = getattr(self.public, "_last_market_stats_snapshot", None)
                    if isinstance(snap, dict) and snap:
                        raw_data = snap
                except Exception:
                    raw_data = {}
                if not raw_data:
                    try:
                        snap2 = getattr(self.public, "_last_all_tickers_snapshot", None)
                        if isinstance(snap2, dict):
                            raw_data = snap2.get("by_symbol") if isinstance(snap2.get("by_symbol"), dict) else snap2
                    except Exception:
                        raw_data = {}
                if not raw_data:
                    self._log.warning("event=FOCUS_SCAN_FAIL mode=momentum err=%s", e)
                    raw_data = {}
            for sym, info in (raw_data or {}).items():
                s = _canon_symbol(sym)
                if not s or (not s.endswith("IRT")):
                    continue
                if not isinstance(info, dict):
                    continue
                try:
                    vol_24h = float(_safe_float(info.get("volume") or info.get("quote_volume") or info.get("quoteVolume") or 0.0, default=0.0, translate_digits=True, allow_percent=False, finite=True, na_values=True, strip=True) or 0.0)
                except Exception:
                    vol_24h = 0.0
                if vol_24h < min_vol:
                    continue
                def _f(k: str, default: float = 0.0) -> float:
                    return float(_safe_float((info or {}).get(k), default=default, translate_digits=True, allow_percent=False, finite=True, na_values=False, strip=True) or default)
                price_now = _f("last", _f("price", _f("close", _f("last_price", 0.0))))
                if price_now <= 0:
                    continue
                price_1h = _f("open_1h", _f("open1h", _f("open_1hour", _f("open", price_now))))
                if price_1h <= 0:
                    price_1h = price_now
                change_1h = ((price_now - price_1h) / price_1h) * 100.0 if price_1h > 0 else 0.0
                score = abs(change_1h) * 15.0
                if score > 0:
                    candidates.append({"symbol": s, "score": float(score), "change_1h": float(change_1h)})
        else:
            try:
                all_stats = await self.public.get_all_market_stats()
            except Exception as e:
                self._log.warning("event=FOCUS_SCAN_FAIL mode=fallback err=%s", e)
                return list((self.supported_symbols or {}).keys())
            for sym, data in (all_stats or {}).items():
                s = _canon_symbol(sym)
                if not s or (not s.endswith("IRT")):
                    continue
                if not isinstance(data, dict):
                    continue
                try:
                    vol = float(data.get("volume") or 0.0)
                except Exception:
                    vol = 0.0
                if termux and vol < min_vol:
                    continue
                if termux:
                    score = float(self.calculate_opportunity_score(data))
                else:
                    try:
                        high = float(data.get("high") or 0.0)
                        low = float(data.get("low") or 0.0)
                    except Exception:
                        high, low = 0.0, 0.0
                    vola = 0.0
                    if low and low > 0 and high and high > 0:
                        vola = max(0.0, (high - low) / low)
                    score = (vol * 0.6) + (vola * vol * 0.4)
                if score > 0:
                    candidates.append({"symbol": s, "score": float(score)})
        candidates.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
        focus_map: Dict[str, float] = {"PAXGIRT": 0.20}
        scores: Dict[str, float] = {"PAXGIRT": float(candidates[0]["score"] if candidates else 0.0)}
        weights = [0.18, 0.15, 0.12, 0.10, 0.08, 0.07, 0.05, 0.05]
        for c in candidates:
            if len(focus_map) >= 9:
                break
            s = _canon_symbol(c.get("symbol") or "")
            try:
                dq = str(getattr(getattr(self, "cfg", None), "quote", "IRT") or "IRT").upper()
            except Exception:
                dq = "IRT"
            try:
                rm = getattr(self, "_resolved_symbol_map", None) or getattr(self, "_resolved_major_map", None) or {}
                if s and isinstance(rm, dict) and rm.get(s):
                    s = _canon_symbol(rm.get(s))
                if s:
                    s = _canon_pair(s, dq)
            except Exception:
                pass
            if s and s not in focus_map:
                focus_map[s] = float(weights[len(focus_map) - 1])
                scores[s] = float(c.get("score", 0.0) or 0.0)
        focus_keys = list(focus_map.keys())
        prev = getattr(self, "supported_symbols", {}) or {}
        if isinstance(prev, dict):
            self._focus_prev_symbols = list(prev.keys())
        else:
            self._focus_prev_symbols = list(prev or [])
        self.supported_symbols = dict(focus_map)
        self._focus_scores = dict(scores)
        try:
            _src = raw_data if isinstance(raw_data, dict) and raw_data else (all_stats if isinstance(all_stats, dict) else {})
            _umap = {}
            for _sym, _d in (_src or {}).items():
                s0 = _canon_symbol(_sym)
                if not s0 or (not str(s0).endswith("IRT")):
                    continue
                d0 = _d or {}
                try:
                    vol_irt = _safe_float(
                        d0.get("volume_24h_irt")
                        or d0.get("vol_irt")
                        or d0.get("quoteVolume")
                        or d0.get("quote_volume")
                        or d0.get("value")
                        or d0.get("value_irt")
                        or d0.get("volume")
                        or 0.0
                    )
                except Exception:
                    vol_irt = 0.0
                try:
                    chg_1h = _safe_float(
                        d0.get("change_1h")
                        or d0.get("changePercent1h")
                        or d0.get("pct_1h")
                        or d0.get("priceChangePercent")
                        or d0.get("change")
                        or 0.0
                    )
                except Exception:
                    chg_1h = 0.0
                _umap[s0] = {"vol_irt": float(vol_irt or 0.0), "chg_1h": float(chg_1h or 0.0)}
            _u_max = int(_env_int("UNIVERSE_MAX", 80) or 80)
            _u_sorted = sorted(_umap.items(), key=lambda kv: float((kv[1] or {}).get("vol_irt") or 0.0), reverse=True)
            self._universe_symbols = [k for (k, _v) in _u_sorted[: max(20, _u_max)]]
            self._universe_mkt_map = dict(_umap)
            self._universe_last_ts = time.time()
        except Exception:
            pass
        self.last_market_scan = time.time()
        self._focus_last_scan_ts = float(self.last_market_scan)
        self._focus_risk_weights = dict(focus_map)
        self._focus_scan_mode = "momentum_1h" if use_momentum else ("termux" if termux else "v126")
        self._log.info(
            "event=FOCUS_UPDATED mode=%s termux=%s min_vol=%s symbols=%s",
            self._focus_scan_mode,
            termux,
            int(min_vol),
            ",".join(focus_keys),
        )
        for w in self.wallets.values():
            try:
                if bool(getattr(w.cfg, "autonomous_ai", False)):
                    setattr(w, "focus_symbols", list(self.supported_symbols or []))
            except Exception:
                pass
        try:
            removed = set(self._focus_prev_symbols or []) - set(self.supported_symbols or [])
            if removed:
                t = getattr(self, "_soft_exit_task", None)
                if t is None or bool(getattr(t, "done", lambda: True)()):
                    async def _runner(rem=set(removed)):
                        try:
                            to2 = float(os.getenv("SOFT_EXIT_TIMEOUT_SEC", "25") or 25.0)
                        except Exception:
                            to2 = 25.0
                        try:
                            await asyncio.wait_for(self._soft_exit_removed_symbols(rem), timeout=max(5.0, min(120.0, float(to2))))
                        except asyncio.CancelledError:
                            raise
                        except Exception as e:
                            try:
                                self._log.warning("event=SOFT_EXIT_FAIL n=%d err=%s", int(len(rem)), str(e)[:180])
                            except Exception:
                                pass
                    setattr(self, "_soft_exit_task", asyncio.create_task(_runner(), name="soft_exit"))
        except Exception:
            pass
        return list(self.supported_symbols.keys())
    async def _soft_exit_removed_symbols(self, removed: "set[str]") -> None:
        if not removed:
            return
        for w in self.wallets.values():
            if not bool(getattr(w.cfg, "autonomous_ai", False)):
                continue
            for sym in removed:
                s = _canon_symbol(sym)
                if not s:
                    continue
                try:
                    try:
                        _to = float(getattr(self.cfg, "low_priority_timeout_sec", 6.0) or 6.0)
                    except Exception:
                        _to = 6.0
                    resp = await asyncio.wait_for(w.ex.list_orders(symbol=s), timeout=max(1.0, min(25.0, float(_to))))
                    orders = OrderJournal._extract_orders(resp)
                except Exception:
                    continue
                for o in orders:
                    try:
                        st = OrderJournal._order_status(o)
                        if OrderJournal._is_terminal_status(st):
                            continue
                        side = (OrderJournal._order_side(o) or "").lower()
                        if side and side != "buy":
                            continue
                        oid = OrderJournal._order_id(o)
                        if oid:
                            await asyncio.wait_for(w.ex.cancel_order(oid), timeout=float(self.cfg.low_priority_timeout_sec))
                    except Exception:
                        continue
    async def _refresh_market_snapshot_if_needed(self, now: Optional[float] = None) -> None:
        allow_remote = bool(getattr(self.cfg, "batch_tickers_enabled", False))
        ca = getattr(self, "clock_arbiter", None)
        try:
            if ca is not None and now is None:
                ca.resync()
        except Exception:
            pass
        try:
            now_f = float(now) if now is not None else float(ca.now() if ca is not None else time.time())
        except Exception:
            now_f = float(time.time())
        try:
            min_iv = float(getattr(self.cfg, "batch_tickers_min_interval_sec", 1.0) or 1.0)
        except Exception:
            min_iv = 1.0
        try:
            thr = float(getattr(self.cfg, "market_age_skip_sec", 4.0) or 4.0)
            min_iv = min(float(min_iv), max(0.25, float(thr) * 0.8))
        except Exception:
            pass
        last_ts = float(getattr(self, "_market_snapshot_local_ts", 0.0) or 0.0)
        if last_ts > 1e11:
            try:
                last_ts = float(last_ts) / 1000.0
            except Exception:
                last_ts = float(last_ts)
        if last_ts and (now_f - last_ts) < min_iv:
            return
        t = getattr(self, "_snapshot_task", None)
        if t is not None and not t.done():
            try:
                hard_to = float(os.getenv("MKT_SNAPSHOT_HARD_TIMEOUT_SEC", "20.0") or 20.0)
            except Exception:
                hard_to = 20.0
            try:
                started = float(getattr(self, "_snapshot_task_started_ts", 0.0) or 0.0)
            except Exception:
                started = 0.0
            if started and (now_f - started) > float(max(5.0, hard_to)):
                try:
                    t.cancel()
                except Exception:
                    pass
                try:
                    setattr(self, "_snapshot_task", None)
                except Exception:
                    pass
                try:
                    setattr(self, "_snapshot_task_started_ts", 0.0)
                except Exception:
                    pass
            return
        fail_streak = int(getattr(self, "_snapshot_fail_streak", 0) or 0)
        backoff_until = float(getattr(self, "_snapshot_backoff_until", 0.0) or 0.0)
        if backoff_until and now_f < backoff_until:
            return
        try:
            bt_to = float(os.getenv("BATCH_TICKERS_TIMEOUT_SEC", "8.0") or 8.0)
        except Exception:
            bt_to = 8.0
        bt_to = float(max(2.0, min(25.0, bt_to)))
        try:
            fb_to = float(os.getenv("MARKET_STATS_TIMEOUT_SEC", "5.0") or 5.0)
        except Exception:
            fb_to = 5.0
        fb_to = float(max(1.5, min(20.0, fb_to)))
        async def _fetch_snapshot() -> Tuple[Optional[dict], Optional[str]]:
            try:
                if not allow_remote:
                    raise RuntimeError("REMOTE_DISABLED")
                fn = getattr(self.public, "get_all_tickers_optimized", None) or getattr(self.public, "get_all_tickers", None)
                if fn is not None:
                    data = await asyncio.wait_for(fn(), timeout=bt_to)
                    if isinstance(data, dict):
                        by = data.get("by_symbol") if isinstance(data.get("by_symbol"), dict) else None
                        if isinstance(by, dict) and by:
                            return data, "batch"
                        try:
                            if len(data) >= 5 and all((v is None) or isinstance(v, dict) for v in data.values()):
                                norm = {}
                                for k0, v0 in data.items():
                                    cs = _canon_symbol(k0)
                                    if not cs:
                                        continue
                                    norm[cs] = dict(v0 or {})
                                    norm[cs].setdefault("symbol", cs)
                                if norm:
                                    st = float(time.time())
                                    return {"by_symbol": norm, "server_time": st}, "batch_map"
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                if not allow_remote:
                    raise RuntimeError("REMOTE_DISABLED")
                stats = await asyncio.wait_for(self.public.get_all_market_stats(), timeout=fb_to)
                if isinstance(stats, dict) and stats:
                    st = None
                    try:
                        st = float(ClockArbiter._epoch_to_seconds(stats.get("server_time"))) if isinstance(stats, dict) else None
                    except Exception:
                        st = None
                    if st is None or not (st and math.isfinite(st) and st > 0.0):
                        st = float(time.time())
                    return {"by_symbol": stats, "server_time": st}, "stats"
            except Exception:
                try:
                    cached = getattr(self.public, "_last_market_stats_snapshot", None)
                    lu = float(getattr(self.public, "last_update_time", 0.0) or 0.0)
                    if lu > 1e11:
                        lu = lu / 1000.0
                    age = (float(time.time()) - lu) if lu > 0.0 else 1e9
                    try:
                        max_age = float(os.getenv("MARKET_STATS_CACHE_MAX_AGE_SEC", "20") or 20.0)
                    except Exception:
                        max_age = 20.0
                    if isinstance(cached, dict) and cached and age <= float(max_age):
                        st = lu if (lu > 0.0 and math.isfinite(lu)) else float(time.time())
                        return {"by_symbol": cached, "server_time": st, "_local_ts": st}, "stats_cache"
                except Exception:
                    pass
            try:
                synth = {}
                cache = getattr(self.feed, "_cache", None) or {}
                syms0 = []
                try:
                    ss0 = getattr(self, "supported_symbols", None)
                    if isinstance(ss0, dict):
                        syms0 = list(ss0.keys())
                    elif isinstance(ss0, (list, tuple, set)):
                        syms0 = list(ss0)
                except Exception:
                    syms0 = []
                try:
                    _t_syms = list(self._phoenix_target_symbols() or [])
                except Exception:
                    _t_syms = []
                if _t_syms:
                    try:
                        merged = []
                        seen = set()
                        for _x in (list(_t_syms) + list(syms0 or [])):
                            cs = _canon_symbol(str(_x or ""))
                            if not cs or cs in seen:
                                continue
                            seen.add(cs)
                            merged.append(cs)
                        syms0 = merged
                    except Exception:
                        syms0 = list(_t_syms) + list(syms0 or [])
                if not syms0:
                    syms0 = list(cache.keys())
                try:
                    max_n = int(_env_int("SNAP_SYNTH_MAX_SYMBOLS", 24) or 24)
                except Exception:
                    max_n = 24
                max_n = max(4, min(80, int(max_n)))
                for _s in (syms0 or [])[:max_n]:
                    try:
                        s = _canon_symbol(str(_s or ""))
                        if not s:
                            continue
                        rec = cache.get(s)
                        if rec is None:
                            continue
                        bts, ob = rec
                        mid = float(getattr(ob, "mid", 0.0) or 0.0)
                        if mid <= 0.0:
                            continue
                        synth[s] = {
                            "latest": mid,
                            "bid": float(getattr(ob, "bid", 0.0) or 0.0),
                            "ask": float(getattr(ob, "ask", 0.0) or 0.0),
                            "spread_bps": float(getattr(ob, "spread_bps", 0.0) or 0.0),
                            "_src": "depth",
                            "_ts": float(bts),
                        }
                    except Exception:
                        continue
                if synth:
                    try:
                        st = float(time.time())
                    except Exception:
                        st = float(now1)
                    return {"by_symbol": synth, "server_time": st, "_synthetic": True}, "synth"
            except Exception:
                pass
            try:
                synth2 = {}
                px_hist2 = getattr(self, "_phoenix_px_hist", None)
                if isinstance(px_hist2, dict) and px_hist2:
                    syms1 = []
                    try:
                        ss1 = getattr(self, "supported_symbols", None)
                        if isinstance(ss1, dict):
                            syms1 = list(ss1.keys())
                        elif isinstance(ss1, (list, tuple, set)):
                            syms1 = list(ss1)
                    except Exception:
                        syms1 = []
                    if not syms1:
                        try:
                            syms1 = list(getattr(self.cfg, "symbols", []) or [])
                        except Exception:
                            syms1 = []
                    if not syms1:
                        syms1 = list(px_hist2.keys())
                    try:
                        max_n2 = int(_env_int("SNAP_PXHIST_MAX_SYMBOLS", 48) or 48)
                    except Exception:
                        max_n2 = 48
                    max_n2 = max(4, min(200, int(max_n2)))
                    nowh = float(time.time())
                    for _s in (syms1 or [])[:max_n2]:
                        try:
                            s = _canon_symbol(str(_s or ""))
                            if not s:
                                continue
                            dq = px_hist2.get(s)
                            if not dq:
                                try:
                                    for a in (_symbol_aliases(s) or []):
                                        dq = px_hist2.get(_canon_symbol(a))
                                        if dq:
                                            break
                                except Exception:
                                    dq = None
                            if not dq:
                                continue
                            try:
                                t_last, p_last = dq[-1]
                            except Exception:
                                continue
                            p_last = float(p_last or 0.0)
                            if p_last <= 0.0:
                                continue
                            t_last = float(t_last or 0.0)
                            if t_last > nowh + 5.0:
                                t_last = nowh
                            synth2[s] = {"latest": p_last, "_src": "px_hist", "_ts": t_last}
                        except Exception:
                            continue
                    if synth2:
                        try:
                            st = float(time.time())
                        except Exception:
                            st = float(nowh)
                        return {"by_symbol": synth2, "server_time": st, "_local_ts": st, "_synthetic": True, "_synth_src": "px_hist"}, "px_hist"
            except Exception:
                pass
            return None, None
        async def _apply_snapshot_result(res: Optional[dict], source: Optional[str]) -> None:
            try:
                setattr(self, "_snapshot_task", None)
            except Exception:
                pass
            now2 = float(time.time())
            if not res or not isinstance(res, dict) or not isinstance(res.get("by_symbol"), dict) or not res["by_symbol"]:
                fs = int(getattr(self, "_snapshot_fail_streak", 0) or 0) + 1
                try:
                    setattr(self, "_snapshot_fail_streak", fs)
                except Exception:
                    pass
                try:
                    base = float(os.getenv("MKT_SNAPSHOT_BACKOFF_BASE_SEC", "6") or 6.0)
                except Exception:
                    base = 6.0
                try:
                    cap = float(os.getenv("MKT_SNAPSHOT_BACKOFF_CAP_SEC", "60") or 60.0)
                except Exception:
                    cap = 60.0
                base = float(max(0.5, min(60.0, base)))
                cap = float(max(base, min(600.0, cap)))
                backoff_sec = float(min(cap, base * (2 ** min(6, max(0, fs - 1))))) if fs > 0 else 0.0
                try:
                    setattr(self, "_snapshot_backoff_until", now2 + backoff_sec if backoff_sec > 0 else 0.0)
                except Exception:
                    pass
                try:
                    self._log.warning("event=MKT_SNAPSHOT_FAIL streak=%d backoff=%.0fs", int(fs), float(backoff_sec))
                except Exception:
                    pass
                try:
                    self._update_market_snapshot_confidence(getattr(self, "_market_snapshot", {}) or {}, source="fail", now_ts=now2)
                except Exception:
                    pass
                return
            by_symbol = res.get("by_symbol") or {}
            try:
                if isinstance(by_symbol, dict):
                    _norm_bs: Dict[str, dict] = {}
                    for _k0, _v0 in (by_symbol or {}).items():
                        cs = _canon_symbol(_k0)
                        if not cs:
                            continue
                        if not isinstance(_v0, dict):
                            continue
                        row = dict(_v0 or {})
                        row.setdefault("symbol", cs)
                        _norm_bs[cs] = row
                    if _norm_bs:
                        by_symbol = _norm_bs
            except Exception:
                pass
            try:
                if str(source or "").lower() == "synth":
                    prev = getattr(self, "_market_snapshot", None)
                    if isinstance(prev, dict) and prev:
                        merged = dict(prev)
                        merged.update(by_symbol)
                        by_symbol = merged
                setattr(self, "_market_snapshot", by_symbol)
                try:
                    _lts = float(res.get("_local_ts") or now2)
                    if _lts > 1e11:
                        _lts = _lts / 1000.0
                except Exception:
                    _lts = float(now2)
                setattr(self, "_market_snapshot_local_ts", float(_lts))
                try:
                    setattr(self, "_market_snapshot_mono_ts", float(time.monotonic()))
                except Exception:
                    pass
                try:
                    pho = getattr(self, "phoenix", None)
                except Exception:
                    pho = None
                try:
                    ana = getattr(self, "analyzer", None)
                except Exception:
                    ana = None
                try:
                    sym_u = getattr(self, "_phoenix_sym_last_update", None)
                    if not isinstance(sym_u, dict):
                        sym_u = {}
                        setattr(self, "_phoenix_sym_last_update", sym_u)
                except Exception:
                    sym_u = {}
                try:
                    px_hist = getattr(self, "_phoenix_px_hist", None)
                    if not isinstance(px_hist, dict):
                        px_hist = {}
                        setattr(self, "_phoenix_px_hist", px_hist)
                except Exception:
                    px_hist = {}
                try:
                    boot = getattr(self, "_phoenix_flow_bootstrap", None)
                    if not isinstance(boot, set):
                        boot = set()
                        setattr(self, "_phoenix_flow_bootstrap", boot)
                except Exception:
                    boot = set()
                try:
                    _tl0 = list(self._phoenix_target_symbols() or [])
                except Exception:
                    _tl0 = []
                target_list = []
                try:
                    seen = set()
                    for _s0 in (_tl0 or []):
                        cs = _canon_symbol(_s0)
                        if not cs:
                            continue
                        if cs in seen:
                            continue
                        seen.add(cs)
                        target_list.append(cs)
                except Exception:
                    target_list = [(_canon_symbol(s) or str(s or '').strip().upper()) for s in (_tl0 or []) if s]
                try:
                    target_set = set(target_list)
                except Exception:
                    target_set = set()
                try:
                    seed_eps = float(os.getenv("PHOENIX_FLOW_SEED_PCT", "0.00001") or 0.00001)  #
                except Exception:
                    seed_eps = 0.00001
                try:
                    gap_reset = float(os.getenv("PHOENIX_FLOW_GAP_RESET_SEC", "300") or 300.0)
                except Exception:
                    gap_reset = 300.0
                try:
                    accept_dt = float(os.getenv("PHOENIX_FLOW_MIN_DT_SEC", "0.05") or 0.05)
                except Exception:
                    accept_dt = 0.05
                try:
                    clamp_pct = float(os.getenv("TOP8_CHANGE_CLAMP_PCT", 30.0) or 30.0)
                except Exception:
                    clamp_pct = 30.0
                try:
                    max_points = int(_env_int("TOP8_CHANGE_MAX_POINTS", 520) or 520)
                except Exception:
                    max_points = 520
                max_points = max(60, min(5000, int(max_points)))
                now_ts0 = float(time.time())
                def _mid_from_row(rr):
                    try:
                        if not isinstance(rr, dict):
                            return 0.0
                        for _k in ("mid", "mark", "markPrice", "last", "last_price", "lastPrice", "last_trade_price",
                                   "lastTradePrice", "price", "close", "closePrice", "c", "p", "rate", "value",
                                   "latest", "ltp", "tradePrice"):
                            _v = rr.get(_k)
                            try:
                                _vf = float(_safe_float(_v, default=0.0, translate_digits=True, finite=True, na_values=True, strip=True) or 0.0)
                            except Exception:
                                _vf = 0.0
                            if _vf > 0.0:
                                return float(_vf)
                    except Exception:
                        pass
                    return 0.0
                def _open_from_row(rr, last_mid):
                    try:
                        if not isinstance(rr, dict):
                            rr = {}
                        for _k in ("open", "openPrice", "open_price", "o", "open24h", "open_24h", "open24H", "prevClose", "prev_close", "yesterdayClose"):
                            _v = rr.get(_k)
                            try:
                                _vf = float(_safe_float(_v, default=0.0, translate_digits=True, finite=True, na_values=True, strip=True) or 0.0)
                            except Exception:
                                _vf = 0.0
                            if _vf > 0.0:
                                return float(_vf)
                        pct = None
                        for _k in ("changePercent", "percentChange", "priceChangePercent", "chgPct", "change_pct", "change24hPct", "change_24h_pct", "percent"):
                            _v = rr.get(_k)
                            try:
                                _vf = float(_safe_float(_v, default=0.0, translate_digits=True, finite=True, na_values=True, strip=True) or 0.0)
                            except Exception:
                                _vf = 0.0
                            if _vf != 0.0 and math.isfinite(_vf):
                                pct = float(_vf)
                                break
                        if pct is not None:
                            frac = float(pct)
                            if abs(frac) > 2.0:
                                frac = frac / 100.0
                            den = 1.0 + float(frac)
                            if den != 0.0 and math.isfinite(den) and float(last_mid) > 0.0:
                                op = float(last_mid) / den
                                if op > 0.0 and math.isfinite(op):
                                    return float(op)
                        chg = None
                        for _k in ("change", "priceChange", "delta", "price_delta", "d"):
                            _v = rr.get(_k)
                            try:
                                _vf = float(_safe_float(_v, default=0.0, translate_digits=True, finite=True, na_values=True, strip=True) or 0.0)
                            except Exception:
                                _vf = 0.0
                            if _vf != 0.0 and math.isfinite(_vf):
                                chg = float(_vf)
                                break
                        if chg is not None and float(last_mid) > 0.0:
                            op = float(last_mid) - float(chg)
                            if op > 0.0 and math.isfinite(op):
                                return float(op)
                    except Exception:
                        pass
                    try:
                        return float(last_mid) if float(last_mid) > 0.0 else 0.0
                    except Exception:
                        return 0.0
                def _bootstrap_prices(open_px, last_px, n):
                    try:
                        n = int(max(2, n))
                    except Exception:
                        n = 16
                    try:
                        op = float(open_px) if float(open_px) > 0.0 else float(last_px)
                    except Exception:
                        op = float(last_px)
                    try:
                        lp = float(last_px) if float(last_px) > 0.0 else float(op) * (1.0 + float(seed_eps))
                    except Exception:
                        lp = float(op) * (1.0 + float(seed_eps))
                    try:
                        if lp > 0.0 and abs(op - lp) / lp < 1e-12:
                            op = lp
                    except Exception:
                        pass
                    out = []
                    for i in range(int(n)):
                        frac = float(i) / float(max(1, n - 1))
                        px = (op * (1.0 - frac)) + (lp * frac)
                        wig = 1.0 + ((-1.0 if (i % 2 == 0) else 1.0) * float(seed_eps) * 0.25)
                        try:
                            px = float(px) * float(wig)
                        except Exception:
                            pass
                        out.append(max(1e-12, float(px)))
                    return out
                try:
                    feed = getattr(self, "feed", None)
                except Exception:
                    feed = None
                spot_cache = None
                mid_hist = None
                try:
                    if feed is not None:
                        spot_cache = getattr(feed, "_spot_cache", None)
                        mid_hist = getattr(feed, "_mid_hist", None)
                except Exception:
                    spot_cache = None
                    mid_hist = None
                try:
                    if isinstance(by_symbol, dict) and target_set:
                        feed_cache = None
                        try:
                            if feed is not None:
                                feed_cache = getattr(feed, "_cache", None)
                        except Exception:
                            feed_cache = None
                        for _tsym in list(target_set):
                            try:
                                s = _canon_symbol(str(_tsym or ""))
                            except Exception:
                                s = str(_tsym or "").strip().upper()
                            if not s:
                                continue
                            if s in by_symbol:
                                continue
                            mid = 0.0
                            tsx = float(now_ts0)
                            try:
                                if isinstance(feed_cache, dict):
                                    rec = feed_cache.get(s)
                                    if rec:
                                        bts, ob = rec
                                        mid = float(getattr(ob, "mid", 0.0) or 0.0)
                                        tsx = float(bts or tsx)
                            except Exception:
                                pass
                            try:
                                if mid <= 0.0 and isinstance(spot_cache, dict):
                                    rec2 = spot_cache.get(s)
                                    if rec2:
                                        ts2, px2 = rec2
                                        mid = float(px2 or 0.0)
                                        tsx = float(ts2 or tsx)
                            except Exception:
                                pass
                            try:
                                if mid <= 0.0 and isinstance(px_hist, dict):
                                    dq0 = px_hist.get(s)
                                    if dq0:
                                        ts3, px3 = dq0[-1]
                                        mid = float(px3 or 0.0)
                                        tsx = float(ts3 or tsx)
                            except Exception:
                                pass
                            if mid > 0.0 and math.isfinite(float(mid)):
                                by_symbol[s] = {"symbol": s, "latest": float(mid), "_src": "synth_target", "_ts": float(tsx)}
                except Exception:
                    pass
                try:
                    if isinstance(by_symbol, dict) and target_list:
                        missing_all = [s for s in (target_list or []) if s and s not in by_symbol]
                        try:
                            _st0 = getattr(self, "_mkt_store", None)
                            if _st0 is not None and hasattr(_st0, "should_attempt"):
                                try:
                                    bo_base = float(_env_float("PHOENIX_TAIL_BACKOFF_BASE_SEC", 6.0) or 6.0)
                                except Exception:
                                    bo_base = 6.0
                                try:
                                    bo_cap = float(_env_float("PHOENIX_TAIL_BACKOFF_CAP_SEC", 120.0) or 120.0)
                                except Exception:
                                    bo_cap = 120.0
                                missing_all = [s for s in missing_all if _st0.should_attempt(s, now=float(now_ts0), base_sec=float(bo_base), cap_sec=float(bo_cap))]
                        except Exception:
                            pass
                        try:
                            _st0 = getattr(self, "_mkt_store", None)
                            if _st0 is not None and hasattr(_st0, "should_attempt"):
                                try:
                                    bo_base = float(_env_float("PHOENIX_TAIL_BACKOFF_BASE_SEC", 6.0) or 6.0)
                                except Exception:
                                    bo_base = 6.0
                                try:
                                    bo_cap = float(_env_float("PHOENIX_TAIL_BACKOFF_CAP_SEC", 120.0) or 120.0)
                                except Exception:
                                    bo_cap = 120.0
                                missing_all = [s for s in missing_all if _st0.should_attempt(s, now=float(now_ts0), base_sec=float(bo_base), cap_sec=float(bo_cap))]
                        except Exception:
                            pass
                    else:
                        missing_all = []
                    missing = []
                    if missing_all:
                        try:
                            max_miss = int(_env_int("PHOENIX_TARGET_SPOT_FETCH_MAX", 8) or 8)
                        except Exception:
                            max_miss = 8
                        max_miss = max(0, min(32, int(max_miss)))
                        try:
                            rr_i = int(getattr(self, "_phoenix_target_spot_rr_i", 0) or 0)
                        except Exception:
                            rr_i = 0
                        if rr_i < 0:
                            rr_i = 0
                        if rr_i >= len(missing_all):
                            rr_i = 0
                        missing_rot = list(missing_all[rr_i:]) + list(missing_all[:rr_i])
                        missing = list(missing_rot)[:max_miss]
                        try:
                            setattr(self, "_phoenix_target_spot_rr_i", int((rr_i + len(missing)) % max(1, len(missing_all))))
                        except Exception:
                            pass
                        async def _fetch_one(_s: str):
                            try:
                                feed0 = getattr(self, "feed", None)
                                if feed0 is None or not hasattr(feed0, "fetch_spot"):
                                    return _s, None
                                px = await asyncio.wait_for(feed0.fetch_spot(_s), timeout=1.2)
                                try:
                                    if px is not None and float(px) > 0.0:
                                        return _s, float(px)
                                except Exception:
                                    return _s, None
                            except Exception:
                                return _s, None
                            return _s, None
                        fetched = await asyncio.gather(*[_fetch_one(s) for s in missing], return_exceptions=True)
                        for it in fetched:
                            try:
                                if isinstance(it, Exception):
                                    continue
                                s2, px2 = it
                                if not s2 or px2 is None:
                                    continue
                                by_symbol[str(s2)] = {"symbol": str(s2), "latest": float(px2), "_src": "spot_fetch", "_ts": float(now_ts0)}
                                try:
                                    if isinstance(spot_cache, dict):
                                        spot_cache[str(s2)] = (float(now_ts0), float(px2))
                                except Exception:
                                    pass
                            except Exception:
                                continue
                        try:
                            _st = getattr(self, "_mkt_store", None)
                            if _st is not None:
                                for s2 in (missing or []):
                                    try:
                                        cs2 = _canon_symbol(str(s2 or ""))
                                    except Exception:
                                        cs2 = str(s2 or "").strip().upper()
                                    if cs2 and cs2 not in by_symbol:
                                        _st.mark_missing(cs2, reason="SPOT_FETCH_FAIL")
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    flow_all = bool(_env_bool("PHOENIX_FLOW_PXHIST_ALL", False))
                except Exception:
                    flow_all = False
                try:
                    yield_every = int(_env_int("PHOENIX_FLOW_YIELD_EVERY", 150) or 150)
                except Exception:
                    yield_every = 150
                yield_every = int(max(25, min(500, yield_every)))
                try:
                    it0 = (by_symbol.items() if isinstance(by_symbol, dict) else [])
                    if (not flow_all) and target_list and isinstance(by_symbol, dict):
                        it0 = ((s, by_symbol.get(s)) for s in (target_list or []) if s and by_symbol.get(s))
                except Exception:
                    it0 = (by_symbol.items() if isinstance(by_symbol, dict) else [])
                i0 = 0
                for sym, rr in it0:
                    i0 += 1
                    if (i0 % yield_every) == 0:
                        try:
                            await asyncio.sleep(0)
                        except Exception:
                            pass
                    try:
                        s = _canon_symbol(str(sym or ""))
                    except Exception:
                        s = str(sym or "").strip().upper()
                    if not s:
                        continue
                    if not isinstance(rr, dict):
                        rr = {}
                    mid = float(_mid_from_row(rr) or 0.0)
                    if mid <= 0.0:
                        try:
                            _st = getattr(self, "_mkt_store", None)
                            if _st is not None and (s in target_set):
                                try:
                                    sp = getattr(getattr(self, "specs", None), "_cache", None)
                                    if isinstance(sp, dict) and sp and (not sp.get(s)):
                                        _st.mark_unsupported(s, reason="UNSUPPORTED")
                                    else:
                                        _st.mark_missing(s, reason="NO_TICK")
                                except Exception:
                                    _st.mark_missing(s, reason="NO_TICK")
                        except Exception:
                            pass
                        continue
                    try:
                        _st = getattr(self, "_mkt_store", None)
                        if _st is not None:
                            tsx = float(now_ts0)
                            try:
                                tsx = float(rr.get("_ts") or rr.get("ts") or rr.get("timestamp") or rr.get("time") or now_ts0)
                                if tsx > 1e11:
                                    tsx = tsx / 1000.0
                            except Exception:
                                tsx = float(now_ts0)
                            _src = str(rr.get("_src") or source or "snap")
                            _st.update_ok(s, mid=float(mid), ts=float(tsx), src=_src, quality=100)
                    except Exception:
                        pass
                    try:
                        dq = px_hist.get(s)
                        if dq is None:
                            dq = __import__("collections").deque(maxlen=int(max_points))
                            px_hist[s] = dq
                        if dq and (now_ts0 - float(dq[-1][0] or 0.0)) > float(gap_reset):
                            dq.clear()
                        if not dq:
                            dq.append((now_ts0 - 0.2, float(mid)))
                        else:
                            if (now_ts0 - float(dq[-1][0] or 0.0)) < float(accept_dt):
                                try:
                                    sym_u[s] = float(now_ts0)
                                except Exception:
                                    pass
                                continue
                            try:
                                last_p = float(dq[-1][1] or 0.0)
                                if last_p > 0.0:
                                    one_tick = ((float(mid) - last_p) / last_p) * 100.0
                                    if math.isfinite(one_tick) and abs(one_tick) > float(clamp_pct):
                                        try:
                                            sym_u[s] = float(now_ts0)
                                        except Exception:
                                            pass
                                        continue
                            except Exception:
                                pass
                        dq.append((now_ts0, float(mid)))
                    except Exception:
                        pass
                    try:
                        sym_u[s] = float(now_ts0)
                    except Exception:
                        pass
                    try:
                        if isinstance(spot_cache, dict):
                            spot_cache[s] = (float(now_ts0), float(mid))
                    except Exception:
                        pass
                    try:
                        if isinstance(mid_hist, dict):
                            dqmh = mid_hist.get(s)
                            if dqmh is None:
                                dqmh = __import__("collections").deque(maxlen=240)
                                mid_hist[s] = dqmh
                            dqmh.append(float(mid))
                    except Exception:
                        pass
                    if s not in target_set:
                        continue
                    try:
                        if ana is not None and hasattr(ana, "update"):
                            hmap = getattr(ana, "_hist", None)
                            if isinstance(hmap, dict):
                                hdq = hmap.get(s)
                                if hdq is None or len(hdq) < 3:
                                    open_px = _open_from_row(rr, float(mid))
                                    try:
                                        seed_n = int(getattr(getattr(self, "cfg", None), "phoenix_rsi_period", 14) or 14) + 1
                                    except Exception:
                                        seed_n = 15
                                    seed_n = int(max(16, min(64, seed_n)))
                                    series = _bootstrap_prices(open_px, float(mid), int(seed_n))
                                    hdq2 = hdq if isinstance(hdq, deque) else __import__("collections").deque(maxlen=int(getattr(ana, "maxlen", 120) or 120))
                                    for x in series[:-1]:
                                        try:
                                            hdq2.append(float(x))
                                        except Exception:
                                            pass
                                    hmap[s] = hdq2
                            ana.update(s, float(mid))
                    except Exception:
                        pass
                    try:
                        if pho is not None and hasattr(pho, "update"):
                            if s not in boot:
                                open_px = _open_from_row(rr, float(mid))
                                try:
                                    rsi_p = int(getattr(getattr(self, "cfg", None), "phoenix_rsi_period", 14) or 14)
                                except Exception:
                                    rsi_p = 14
                                try:
                                    sh_n = int(getattr(getattr(self, "cfg", None), "phoenix_shadow_window", 20) or 20)
                                except Exception:
                                    sh_n = 20
                                seed_n = int(max(16, int(rsi_p) + 1, int(sh_n)))
                                seed_n = int(min(64, seed_n))
                                series = _bootstrap_prices(open_px, float(mid), int(seed_n))
                                for x in series[:-1]:
                                    try:
                                        pho.update(s, None, None, float(x), depth_latency_ms=None)
                                    except TypeError:
                                        pho.update(s, None, None, float(x))
                                try:
                                    boot.add(s)
                                except Exception:
                                    pass
                            try:
                                pho.update(s, None, None, float(mid), depth_latency_ms=None)
                            except TypeError:
                                pho.update(s, None, None, float(mid))
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                _st = getattr(self, "_mkt_store", None)
                if _st is not None and target_list:
                    try:
                        max_explicit = int(_env_int("PHOENIX_TARGET_EXPLICIT_MAX", 80) or 80)
                    except Exception:
                        max_explicit = 80
                    max_explicit = int(max(8, min(200, max_explicit)))
                    for s in (target_list or [])[:max_explicit]:
                        if not s:
                            continue
                        rr0 = (by_symbol.get(s) if isinstance(by_symbol, dict) else None)
                        if isinstance(rr0, dict) and float(_mid_from_row(rr0) or 0.0) > 0.0:
                            continue
                        try:
                            sp = getattr(getattr(self, "specs", None), "_cache", None)
                            if isinstance(sp, dict) and sp and (not sp.get(s)):
                                _st.mark_unsupported(s, reason="UNSUPPORTED")
                            else:
                                _st.mark_missing(s, reason="NO_TICK")
                        except Exception:
                            _st.mark_missing(s, reason="NO_TICK")
            except Exception:
                pass
            try:
                self._update_market_snapshot_confidence(by_symbol, source=str(source or ""), now_ts=now2)
            except Exception:
                pass
            st = res.get("server_time")
            stf: Optional[float] = None
            try:
                stf0 = float(ClockArbiter._epoch_to_seconds(st))
                if stf0 > 0.0 and math.isfinite(stf0):
                    stf = float(stf0)
            except Exception:
                stf = None
            if stf is not None:
                try:
                    setattr(self, "_market_server_time", float(stf))
                except Exception:
                    pass
                raw_skew = float("inf")
                try:
                    ca2 = getattr(self, "clock_arbiter", None)
                    if ca2 is not None:
                        ca2.observe(float(now2), float(stf))
                        raw_skew = float(ca2.skew_s(float(now2), float(stf)))
                    else:
                        raw_skew = abs(float(now2) - float(stf))
                except Exception:
                    raw_skew = abs(float(now2) - float(stf))
                try:
                    if raw_skew >= 0.0 and math.isfinite(raw_skew):
                        win = getattr(self, "_radar_skew_ma_window", None)
                        if not isinstance(win, deque):
                            win = __import__("collections").deque(maxlen=15)
                            setattr(self, "_radar_skew_ma_window", win)
                        win.append(float(raw_skew))
                        xs = [float(x) for x in list(win) if math.isfinite(float(x)) and float(x) >= 0.0]
                        if xs:
                            raw_skew = float(sum(xs) / max(1, len(xs)))
                except Exception:
                    pass
                try:
                    setattr(self, "_market_age_s", float(max(0.0, raw_skew)))
                except Exception:
                    pass
            else:
                try:
                    prev = float(getattr(self, "_market_age_s", 0.0) or 0.0)
                    if not math.isfinite(prev) or prev < 0.0:
                        prev = 0.0
                    setattr(self, "_market_age_s", float(prev))
                except Exception:
                    try:
                        setattr(self, "_market_age_s", 0.0)
                    except Exception:
                        pass
                try:
                    st_prev = float(getattr(self, "_market_server_time", 0.0) or 0.0)
                    if st_prev <= 0.0 or (not math.isfinite(st_prev)):
                        setattr(self, "_market_server_time", float(now2))
                except Exception:
                    pass
            try:
                self.public.last_update_time = float(now2)
            except Exception:
                pass
            try:
                src = str(source or "")
                setattr(self, "_market_last_err", "" if src == "batch" else f"{src}_FALLBACK")
            except Exception:
                pass
            try:
                setattr(self, "_snapshot_fail_streak", 0)
                setattr(self, "_snapshot_backoff_until", 0.0)
            except Exception:
                pass
            try:
                self._log.info("event=MKT_SNAPSHOT_OK source=%s size=%d", str(source or "?"), int(len(by_symbol)))
            except Exception:
                pass
        async def _runner() -> Tuple[Optional[dict], Optional[str]]:
            return await _fetch_snapshot()
        task = asyncio.create_task(_runner())
        setattr(self, "_snapshot_task", task)
        try:
            setattr(self, "_snapshot_task_started_ts", float(now_f))
        except Exception:
            pass
        def _done_cb(t_: asyncio.Task) -> None:
            try:
                res, src = t_.result()
            except Exception:
                res, src = None, None
            try:
                asyncio.create_task(_apply_snapshot_result(res, src))
            except Exception:
                pass
        try:
            task.add_done_callback(_done_cb)
        except Exception:
            pass
        return
    def _update_market_snapshot_confidence(self, by_symbol: dict, *, source: str = "", now_ts: float | None = None) -> None:
        now0 = float(time.time()) if now_ts is None else float(now_ts)
        try:
            conf_ok = float(_env_float("SNAP_CONFIDENCE_OK", 80.0) or 80.0)
        except Exception:
            conf_ok = 80.0
        try:
            conf_crit = float(_env_float("SNAP_CONFIDENCE_CRITICAL", 40.0) or 40.0)
        except Exception:
            conf_crit = 40.0
        try:
            penalty_missing = float(_env_float("SNAP_PENALTY_MISSING", 0.8) or 0.8)
        except Exception:
            penalty_missing = 0.8
        try:
            penalty_stale_sec = float(_env_float("SNAP_PENALTY_STALE_SEC", 0.1) or 0.1)
        except Exception:
            penalty_stale_sec = 0.1
        try:
            stale_max_sec = float(_env_float("SNAP_STALE_MAX_SEC", 60.0) or 60.0)
        except Exception:
            stale_max_sec = 60.0
        try:
            penalty_spread_high = float(_env_float("SNAP_PENALTY_SPREAD_HIGH", 0.4) or 0.4)
        except Exception:
            penalty_spread_high = 0.4
        try:
            streak_factor = float(_env_float("SNAP_STREAK_FACTOR", 1.5) or 1.5)
        except Exception:
            streak_factor = 1.5
        try:
            max_syms = int(_env_int("SNAP_SCORE_MAX_SYMBOLS", int(_env_int("SNAP_SCORE_HEALTH_MAX_SYMBOLS", 16) or 16)) or 16)
        except Exception:
            max_syms = 12
        max_syms = max(8, min(256, int(max_syms)))
        snap_age = None
        try:
            mts = float(getattr(self, "_market_snapshot_local_ts", 0.0) or 0.0)
            if mts > 0.0:
                snap_age = max(0.0, now0 - mts)
        except Exception:
            snap_age = None
        by_symbol = by_symbol or {}
        by_canon: dict = {}
        try:
            if isinstance(by_symbol, dict):
                for k, v in by_symbol.items():
                    try:
                        kk = _canon_symbol(str(k or ""))
                        if kk:
                            by_canon[kk] = v
                    except Exception:
                        continue
        except Exception:
            by_canon = {}
        syms: list[str] = []
        try:
            ss = getattr(self, "supported_symbols", None)
            if isinstance(ss, dict):
                syms = list(ss.keys())
            elif isinstance(ss, (list, tuple, set)):
                syms = list(ss)
        except Exception:
            syms = []
        if not syms:
            try:
                syms = list(getattr(self.cfg, "symbols", []) or [])
            except Exception:
                syms = []
        if not syms:
            syms = list(by_canon.keys())
        out_syms: list[str] = []
        want_syms: list[str] = []
        try:
            want_syms = list(getattr(self, "_phoenix_health_symbols", None)() or []) if hasattr(self, "_phoenix_health_symbols") else list(self._phoenix_target_symbols() or [])
        except Exception:
            want_syms = []
        for s in (want_syms + (syms or [])):
            try:
                cs = _canon_symbol(str(s or ""))
                if not cs:
                    continue
                try:
                    if getattr(self, "feed", None) is not None and self.feed.is_ignored(cs):
                        continue
                except Exception:
                    pass
                if cs not in out_syms:
                    out_syms.append(cs)
            except Exception:
                continue
            if len(out_syms) >= max_syms:
                break
        try:
            streaks = getattr(self, "_snap_field_streaks", None)
            if not isinstance(streaks, dict):
                streaks = {}
                setattr(self, "_snap_field_streaks", streaks)
        except Exception:
            streaks = {}
        def _f(x) -> float:
            try:
                return float(_safe_float(
                    x,
                    default=0.0,
                    translate_digits=True,
                    allow_percent=True,
                    finite=True,
                    na_values=True,
                    strip=True,
                ) or 0.0)
            except Exception:
                try:
                    return float(x)
                except Exception:
                    return 0.0
        w_mid = 0.55
        w_spread = 0.20
        w_fresh = 0.25
        w_sum = (w_mid + w_spread + w_fresh) or 1.0
        cache = {}
        try:
            cache = getattr(self.feed, "_cache", None) or {}
        except Exception:
            cache = {}
        sym_scores: list[float] = []
        sym_conf_map: dict = {}
        for s in (out_syms or []):
            row = by_canon.get(s) if isinstance(by_canon, dict) else None
            if not isinstance(row, dict):
                row = {}
            mid = 0.0
            for k in ("mid", "latest", "last", "price", "close", "c", "p"):
                if k in row:
                    mid = _f(row.get(k))
                    if mid > 0.0:
                        break
            if mid <= 0.0:
                try:
                    for k in ("ticker", "data"):
                        sub = row.get(k)
                        if isinstance(sub, dict):
                            for kk in ("mid", "latest", "last", "price", "close"):
                                mid = _f(sub.get(kk))
                                if mid > 0.0:
                                    raise StopIteration
                except StopIteration:
                    pass
                except Exception:
                    pass
            book_mid = 0.0
            book_spread = 0.0
            book_age = None
            try:
                rec = cache.get(s)
                if rec is not None:
                    bts, ob = rec
                    book_mid = _f(getattr(ob, "mid", None))
                    book_spread = _f(getattr(ob, "spread_bps", None))
                    try:
                        book_age = max(0.0, now0 - float(bts))
                    except Exception:
                        book_age = _f(getattr(ob, "age_sec", None)) or 0.0
            except Exception:
                pass
            used_depth = False
            if (mid <= 0.0) and (book_mid > 0.0):
                mid = float(book_mid)
                used_depth = True
            age = 0.0
            try:
                row_ts = 0.0
                try:
                    for tk in ("_ts", "ts", "t", "time", "timestamp", "server_time"):
                        if isinstance(row, dict) and (tk in row):
                            row_ts = _f(row.get(tk))
                            if row_ts:
                                break
                except Exception:
                    row_ts = 0.0
                if row_ts > 1e11:
                    try:
                        row_ts = float(row_ts) / 1000.0
                    except Exception:
                        row_ts = float(row_ts)
                row_age = None
                try:
                    if row_ts and math.isfinite(float(row_ts)) and float(row_ts) > 0.0:
                        if (float(row_ts) <= float(now0) + 10.0) and (float(row_ts) >= float(now0) - 7.0 * 24.0 * 3600.0):
                            row_age = max(0.0, float(now0) - float(row_ts))
                except Exception:
                    row_age = None
                if used_depth and (book_age is not None):
                    age = float(book_age)
                elif row_age is not None:
                    age = float(row_age)
                elif snap_age is not None:
                    age = float(snap_age)
                else:
                    age = 0.0
            except Exception:
                age = 0.0
            spread_bps = 0.0
            try:
                spread_bps = _f(row.get("spread_bps"))
            except Exception:
                spread_bps = 0.0
            if spread_bps <= 0.0 and book_spread > 0.0:
                spread_bps = float(book_spread)
            mid_key = f"{s}.mid"
            mid_fail = (mid <= 0.0)
            try:
                st_prev = int(streaks.get(mid_key, 0) or 0)
            except Exception:
                st_prev = 0
            if mid_fail:
                st_now = st_prev + 1
                streaks[mid_key] = int(st_now)
            else:
                try:
                    if mid_key in streaks:
                        streaks.pop(mid_key, None)
                except Exception:
                    pass
                st_now = 0
            if mid_fail:
                pen_mid = float(penalty_missing)
            else:
                pen_mid = 0.0
            try:
                expn = max(0, int(st_now) - 1)
                if expn > 0:
                    pen_mid = min(1.0, float(pen_mid) * (float(streak_factor) ** float(expn)))
            except Exception:
                pass
            if age > stale_max_sec:
                pen_fresh = 1.0
            else:
                pen_fresh = min(1.0, max(0.0, float(age) * float(penalty_stale_sec)))
            if spread_bps <= 0.0:
                pen_spread = 0.0 if used_depth else (0.25 * float(penalty_missing))
            else:
                if spread_bps > 200.0:
                    pen_spread = float(penalty_spread_high)
                elif spread_bps > 100.0:
                    try:
                        pen_spread = ((spread_bps - 100.0) / 100.0) * float(penalty_spread_high)
                    except Exception:
                        pen_spread = float(penalty_spread_high)
                else:
                    pen_spread = 0.0
                pen_spread = max(0.0, min(1.0, float(pen_spread)))
            pen = (w_mid * pen_mid + w_spread * pen_spread + w_fresh * pen_fresh) / w_sum
            pen = max(0.0, min(1.0, float(pen)))
            score = 100.0 * (1.0 - pen)
            score = max(0.0, min(100.0, float(score)))
            sym_scores.append(float(score))
            sym_conf_map[s] = float(score)
        if not sym_scores:
            confidence = 0.0
        else:
            confidence = float(sum(sym_scores) / max(1, len(sym_scores)))
        state = "OK"
        if confidence >= float(conf_ok):
            state = "OK"
        elif confidence >= float(conf_crit):
            state = "DEGRADED"
        else:
            state = "CRITICAL"
        try:
            setattr(self, "_snap_confidence", float(confidence))
            setattr(self, "_snap_state", str(state))
            setattr(self, "_snap_source", str(source or ""))
            setattr(self, "_snap_last_calc_ts", float(now0))
            setattr(self, "_snap_symbol_conf", dict(sym_conf_map))
        except Exception:
            pass
    async def _refresh_market_focus_if_needed(self) -> None:
        try:
            _always = bool(_env_bool("FOCUS_SCAN_ALWAYS_ON", _env_bool("TERMUX_MODE", False)))
        except Exception:
            _always = bool(_env_bool("TERMUX_MODE", False))
        if (not _always) and (not any(bool(getattr(w.cfg, "autonomous_ai", False)) for w in self.wallets.values())):
            return
        now = time.time()
        scan_ts = float(getattr(self, "last_market_scan", 0.0) or 0.0)
        if scan_ts <= 0.0:
            scan_ts = float(getattr(self, "_focus_last_scan_ts", 0.0) or 0.0)
        scan_ts = scan_ts / 1000.0 if scan_ts and scan_ts > 1e11 else scan_ts
        interval = float(_env_float("FOCUS_SCAN_INTERVAL_SEC", (60.0 if _env_bool("TERMUX_MODE", False) else 1800.0)))
        if (now - scan_ts) < interval:
            return
        try:
            to = float(os.getenv("FOCUS_SCAN_TIMEOUT_SEC", "35.0") or 12.0)
        except Exception:
            to = 12.0
        to = float(max(2.0, min(90.0, to)))
        try:
            await asyncio.wait_for(self.refresh_market_focus(), timeout=to)
        except asyncio.TimeoutError:
            now2 = time.time()
            try:
                self.last_market_scan = float(now2)
                self._focus_last_scan_ts = float(now2)
            except Exception:
                pass
            try:
                self._log.warning("event=FOCUS_SCAN_TIMEOUT timeout=%.1fs", float(to))
            except Exception:
                pass
        except Exception as e:
            now2 = time.time()
            try:
                self.last_market_scan = float(now2)
                self._focus_last_scan_ts = float(now2)
            except Exception:
                pass
            try:
                self._log.warning("event=FOCUS_SCAN_ERROR err=%s", e)
            except Exception:
                pass
    def _focus_weight_for(self, symbol: str) -> float:
        s = _canon_symbol(symbol)
        try:
            m = getattr(self, "supported_symbols", None)
            if isinstance(m, dict):
                w = m.get(s)
                if w is None:
                    w = m.get(symbol)
                w = float(w) if w is not None else 1.0
            else:
                w = float((getattr(self, "_focus_risk_weights", {}) or {}).get(s, 1.0))
        except Exception:
            w = 1.0
        if not (0.0 < w <= 1.0):
            w = 1.0
        return float(w)
    def _phoenix_target_symbols(self) -> List[str]:
        """Symbols that must be kept 'hot' in Phoenix (RSI/Shadow ready).

        """
        c = getattr(self, "cfg", None)
        try:
            dq = str(getattr(c, "quote", "IRT") or "IRT").upper()
        except Exception:
            dq = "IRT"
        out: List[str] = []
        def _add(sym_any: Any) -> None:
            try:
                raw = str(sym_any or "").strip()
            except Exception:
                raw = ""
            if not raw:
                return
            try:
                rm = getattr(self, "_resolved_symbol_map", None) or getattr(self, "_resolved_major_map", None) or {}
                s0 = _canon_symbol(raw)
                if s0 and isinstance(rm, dict) and rm.get(s0):
                    raw = str(rm.get(s0) or raw)
            except Exception:
                pass
            cs = ""
            try:
                cs = _canon_pair(raw, dq)
            except Exception:
                try:
                    cs = _canon_symbol(raw)
                except Exception:
                    cs = raw.strip().upper()
            try:
                ss = getattr(self, "supported_symbols", None)
                if isinstance(ss, dict) and cs and (cs not in ss):
                    base = _canon_symbol(raw)
                    for qq in ("IRT", "USDT", "BTC", "ETH", "IRR", "USD"):
                        try:
                            cand = _canon_pair(base, qq)
                        except Exception:
                            cand = ""
                        if cand and cand in ss:
                            cs = cand
                            break
            except Exception:
                pass
            if cs and cs not in out:
                out.append(cs)
        try:
            focus_sym = getattr(self, "_focus_symbol", None) or getattr(self, "focus_symbol", None)
            if focus_sym:
                _add(focus_sym)
        except Exception:
            pass
        try:
            ss = getattr(self, "supported_symbols", None)
            if isinstance(ss, dict):
                syms = list(ss.keys())
            elif isinstance(ss, (list, tuple, set)):
                syms = list(ss)
            else:
                syms = []
            for s in (syms or []):
                _add(s)
        except Exception:
            pass
        try:
            rows = getattr(self, "_top8_snapshot", None) or []
            for r in (rows or [])[:8]:
                s = ""
                try:
                    if isinstance(r, dict):
                        s = r.get("symbol") or r.get("market") or r.get("pair") or ""
                    else:
                        s = str(r or "")
                except Exception:
                    s = ""
                if s:
                    _add(s)
        except Exception:
            pass
        try:
            for s in (getattr(c, "symbols", None) or []):
                _add(s)
        except Exception:
            pass
        try:
            for s in (getattr(c, "symbol_priority", None) or []):
                _add(s)
        except Exception:
            pass
        try:
            ws = getattr(self, "wallets", None)
            if isinstance(ws, dict):
                for w in (ws or {}).values():
                    for s in (getattr(w, "focus_symbols", None) or []):
                        _add(s)
        except Exception:
            pass
        try:
            base_raw = str(os.getenv("PHOENIX_BASE_SYMBOLS", "BTC,ETH,USDT,PAXG,BNB,SOL,XRP,ZEC") or "")
            base = [p.strip() for p in base_raw.replace(";", ",").split(",") if p.strip()]
            for b in base:
                bb = str(b).strip().upper()
                if not bb:
                    continue
                if bb.endswith(dq):
                    _add(bb)
                else:
                    _add(f"{bb}{dq}")
        except Exception:
            pass
        return out
    def _phoenix_health_symbols(self) -> List[str]:
        """Symbols that are health-critical (used for confidence & TOP8 fallback).

        """
        c = getattr(self, "cfg", None)
        try:
            dq = str(getattr(c, "quote", "IRT") or "IRT").upper()
        except Exception:
            dq = "IRT"
        out: List[str] = []
        def _add(sym_any: Any) -> None:
            try:
                raw = str(sym_any or "").strip()
            except Exception:
                raw = ""
            if not raw:
                return
            try:
                raw = str(raw).strip()
            except Exception:
                pass
            try:
                cs = _canon_pair(raw, dq)
            except Exception:
                cs = _canon_symbol(raw) if raw else ""
            cs = _canon_symbol(cs) if cs else ""
            try:
                ss = getattr(self, "supported_symbols", None)
                if isinstance(ss, dict) and cs and (cs not in ss):
                    base = _canon_symbol(raw)
                    for qq in ("IRT", "USDT", "BTC", "ETH", "IRR", "USD"):
                        try:
                            cand = _canon_pair(base, qq)
                        except Exception:
                            cand = ""
                        if cand and cand in ss:
                            cs = _canon_symbol(cand)
                            break
            except Exception:
                pass
            if cs and cs not in out:
                out.append(cs)
        try:
            focus_sym = getattr(self, "_focus_symbol", None) or getattr(self, "focus_symbol", None)
            if focus_sym:
                _add(focus_sym)
        except Exception:
            pass
        try:
            rows = getattr(self, "_top8_snapshot", None) or []
            for r in (rows or [])[:8]:
                s = ""
                try:
                    if isinstance(r, dict):
                        s = r.get("symbol") or r.get("market") or r.get("pair") or ""
                    else:
                        s = str(r or "")
                except Exception:
                    s = ""
                if s:
                    _add(s)
        except Exception:
            pass
        try:
            ws = getattr(self, "wallets", None)
            if isinstance(ws, dict):
                for w in (ws or {}).values():
                    pos = getattr(w, "positions", None) or getattr(getattr(w, "exec", None), "positions", None) or {}
                    if isinstance(pos, dict):
                        for psym, pobj in pos.items():
                            try:
                                qty = float(getattr(pobj, "qty", getattr(pobj, "amount", 0.0)) or 0.0)
                            except Exception:
                                try:
                                    qty = float(pobj.get("qty") or pobj.get("amount") or 0.0) if isinstance(pobj, dict) else 0.0
                                except Exception:
                                    qty = 0.0
                            if qty and abs(float(qty)) > 0.0:
                                _add(psym)
        except Exception:
            pass
        try:
            base_raw = str(os.getenv("PHOENIX_BASE_SYMBOLS", "BTC,ETH,USDT,PAXG,BNB,SOL,XRP,ZEC") or "")
            base = [p.strip() for p in base_raw.replace(";", ",").split(",") if p.strip()]
            for b in base:
                bb = str(b).strip().upper()
                if not bb:
                    continue
                if bb.endswith(dq):
                    _add(bb)
                else:
                    _add(f"{bb}{dq}")
        except Exception:
            pass
        try:
            for s in (getattr(c, "symbol_priority", None) or [])[:8]:
                _add(s)
        except Exception:
            pass
        try:
            maxn = int(_env_int("HEALTH_CORE_SYMBOLS_MAX", 16) or 16)
        except Exception:
            maxn = 16
        maxn = int(max(8, min(64, maxn)))
        return out[:maxn]
    def _symbols_priority_order(self, cfg: Optional[BotConfig] = None, wallet: Optional["WalletRuntime"] = None) -> List[str]:
        c = cfg or self.cfg
        out: List[str] = []
        try:
            focus: List[str] = []
            if wallet is not None:
                focus = list(getattr(wallet, "focus_symbols", None) or [])
            if not focus and bool(getattr(c, "autonomous_ai", False)):
                focus = list(getattr(self, "supported_symbols", None) or [])
            focus = [_canon_symbol(s) for s in focus if s]
            for s in focus:
                if s in (c.symbols or []) and s not in out:
                    out.append(s)
        except Exception:
            pass
        try:
            if bool(getattr(c, "top8_use_for_selection", False)):
                ranked = [str(r.get("symbol") or "").strip() for r in (self._top8_snapshot or [])]
                ranked = [_canon_symbol(s) for s in ranked if s]
                for s in ranked:
                    if s in (c.symbols or []) and s not in out:
                        out.append(s)
        except Exception:
            pass
        pri = [s for s in (c.symbol_priority or []) if s in (c.symbols or []) and s not in out]
        rest = [s for s in (c.symbols or []) if s not in out and s not in pri]
        out = list(out + pri + rest)
        try:
            if hasattr(self, "feed") and self.feed is not None:
                out = [s for s in out if not self.feed.is_ignored(s)]
        except Exception:
            pass
        return out
    def get_top8_snapshot(self) -> List[dict]:
        try:
            rows = list(getattr(self, "_top8_snapshot", None) or [])
        except Exception:
            rows = []
        if rows:
            return rows
        return []
    async def _refresh_orders_if_needed(self, w: WalletRuntime) -> int:
        now = time.time()
        try:
            last_ts = float(getattr(w, 'last_orders_ts', 0.0) or 0.0)
            ttl = float(getattr(self.cfg, 'orders_refresh_sec', 3.0) or 3.0)
            if (now - last_ts) < max(0.5, ttl):
                return int(getattr(w, 'open_orders_exch', 0) or 0)
        except Exception:
            pass
        if bool(getattr(self.cfg, 'dry_run', False)):
            cnt = 0
            try:
                pend = self.orders.pending() if hasattr(self, 'orders') else {}
                for _cid, rec in (pend or {}).items():
                    if isinstance(rec, dict) and str(rec.get('wallet')) == str(getattr(w, 'name', '')):
                        cnt += 1
            except Exception:
                cnt = 0
            try:
                w.last_orders_sync_ok = True
                w.last_orders_sync_err = ""
                w.last_orders_sync_ts = float(now)
            except Exception:
                pass
            _obs_trace(w, "ORDERS_SYNC_DRY", meta={"open": int(cnt)})
            try:
                w._orders_sync_fail_streak = 0
            except Exception:
                pass
            w.open_orders_exch = int(cnt)
            w.last_orders_ts = float(now)
            return int(cnt)
        resp = None
        resps = []
        last_err: Optional[Exception] = None
        _is_arz = False
        try:
            _is_arz = bool(getattr(w.ex, "_is_arzplus", None) and w.ex._is_arzplus())
        except Exception:
            _is_arz = False
        for _st in (("new",) if _is_arz else ("open", "new", "active")):
            try:
                lo = getattr(w.ex, "list_orders", None)
                if callable(lo):
                    r0 = await lo(status=_st)
                else:
                    req = getattr(w.ex, "request", None)
                    if callable(req):
                        params = {}
                        if _st:
                            params["status"] = str(_st)
                        r0 = await req("GET", "/market/orders/", params=params, auth=True)
                    else:
                        raise AttributeError("has no attribute 'list_orders'")
                if r0 is not None:
                    resps.append(r0)
            except Exception as e:
                last_err = e
        if not resps:
            try:
                lo2 = getattr(w.ex, "list_orders", None)
                if callable(lo2):
                    r0 = await lo2()
                else:
                    req2 = getattr(w.ex, "request", None)
                    if callable(req2):
                        r0 = await req2("GET", "/market/orders/", auth=True)
                    else:
                        raise AttributeError("has no attribute 'list_orders'")
                if r0 is not None:
                    resps.append(r0)
                last_err = None
            except Exception as e:
                last_err = e
        if not resps:
            e = last_err or Exception("list_orders returned empty")
            err_s = f"{type(e).__name__}: {e}"
            try:
                w.last_orders_err = str(err_s)[:300]
            except Exception:
                pass
            self._log.warning('event=OPEN_ORDERS_REFRESH_FAIL wallet=%s err=%s', w.name, err_s)
            try:
                w.last_orders_sync_ok = False
                w.last_orders_sync_err = str(err_s)[:300]
                w.last_orders_sync_ts = float(now)
            except Exception:
                pass
            _obs_trace(w, "ORDERS_SYNC_FAIL", reason=str(err_s)[:120], meta={})
            try:
                w._orders_sync_fail_streak = int(getattr(w, "_orders_sync_fail_streak", 0) or 0) + 1
            except Exception:
                pass
            try:
                if _env_bool("SAFE_RECONCILE", True) and _env_bool('LIVE_TRADING', False):
                    w.sanity_halt = True
                    try:
                        w.sanity_since_ts = float(now)
                    except Exception:
                        pass
                    try:
                        setattr(w, "_sanity_since_ts", float(now))
                    except Exception:
                        pass
                    w.sanity_reason = "ORDER_SYNC_UNHEALTHY"
                    hold = float(getattr(self.cfg, 'sanity_hold_sec', 8.0) or 8.0)
                    w.sanity_until_ts = float(now + max(2.0, hold))
                    if _env_bool("SAFE_RECONCILE_STRICT", True) and _env_bool("GLOBAL_SAFE_ON_ORDER_DESYNC", False):
                        self.risk.halt_new_trades('ORDER_RECONCILE_FAIL')
            except Exception:
                pass
            w.last_orders_ts = float(now)
            return int(getattr(w, 'open_orders_exch', 0) or 0)
        orders = []
        try:
            if hasattr(self, 'orders') and hasattr(self.orders, '_extract_orders'):
                for _r in (resps or []):
                    try:
                        orders.extend(self.orders._extract_orders(_r))
                    except Exception:
                        pass
            else:
                for _r in (resps or []):
                    if isinstance(_r, dict):
                        v = _r.get('data') or _r.get('orders') or _r.get('items') or []
                        if isinstance(v, list):
                            orders.extend([o for o in v if isinstance(o, dict)])
        except Exception:
            orders = []
        try:
            _seen = set()
            _out = []
            for _o in (orders or []):
                _oid = None
                try:
                    _oid = OrderJournal._order_id(_o)
                except Exception:
                    _oid = None
                _k = str(_oid or '').strip()
                if not _k:
                    continue
                if _k in _seen:
                    continue
                _seen.add(_k)
                _out.append(_o)
            orders = _out
        except Exception:
            pass
        # --- FIX: per-symbol open-order map (restart-safe entry guard) ---
        try:
            by_sym = {}
            for _o in (orders or []):
                if not isinstance(_o, dict):
                    continue
                s = _o.get("symbol") or _o.get("market") or _o.get("pair") or _o.get("instrument") or ""
                s = _canon_symbol(s)
                if not s:
                    continue
                side = str(_o.get("side") or _o.get("type") or "").lower().strip()
                if side.startswith("buy"):
                    k = "buy"
                elif side.startswith("sell"):
                    k = "sell"
                else:
                    k = "other"
                rec = by_sym.get(s)
                if rec is None:
                    rec = {"buy": 0, "sell": 0, "other": 0, "all": 0}
                    by_sym[s] = rec
                rec[k] += 1
                rec["all"] += 1
            setattr(w, "_open_orders_by_sym", by_sym)
        except Exception:
            pass
        try:
            bot_ttl_sec = float(_env_float("ORDER_TTL_SEC", 60.0) or 60.0)
        except Exception:
            bot_ttl_sec = 60.0
        bot_ttl_sec = max(10.0, float(bot_ttl_sec))
        try:
            manual_ttl_sec = float(_env_float("MANUAL_ORDER_TTL_SEC", 300.0) or 300.0)
        except Exception:
            manual_ttl_sec = 300.0
        manual_ttl_sec = max(30.0, float(manual_ttl_sec))
        try:
            max_age_h = float(_env_float("ORDER_MAX_AGE_HOURS", 48.0) or 48.0)
        except Exception:
            max_age_h = 48.0
        max_any_age_sec = max(1.0, float(max_age_h)) * 3600.0
        try:
            orphan_manual_sec = float(_env_float("MANUAL_ORPHAN_TTL_SEC", 300.0) or 300.0)
        except Exception:
            orphan_manual_sec = 300.0
        orphan_manual_sec = max(30.0, float(orphan_manual_sec))
        active_syms = set()
        try:
            active_syms = {_canon_symbol(s) for s in (getattr(self.cfg, "symbols", []) or []) if s}
        except Exception:
            active_syms = set()
        try:
            orphan_age_sec = float(_env_float("ORPHAN_BOT_ORDER_MAX_AGE_SEC", 900.0) or 900.0)
        except Exception:
            orphan_age_sec = 900.0
        orphan_age_sec = max(60.0, float(orphan_age_sec))
        try:
            max_cancel = int(_env_int("ORDER_TTL_MAX_CANCEL", 8) or 8)
        except Exception:
            max_cancel = 8
        max_cancel = max(1, min(30, int(max_cancel)))
        try:
            rawp = str(os.getenv("BOT_CID_PREFIXES", "SOV,RAZ,PP") or "")
            prefixes = tuple([p.strip().upper() for p in rawp.split(",") if p.strip()])
        except Exception:
            prefixes = ("SOV", "RAZ", "PP")
        pos_qty = 0.0
        try:
            for p in (getattr(w, "positions", {}) or {}).values():
                pos_qty += abs(float(getattr(p, "qty", 0.0) or 0.0))
        except Exception:
            pos_qty = 0.0
        fs_map = {}
        fs_dirty = False
        fs_path = ""
        try:
            fs_path = str(os.path.join("cache", f"order_first_seen_{str(getattr(w,'name','W'))}.json"))
            _ensure_dir(fs_path)
            if hasattr(w, "_order_first_seen") and isinstance(getattr(w, "_order_first_seen"), dict):
                fs_map = dict(getattr(w, "_order_first_seen") or {})
            else:
                if os.path.exists(fs_path):
                    with open(fs_path, "r", encoding="utf-8") as f:
                        fs_map = dict(json.load(f) or {})
                else:
                    fs_map = {}
            try:
                now0 = float(now)
                for k, ts0 in list(fs_map.items()):
                    try:
                        if (now0 - float(ts0)) > 90 * 24 * 3600:
                            fs_map.pop(k, None)
                            fs_dirty = True
                    except Exception:
                        pass
            except Exception:
                pass
            setattr(w, "_order_first_seen", fs_map)
        except Exception:
            fs_map = {}
            def _order_ts_seconds(o) -> float | None:
                try:
                    ots = None
                    if isinstance(o, dict):
                        ots = (o.get('created_at') or o.get('createdAt') or o.get('create_time') or o.get('ctime') or
                               o.get('timestamp') or o.get('ts') or o.get('time'))
                    if ots is None:
                        return None
                    ts_s = float(_epoch_to_sec(ots))
                    if ts_s <= 0.0:
                        return None
                    if ts_s < 946684800.0:
                        return None
                    return float(ts_s)
                except Exception:
                    return None
        open_list = []
        try:
            raw = list(orders or [])
        except Exception:
            raw = []
        now_s = float(now)
        for o in (raw or []):
            try:
                st = OrderJournal._order_status(o)
            except Exception:
                st = ""
            try:
                term = bool(self.orders._is_terminal_status(st)) if hasattr(self, "orders") else False
            except Exception:
                term = False
            if term:
                continue
            oid = None
            try:
                oid = OrderJournal._order_id(o)
            except Exception:
                oid = None
            if not oid:
                continue
            ts0 = _order_ts_seconds(o)
            if ts0 is None:
                try:
                    ts0 = float(fs_map.get(str(oid)) or 0.0) or None
                except Exception:
                    ts0 = None
            if ts0 is None:
                try:
                    fs_map[str(oid)] = float(now_s)
                    setattr(w, "_order_first_seen", fs_map)
                    fs_dirty = True
                    ts0 = float(now_s)
                except Exception:
                    ts0 = float(now_s)
            age = max(0.0, now_s - float(ts0))
            open_list.append((age, oid, o))
        def _is_bot_order(o) -> bool:
            try:
                cid = str(OrderJournal._order_cid(o) or "").strip().upper()
            except Exception:
                cid = ""
            if not cid:
                return False
            for p in prefixes:
                if cid.startswith(p):
                    return True
            return False
        canc_ok = 0
        canc_fail = 0
        last_err = ""
        if open_list:
            open_list.sort(key=lambda x: float(x[0] or 0.0), reverse=True)
            for age, oid, o in open_list:
                if canc_ok + canc_fail >= max_cancel:
                    break
                is_bot = _is_bot_order(o)
                do_cancel = False
                reason = ""
                if float(age) >= float(max_any_age_sec):
                    do_cancel = True
                    reason = f"AGE>{int(max_age_h)}h"
                if is_bot:
                    if float(age) >= float(bot_ttl_sec):
                        do_cancel = True
                        reason = f"BOT_TTL>{int(bot_ttl_sec)}s"
                    if (not do_cancel) and (pos_qty <= 0.0) and (float(age) >= float(orphan_age_sec)):
                        do_cancel = True
                        reason = f"ORPHAN>{int(orphan_age_sec)}s"
                else:
                    if not do_cancel:
                        try:
                            osym = _canon_symbol(str(OrderJournal._order_symbol(o) or "").strip())
                        except Exception:
                            osym = str(OrderJournal._order_symbol(o) or "").strip().upper()
                        if osym and active_syms and (osym not in active_syms) and (float(age) >= float(orphan_manual_sec)):
                            do_cancel = True
                            reason = f"MANUAL_ORPHAN>{int(orphan_manual_sec)}s"
                    if _env_bool("CANCEL_MANUAL_ORDERS", True) and (float(age) >= float(manual_ttl_sec)):
                        do_cancel = True
                        reason = f"MANUAL_TTL>{int(manual_ttl_sec)}s"
                if not do_cancel:
                    continue
                try:
                    tmo = float(_env_float("ORDER_TTL_CANCEL_TIMEOUT", 10.0) or 10.0)
                except Exception:
                    tmo = 10.0
                try:
                    await asyncio.wait_for(w.ex.cancel_order(oid), timeout=max(2.0, float(tmo)))
                    canc_ok += 1
                    try:
                        ev = "BOT_ORDER_CANCEL" if is_bot else "MANUAL_ORDER_CANCEL"
                        _obs_trace(w, ev, symbol=str(OrderJournal._order_symbol(o) or ""), reason=reason, meta={"oid": str(oid), "age": float(age)})
                    except Exception:
                        pass
                    try:
                        fs_map.pop(str(oid), None)
                        fs_dirty = True
                    except Exception:
                        pass
                except Exception as e:
                    canc_fail += 1
                    last_err = f"{type(e).__name__}: {e}"
                    try:
                        ev = "BOT_ORDER_CANCEL_FAIL" if is_bot else "MANUAL_ORDER_CANCEL_FAIL"
                        _obs_trace(w, ev, symbol=str(OrderJournal._order_symbol(o) or ""), reason=last_err[:80], meta={"oid": str(oid), "age": float(age)})
                    except Exception:
                        pass
        try:
            if fs_dirty and fs_path:
                with open(fs_path, "w", encoding="utf-8") as f:
                    json.dump(fs_map, f, ensure_ascii=False)
        except Exception:
            pass
        if canc_ok or canc_fail:
            try:
                w.ttl_canceled = int(getattr(w, "ttl_canceled", 0) or 0) + int(canc_ok)
                w.ttl_cancel_failed = int(getattr(w, "ttl_cancel_failed", 0) or 0) + int(canc_fail)
                w.ttl_last_cancel_ts = float(now_s)
                w.ttl_last_cancel_err = str(last_err or "")[:200]
                w.last_event = f"TTL_CXL ok={canc_ok} fail={canc_fail}"
            except Exception:
                pass
        try:
            if fs_dirty and fs_path:
                with open(fs_path, "w", encoding="utf-8") as f:
                    json.dump(fs_map, f, ensure_ascii=False)
        except Exception:
            pass
        open_cnt = 0
        oldest_age = None
        locked_quote: Dict[str, float] = {}
        locked_base: Dict[str, float] = {}
        quote0 = str(getattr(self.cfg, 'quote', 'IRT') or 'IRT').upper()
        def _f(x) -> float:
            try:
                if x is None:
                    return 0.0
                def _f(x) -> float:
                    return float(_safe_float(x, default=0.0, translate_digits=False, allow_percent=True, finite=True, na_values=True, strip=True) or 0.0)
                return float(str(x).replace(',', '').strip())
            except TradingHalt:
                raise
            except Exception:
                return 0.0
        def _split_pair(sym: str) -> Tuple[str, str]:
            s = _canon_symbol(sym).upper()
            for suf in ("USDT", "IRT", "IRR", "TMN", "USD"):
                if s.endswith(suf) and len(s) > len(suf):
                    return s[:-len(suf)], suf
            if s.endswith(quote0) and len(s) > len(quote0):
                return s[:-len(quote0)], quote0
            return s, quote0
        try:
            for o in (orders or []):
                st = ''
                try:
                    if hasattr(self, 'orders') and hasattr(self.orders, '_order_status'):
                        st = str(self.orders._order_status(o) or '')
                    elif isinstance(o, dict):
                        st = str(o.get('status') or o.get('state') or '')
                except Exception:
                    st = ''
                term = False
                try:
                    if hasattr(self, 'orders') and hasattr(self.orders, '_is_terminal_status'):
                        term = bool(self.orders._is_terminal_status(st))
                except Exception:
                    term = False
                if term:
                    continue
                open_cnt += 1
                try:
                    ots = None
                    if isinstance(o, dict):
                        ots = (o.get('created_at') or o.get('createdAt') or o.get('create_time') or o.get('ctime') or
                               o.get('timestamp') or o.get('ts') or o.get('time'))
                    if ots is not None:
                        ts0 = None
                        if isinstance(ots, (int, float)):
                            ts0 = float(ots)
                        else:
                            s0 = str(ots).strip()
                            try:
                                s1 = s0.replace('Z', '').replace('T', ' ')
                                ts0 = datetime.datetime.fromisoformat(s1).timestamp()
                            except Exception:
                                ts0 = None
                        if ts0 is not None:
                            ts0 = float(_epoch_to_sec(ts0))
                            if ts0 > 1000000000:
                                age0 = max(0.0, float(now) - float(ts0))
                                oldest_age = age0 if oldest_age is None else max(oldest_age, age0)
                except Exception:
                    pass
                try:
                    if hasattr(self, 'orders') and hasattr(self.orders, '_order_symbol'):
                        sym = str(self.orders._order_symbol(o) or '')
                    elif isinstance(o, dict):
                        sym = str(o.get('symbol') or o.get('market') or o.get('name') or '')
                    else:
                        sym = ''
                except Exception:
                    sym = ''
                sym = _canon_symbol(sym)
                try:
                    if hasattr(self, 'orders') and hasattr(self.orders, '_order_side'):
                        side = str(self.orders._order_side(o) or '')
                    elif isinstance(o, dict):
                        side = str(o.get('side') or o.get('type') or '')
                    else:
                        side = ''
                except Exception:
                    side = ''
                side_l = str(side or '').lower()
                amt = 0.0
                filled = 0.0
                px = 0.0
                try:
                    if isinstance(o, dict):
                        amt = _f(o.get('amount') or o.get('qty') or o.get('quantity'))
                        filled = _f(o.get('filled_amount') or o.get('filled') or o.get('filled_qty'))
                        px = _f(o.get('price') or o.get('limit_price') or o.get('filled_price'))
                except Exception:
                    pass
                rem = max(0.0, amt - filled)
                if rem <= 0.0:
                    continue
                base, quote = _split_pair(sym)
                if side_l.startswith('b'):
                    if px > 0.0:
                        locked_quote[quote] = float(locked_quote.get(quote, 0.0) + rem * px)
                elif side_l.startswith('s'):
                    locked_base[base] = float(locked_base.get(base, 0.0) + rem)
        except Exception:
            open_cnt = int(getattr(w, 'open_orders_exch', 0) or 0)
        try:
            cash_free = float(getattr(w, 'cash_irt', 0.0) or 0.0)
            assets_free = dict(getattr(w, 'assets_snapshot', {}) or {})
            assets_total = dict(assets_free)
            cash_total = float(cash_free)
            for ccy, amt in (locked_quote or {}).items():
                c = str(ccy or '').upper()
                if c in {'IRT', 'IRR', 'TMN'} or c == quote0:
                    cash_total += float(amt)
                else:
                    assets_total[c] = float(assets_total.get(c, 0.0) + float(amt))
            for a, amt in (locked_base or {}).items():
                aa = str(a or '').upper()
                if not aa:
                    continue
                assets_total[aa] = float(assets_total.get(aa, 0.0) + float(amt))
            if cash_total > 0.0:
                w.cash_total_irt = float(max(0.0, cash_total))
            if assets_total:
                w.assets_total_snapshot = dict(assets_total)
        except Exception:
            pass
        try:
            w.open_orders_oldest_age_sec = float(oldest_age) if (oldest_age is not None and int(open_cnt) > 0) else None
        except Exception:
            pass
        try:
            if _env_bool("CANCEL_STUCK_BOT_ORDERS", True) and int(open_cnt) > 0 and (oldest_age is not None):
                stale_sec = float(_env_float("STUCK_ORDER_CANCEL_SEC", 3600.0) or 3600.0)
                min_iv = float(_env_float("STUCK_CANCEL_MIN_INTERVAL", 30.0) or 30.0)
                last_ts = float(getattr(w, "last_stuck_cancel_ts", 0.0) or 0.0)
                if stale_sec > 0.0 and float(oldest_age) >= stale_sec and (float(now) - last_ts) >= max(5.0, min_iv):
                    raw = str(os.getenv("BOT_CID_PREFIXES", "SOV,RAZ,PP") or "")
                    prefixes = tuple([p.strip().upper() for p in raw.split(",") if p.strip()])
                    canc = 0
                    def _order_age(o0):
                        try:
                            ots = None
                            if isinstance(o0, dict):
                                ots = (o0.get('created_at') or o0.get('createdAt') or o0.get('create_time') or o0.get('ctime') or
                                       o0.get('timestamp') or o0.get('ts') or o0.get('time'))
                            if ots is None:
                                return None
                            ts0 = None
                            if isinstance(ots, (int, float)):
                                ts0 = float(ots)
                            else:
                                s0 = str(ots).strip()
                                try:
                                    s1 = s0.replace('Z', '').replace('T', ' ')
                                    ts0 = datetime.datetime.fromisoformat(s1).timestamp()
                                except Exception:
                                    ts0 = None
                            if ts0 is None:
                                return None
                            ts0 = float(_epoch_to_sec(ts0))
                            if ts0 <= 1000000000:
                                return None
                            return max(0.0, float(now) - float(ts0))
                        except Exception:
                            return None
                    for o0 in (orders or []):
                        try:
                            st0 = ''
                            try:
                                if hasattr(self, 'orders') and hasattr(self.orders, '_order_status'):
                                    st0 = str(self.orders._order_status(o0) or '')
                                elif isinstance(o0, dict):
                                    st0 = str(o0.get('status') or o0.get('state') or '')
                            except Exception:
                                st0 = ''
                            term0 = False
                            try:
                                if hasattr(self, 'orders') and hasattr(self.orders, '_is_terminal_status'):
                                    term0 = bool(self.orders._is_terminal_status(st0))
                            except Exception:
                                term0 = False
                            if term0:
                                continue
                            age0 = _order_age(o0)
                            if age0 is None or float(age0) < stale_sec:
                                continue
                            cid0 = ""
                            try:
                                cid0 = str(OrderJournal._order_cid(o0) or "").strip().upper()
                            except Exception:
                                cid0 = ""
                            is_bot = False
                            if cid0:
                                for p in prefixes:
                                    if cid0.startswith(p):
                                        is_bot = True
                                        break
                            if not is_bot:
                                continue
                            oid0 = OrderJournal._order_id(o0)
                            if not oid0:
                                continue
                            try:
                                await w.ex.cancel_order(oid0)
                                canc += 1
                            except Exception:
                                pass
                        except Exception:
                            continue
                    if canc:
                        try:
                            w.last_stuck_cancel_ts = float(now)
                            w.last_event = f"STUCK_CLEAN {canc}"
                        except Exception:
                            pass
                        try:
                            self._log.warning("event=STUCK_ORDERS_CANCELED wallet=%s canceled=%s oldest=%s", w.name, int(canc), fmt_age_s(oldest_age))
                        except Exception:
                            pass
        except Exception:
            pass
        try:
            w.last_orders_sync_ok = True
            w.last_orders_sync_err = ""
            w.last_orders_sync_ts = float(now)
        except Exception:
            pass
        try:
            w._orders_sync_fail_streak = 0
        except Exception:
            pass
        _obs_trace(w, "ORDERS_SYNC_OK", meta={"open": int(open_cnt)})
        w.open_orders_exch = int(open_cnt)
        w.last_orders_ts = float(now)
        return int(open_cnt)
    async def _refresh_top8_if_needed(self):
        """Refresh TOP8 snapshot deterministically and without stalling the event loop.

        """
        now = float(time.time())
        thr = {}
        try:
            thr = dict(getattr(self, "_hw_thresholds", {}) or {})
        except Exception:
            thr = {}
        try:
            top8_warn_thr = float(thr.get("top8_warn") or _env_float("HEALTH_WD_TOP8_WARN_SEC", 3.0) or 3.0)
        except Exception:
            top8_warn_thr = float(_env_float("HEALTH_WD_TOP8_WARN_SEC", 3.0) or 3.0)
        try:
            refresh_sec = float(_env_float("TOP8_REFRESH_SEC", float(getattr(self.cfg, "top8_refresh_sec", 12.0) or 12.0)) or 12.0)
        except Exception:
            refresh_sec = float(getattr(self.cfg, "top8_refresh_sec", 12.0) or 12.0)
        try:
            if not bool(getattr(self, "_phoenix_seed_done", False)):
                boot = float(_env_float("TOP8_BOOTSTRAP_REFRESH_SEC", 2.0) or 2.0)
                refresh_sec = min(float(refresh_sec), max(0.8, float(boot)))
        except Exception:
            pass
        try:
            force_refresh = bool(_env_bool("TOP8_REFRESH_FORCE", False))
        except Exception:
            force_refresh = False
        try:
            target = max(0.6, min(5.0, float(top8_warn_thr) * 0.70))
        except Exception:
            target = 2.0
        if (not force_refresh) and (float(refresh_sec) > float(target)):
            refresh_sec = float(target)
        if not force_refresh:
            refresh_sec = float(max(0.5, min(8.0, refresh_sec)))
        else:
            refresh_sec = float(max(0.5, min(30.0, refresh_sec)))
        try:
            last_ts = float(getattr(self, "_top8_last_ts", 0.0) or 0.0)
        except Exception:
            last_ts = 0.0
        if last_ts > 1e11:
            last_ts = last_ts / 1000.0
        if last_ts > 0.0 and (now - float(last_ts)) < float(refresh_sec):
            return
        try:
            snap_ts0 = float(getattr(self, "_market_snapshot_local_ts", 0.0) or 0.0)
            if snap_ts0 > 1e11:
                snap_ts0 = snap_ts0 / 1000.0
            if snap_ts0 > 0.0 and snap_ts0 <= (now + 5.0):
                snap_age0 = max(0.0, float(now) - float(snap_ts0))
            else:
                snap_age0 = 1e9
        except Exception:
            snap_age0 = 1e9
        try:
            kick_after = float(_env_float("TOP8_SNAPSHOT_KICK_AFTER_SEC", max(2.0, min(8.0, float(top8_warn_thr)))) or max(2.0, min(8.0, float(top8_warn_thr))))
        except Exception:
            kick_after = max(2.0, min(8.0, float(top8_warn_thr)))
        try:
            if float(snap_age0) > float(kick_after):
                t = getattr(self, "_bg_snapshot_task", None)
                if t is None or bool(getattr(t, "done", lambda: True)()):
                    try:
                        setattr(self, "_bg_snapshot_task", asyncio.create_task(self._refresh_market_snapshot_if_needed(now=now), name="bg_snapshot"))
                        setattr(self, "_bg_snapshot_start_ts", float(now))
                    except Exception:
                        pass
        except Exception:
            pass
        snap = None
        snap_ts = 0.0
        try:
            snap = getattr(self, "_market_snapshot", None)
        except Exception:
            snap = None
        try:
            snap_ts = float(getattr(self, "_market_snapshot_local_ts", 0.0) or 0.0)
        except Exception:
            snap_ts = 0.0
        if snap_ts > 1e11:
            snap_ts = snap_ts / 1000.0
        if not isinstance(snap, dict) or not snap:
            try:
                snap2 = getattr(getattr(self, "public", None), "_last_market_stats_snapshot", None)
                if isinstance(snap2, dict) and snap2:
                    snap = snap2
                    try:
                        snap_ts = float(getattr(getattr(self, "public", None), "last_update_time", 0.0) or snap_ts or now)
                    except Exception:
                        snap_ts = float(snap_ts or now)
            except Exception:
                pass
        try:
            clamp_pct = float(os.getenv("TOP8_CHANGE_CLAMP_PCT", 30.0) or 30.0)
        except Exception:
            clamp_pct = 30.0
        clamp_pct = float(max(1.0, min(200.0, clamp_pct)))
        try:
            uni_max = int(_env_int("TOP8_UNIVERSE_MAX_SCAN", 300) or 300)
        except Exception:
            uni_max = 300
        uni_max = max(30, min(2500, int(uni_max)))
        quotes_spec = str(os.getenv("TOP8_QUOTES", "*") or "*").strip()
        quotes: list[str] = []
        if quotes_spec and quotes_spec != "*":
            for q in re.split(r"[\s,;|]+", quotes_spec):
                q = str(q or "").strip().upper()
                if q and q not in quotes:
                    quotes.append(q)
        def _sf(v, d=0.0, pct=False) -> float:
            try:
                return float(_safe_float(
                    v,
                    default=d,
                    translate_digits=True,
                    allow_percent=bool(pct),
                    finite=True,
                    na_values=True,
                    strip=True,
                ) or d)
            except Exception:
                try:
                    return float(d)
                except Exception:
                    return 0.0
        def _mid_from_row(rr) -> float:
            try:
                if isinstance(rr, dict) and isinstance(rr.get("raw"), dict):
                    rr = rr.get("raw")
                if not isinstance(rr, dict):
                    return 0.0
                for _k in (
                    "mid","mark","markPrice",
                    "last","last_price","lastPrice",
                    "last_trade_price","lastTradePrice",
                    "price","close","closePrice",
                    "c","p","rate","value","latest","ltp","tradePrice",
                ):
                    _v = _sf(rr.get(_k), 0.0, pct=False)
                    if _v > 0.0:
                        return float(_v)
                bid = _sf(rr.get("bid", rr.get("bestBid", rr.get("bidPrice", rr.get("buy", rr.get("b", 0.0))))), 0.0, pct=False)
                ask = _sf(rr.get("ask", rr.get("bestAsk", rr.get("askPrice", rr.get("sell", rr.get("a", 0.0))))), 0.0, pct=False)
                if bid > 0.0 and ask > 0.0:
                    return float(bid + ask) / 2.0
                if bid > 0.0:
                    return float(bid)
                if ask > 0.0:
                    return float(ask)
            except Exception:
                pass
            return 0.0
        def _pct_from_row(rr, last_mid) -> float:
            try:
                if isinstance(rr, dict) and isinstance(rr.get("raw"), dict):
                    rr = rr.get("raw")
                if not isinstance(rr, dict):
                    rr = {}
                pct = None
                for _k in (
                    "changePercent","percentChange","priceChangePercent",
                    "chgPct","change_pct","change24hPct","change_24h_pct",
                    "percent","pct","pct24h","pct_24h","changePct",
                ):
                    if _k in rr:
                        pct = _sf(rr.get(_k), 0.0, pct=True)
                        if math.isfinite(pct):
                            break
                if pct is not None:
                    frac = float(pct)
                    if abs(frac) > 2.0:
                        frac = frac / 100.0
                    return float(frac * 100.0)
                op = None
                for _k in ("open","openPrice","open_price","o","open24h","open_24h","open24H","prevClose","prev_close","yesterdayClose"):
                    if _k in rr:
                        op = _sf(rr.get(_k), 0.0, pct=False)
                        if op and op > 0.0:
                            break
                if op and op > 0.0 and last_mid > 0.0:
                    return float((float(last_mid) - float(op)) / float(op) * 100.0)
            except Exception:
                pass
            return 0.0
        items = []
        if isinstance(snap, dict) and snap:
            try:
                cid = int(getattr(self, "_top8_items_cache_id", 0) or 0)
                cn = int(getattr(self, "_top8_items_cache_n", 0) or 0)
                citems = getattr(self, "_top8_items_cache", None)
                if cid == int(id(snap)) and isinstance(citems, list) and cn == int(len(snap)):
                    items = citems
                else:
                    items = list(snap.items())
                    try:
                        setattr(self, "_top8_items_cache_id", int(id(snap)))
                        setattr(self, "_top8_items_cache_n", int(len(snap)))
                        setattr(self, "_top8_items_cache", items)
                    except Exception:
                        pass
            except Exception:
                try:
                    items = list(snap.items())
                except Exception:
                    items = []
        utotal = int(len(items))
        window = items
        if utotal > 0 and utotal > uni_max:
            try:
                off = int(getattr(self, "_top8_scan_offset", 0) or 0)
            except Exception:
                off = 0
            if off < 0:
                off = 0
            if off >= utotal:
                off = 0
            win = items[off:off + uni_max]
            if len(win) < uni_max:
                win = win + items[0: max(0, uni_max - len(win))]
            window = win
            try:
                setattr(self, "_top8_scan_offset", int((off + uni_max) % max(1, utotal)))
            except Exception:
                pass
        scanned = int(len(window))
        qcounts: Dict[str, int] = {}
        try:
            for sym, _row in (window or []):
                ss = _canon_symbol(str(sym or ""))
                q = ""
                for qq in ("IRT","USDT","BTC","ETH","IRR","USD","USDC"):
                    if ss.endswith(qq):
                        q = qq
                        break
                qcounts[q or "?"] = int(qcounts.get(q or "?", 0) or 0) + 1
        except Exception:
            qcounts = {}
        out: List[dict] = []
        for sym, row in (window or []):
            try:
                s = _canon_symbol(str(sym or ""))
            except Exception:
                s = str(sym or "").strip().upper()
            if not s:
                continue
            if quotes and (not any(s.endswith(q) for q in quotes)):
                continue
            mid = _mid_from_row(row)
            if mid <= 0.0:
                continue
            pct = _pct_from_row(row, mid)
            if not math.isfinite(pct):
                pct = 0.0
            pct = float(clamp(pct, -clamp_pct, clamp_pct))
            out.append({"symbol": s, "mid": float(mid), "pct": float(pct), "chg": float(pct), "src": "snapshot", "ts": float(now)})
        if not out:
            try:
                feed0 = getattr(self, "feed", None)
            except Exception:
                feed0 = None
            try:
                st0 = getattr(self, "_mkt_store", None)
            except Exception:
                st0 = None
            cand = []
            try:
                cand = list(self._phoenix_health_symbols() or [])
            except Exception:
                cand = []
            if not cand:
                try:
                    cand = list(self._phoenix_target_symbols() or [])
                except Exception:
                    cand = []
            majors = ["BTCIRT","USDTIRT","ETHIRT","BNBIRT","SOLIRT","XRPIRT","TONIRT","PAXGIRT","DOGEIRT"]
            for s in majors:
                if s not in cand:
                    cand.append(s)
            px_hist = getattr(self, "_phoenix_px_hist", None)
            for s in (cand or [])[: max(24, len(cand))]:
                cs = _canon_symbol(s)
                if not cs:
                    continue
                mid = 0.0
                try:
                    if st0 is not None:
                        ss = st0.get(cs)
                        mid = float(ss.mid or 0.0)
                except Exception:
                    mid = 0.0
                if mid <= 0.0:
                    try:
                        if feed0 is not None and hasattr(feed0, "peek_mid"):
                            mid = float(feed0.peek_mid(cs) or 0.0)
                    except Exception:
                        mid = 0.0
                if mid <= 0.0:
                    continue
                dp = 0.0
                try:
                    dq = px_hist.get(cs) if isinstance(px_hist, dict) else None
                    if dq and len(dq) >= 2:
                        t1, p1 = dq[-1]
                        t0, p0 = dq[-2]
                        p1 = float(p1 or 0.0); p0 = float(p0 or 0.0)
                        if p0 > 0.0 and p1 > 0.0:
                            dp = float((p1 - p0) / p0 * 100.0)
                except Exception:
                    dp = 0.0
                dp = float(clamp(dp, -clamp_pct, clamp_pct))
                out.append({"symbol": cs, "mid": float(mid), "pct": float(dp), "chg": float(dp), "src": "local", "ts": float(now)})
            if not out:
                try:
                    setattr(self, "_top8_last_err", "TOP8_EMPTY")
                except Exception:
                    pass
                return
            try:
                setattr(self, "_top8_last_err", "TOP8_FALLBACK_LOCAL")
            except Exception:
                pass
        out.sort(key=lambda r: abs(float(r.get("pct", 0.0) or 0.0)), reverse=True)
        top8 = out[:8]
        try:
            setattr(self, "_top8_snapshot", top8)
            setattr(self, "_top8_last_ts", float(now))
            setattr(self, "_top8_ok_ts", float(now))
            try:
                setattr(self, "_top8_ok_mono_ts", float(time.monotonic()))
            except Exception:
                pass
            setattr(self, "_top8_ok_count", int(min(8, len(top8))))
            setattr(self, "_top8_ok_total", int(8))
            setattr(self, "_top8_universe_total", int(utotal))
            setattr(self, "_top8_universe_scanned", int(scanned))
            setattr(self, "_top8_universe_quote_counts", dict(qcounts or {}))
            setattr(self, "_top8_universe_ts", float(now))
        except Exception:
            pass
        try:
            warm_syms: List[str] = []
            try:
                fs = str(getattr(self, "_focus_symbol", "") or "").strip()
                if fs:
                    warm_syms.append(_canon_symbol(fs))
            except Exception:
                pass
            try:
                for r in (top8 or [])[:12]:
                    if not isinstance(r, dict):
                        continue
                    s = r.get("symbol") or r.get("sym") or r.get("pair")
                    cs = _canon_symbol(s) if s else ""
                    if cs:
                        warm_syms.append(cs)
            except Exception:
                pass
            seen2 = set()
            out2: List[str] = []
            for s in (warm_syms or []):
                if not s or s in seen2:
                    continue
                seen2.add(s)
                out2.append(s)
            warm_syms = out2
            if warm_syms:
                if getattr(self, "obsvc", None) is not None:
                    for s in warm_syms[:12]:
                        try:
                            self.obsvc.request_refresh(s, use_disk_cache_on_timeout=True, force_refresh=False)
                        except Exception:
                            pass
                else:
                    for s in warm_syms[:12]:
                        try:
                            asyncio.create_task(self.feed.fetch_depth(s, use_disk_cache_on_timeout=True, force_refresh=False))
                        except Exception:
                            pass
        except Exception:
            pass
        try:
            if snap_ts and snap_ts > 0.0 and math.isfinite(float(snap_ts)) and float(snap_ts) <= (now + 5.0):
                setattr(self, "_market_snapshot_local_ts", float(snap_ts))
                try:
                    setattr(self, "_market_snapshot_mono_ts", float(time.monotonic()))
                except Exception:
                    pass
        except Exception:
            pass
    def _estimate_equity_irt(self, cash_irt: float, positions: Dict[str, Position], current_sym: Optional[str] = None, current_mid: Optional[float] = None) -> float:
        eq = float(cash_irt or 0.0)
        usdt_irt_mid = None
        try:
            usdt_irt_mid = float(self.feed.peek_mid("USDTIRT") or 0.0)
            if usdt_irt_mid <= 0:
                try:
                    usdt_irt_mid = float(WalletRuntime._LAST_KNOWN_VALID_PRICES.get("USDTIRT", 0.0) or 0.0)
                except Exception:
                    usdt_irt_mid = 0.0
            if usdt_irt_mid <= 0:
                usdt_irt_mid = None
        except Exception:
            usdt_irt_mid = None
        for sym, pos in (positions or {}).items():
            mid = None
            if current_sym and _canon_symbol(sym) == _canon_symbol(current_sym) and current_mid is not None:
                mid = float(current_mid)
            else:
                try:
                    mid = self.feed.peek_mid(sym)
                except Exception:
                    mid = None
            try:
                s_key = _canon_symbol(sym)
            except Exception:
                s_key = sym
            if mid is not None and float(mid) > 0.0:
                try:
                    WalletRuntime.set_last_known_price(s_key, float(mid))
                except Exception:
                    pass
            else:
                try:
                    mid2 = float((WalletRuntime._LAST_KNOWN_VALID_PRICES.get(s_key, 0.0)) or 0.0)
                except Exception:
                    mid2 = 0.0
                if mid2 > 0.0:
                    mid = mid2
                else:
                    mid = float(getattr(pos, "entry_px", 0.0) or 0.0)
            eq += float(pos.qty) * float(mid) * (float(usdt_irt_mid) if (usdt_irt_mid is not None and _canon_symbol(sym).endswith('USDT')) else 1.0)
        return float(eq)
    async def _low_priority_call(self, fn, *args, **kwargs) -> None:
        if fn is None:
            return
        try:
            tmo = float(getattr(getattr(self, "cfg", None), "low_priority_timeout_sec", 0.0) or 0.0)
        except Exception:
            tmo = 0.0
        try:
            res = fn(*args, **kwargs)
            if asyncio.iscoroutine(res):
                if tmo > 0.0:
                    await asyncio.wait_for(res, timeout=tmo)
                else:
                    await res
            else:
                return
        except asyncio.CancelledError:
            raise
        except Exception as e:
            try:
                self._log.exception("event=LOWPRIO_ERR fn=%s err=%s", str(getattr(fn, "__name__", "fn")), str(e)[:200])
            except Exception:
                logging.exception("event=LOWPRIO_ERR fn=%s", str(getattr(fn, "__name__", "fn")))
    async def _process_symbol_heartbeat(self, w: WalletRuntime, sym: str, cash_irt: float) -> None:
        sym = _canon_symbol(sym)
        try:
            _hb_state = getattr(w, "_hb_state", None)
            if not isinstance(_hb_state, dict):
                _hb_state = {}
                setattr(w, "_hb_state", _hb_state)
        except Exception:
            _hb_state = {}
        pos = None
        has_pos = False
        try:
            pos = (getattr(w, "positions", None) or {}).get(sym)
        except Exception:
            pos = None
        try:
            has_pos = (pos is not None) and float(getattr(pos, "qty", 0.0) or 0.0) > 0.0
        except Exception:
            has_pos = bool(pos)
        def _normalize_pos_local() -> None:
            nonlocal pos, has_pos
            try:
                q0 = float(getattr(pos, "qty", 0.0) or 0.0) if pos is not None else 0.0
            except Exception:
                q0 = 0.0
            if pos is not None and q0 <= 0.0:
                try:
                    (getattr(w, "positions", None) or {}).pop(sym, None)
                except Exception:
                    pass
                pos = None
                has_pos = False
        _normalize_pos_local()
        def _hb_mark(key: str) -> None:
            try:
                rec = _hb_state.get(sym) or {}
                prev = str(rec.get("key") or "")
                if prev != str(key):
                    _hb_state[sym] = {"key": str(key), "last_change_ts": float(time.time())}
                else:
                    if "last_change_ts" not in rec:
                        rec["last_change_ts"] = float(time.time())
                        _hb_state[sym] = rec
            except Exception:
                pass
        def _set_engine(status: str, reason: str, *, reject: bool = False, meta: dict | None = None) -> None:
            try:
                w.last_engine_status = str(status or "").strip()
                w.last_engine_reason = str(reason or "").strip()
                w.last_engine_ts = float(time.time())
            except Exception:
                pass
            if reject:
                try:
                    _obs_reject(w, str(reason or ""), symbol=sym, meta=dict(meta or {}))
                except Exception:
                    pass
                try:
                    _VETO_REG.note(
                        wallet=str(getattr(w, "name", "") or getattr(w, "id", "") or getattr(w, "wallet", "") or ""),
                        symbol=str(sym or ""),
                        status=str(status or ""),
                        reason=str(reason or ""),
                        meta=dict(meta or {}),
                    )
                except Exception:
                    pass
                try:
                    _record_why_no_trade(
                        self,
                        wallet=str(getattr(w, 'name', '') or getattr(w, 'id', '') or ''),
                        sym=str(sym or ''),
                        status=str(status or ''),
                        reason=str(reason or ''),
                        meta=dict(meta or {}),
                    )
                except Exception:
                    pass
        def _throttle_entry(reason: str, **meta) -> None:
            try:
                sec = float(getattr(self.cfg, "entry_throttle_sec", 2.0) or 2.0)
            except Exception:
                sec = 2.0
            now0 = time.time()
            try:
                until0 = float(getattr(w, "_entry_throttle_until", 0.0) or 0.0)
            except Exception:
                until0 = 0.0
            try:
                setattr(w, "_entry_throttle_until", float(max(until0, now0 + max(0.2, sec))))
            except Exception:
                pass
            try:
                meta.setdefault("entry_attempt", (not has_pos))
                meta.setdefault("stage", "ENTRY")
            except Exception:
                pass
            _set_engine("Run", str(reason or "ENTRY_THROTTLED"), reject=True, meta=meta)
        def _pending_guard(side: str, *, stage: str) -> bool:
            try:
                pend = self.orders.pending() if hasattr(self, "orders") else {}
            except Exception:
                pend = {}
            if not isinstance(pend, dict) or not pend:
                return False
            wallet_name = str(getattr(w, "name", "") or getattr(w, "id", "") or getattr(w, "wallet", "") or "")
            side_l = str(side or "").lower().strip()
            stg = str(stage or "").strip().upper()
            entry_attempt = (not has_pos) if stg == "ENTRY" else False
            for cid0, rec0 in pend.items():
                if not isinstance(rec0, dict):
                    continue
                if str(rec0.get("wallet") or "") != wallet_name:
                    continue
                if _canon_symbol(rec0.get("symbol") or "") != sym:
                    continue
                rec_side = str(rec0.get("side") or "").lower().strip()
                if rec_side not in ("buy", "sell"):
                    continue
                # EXIT stage: only block if the pending order is the same side (prevents double-exit);
                # entry-side BUY pending is handled separately by the explicit exit safety guard.
                if stg == "EXIT" and rec_side != side_l:
                    continue
                st = str(rec0.get("state") or "PENDING").upper()
                try:
                    w.last_event = f"{rec_side.upper()}_PENDING {sym}"
                except Exception:
                    pass
                _set_engine(
                    "Run",
                    "ORDER_PENDING",
                    reject=True,
                    meta={"sym": sym, "stage": stg, "entry_attempt": entry_attempt, "side": side_l, "pending_side": rec_side, "cid": str(cid0), "state": st},
                )
                return True
            return False
        def _apply_resolved_fills() -> None:
            try:
                oj = getattr(self, "orders", None)
                if oj is None:
                    return
                resolved = oj.resolved()
                if not isinstance(resolved, dict) or not resolved:
                    return
                wallet_name = str(getattr(w, "name", "") or getattr(w, "id", "") or getattr(w, "wallet", "") or "")
                rhb = _hb_state.get(sym) or {}
                if not isinstance(rhb, dict):
                    rhb = {}
                cand = []
                try:
                    if isinstance(rhb.get("last_buy_cids"), list):
                        cand.extend([str(x) for x in (rhb.get("last_buy_cids") or []) if x])
                except Exception:
                    pass
                try:
                    if rhb.get("last_buy_cid"):
                        cand.append(str(rhb.get("last_buy_cid")))
                except Exception:
                    pass
                try:
                    if isinstance(rhb.get("last_sell_cids"), list):
                        cand.extend([str(x) for x in (rhb.get("last_sell_cids") or []) if x])
                except Exception:
                    pass
                try:
                    if rhb.get("last_sell_cid"):
                        cand.append(str(rhb.get("last_sell_cid")))
                except Exception:
                    pass
                try:
                    _seen = set()
                    _out = []
                    for _c in (cand or []):
                        if not _c:
                            continue
                        if _c in _seen:
                            continue
                        _seen.add(_c)
                        _out.append(_c)
                    cand = _out
                except Exception:
                    pass
                def _apply_one(cid0: str) -> bool:
                    rec0 = resolved.get(str(cid0))
                    if not isinstance(rec0, dict):
                        return False
                    if rec0.get("local_applied"):
                        return True
                    if str(rec0.get("wallet") or "") != wallet_name:
                        return False
                    if _canon_symbol(rec0.get("symbol") or "") != sym:
                        return False
                    st = str(rec0.get("state") or "").upper()
                    side0 = str(rec0.get("side") or "").lower().strip()
                    fq = 0.0
                    fp = 0.0
                    try:
                        fq = float(rec0.get("fill_qty") or 0.0)
                    except Exception:
                        fq = 0.0
                    filled_states = {"FILLED", "DONE", "CLOSED"}
                    if str(st) in {"REJECTED"}:
                        try:
                            oj.mark_local_applied(str(cid0), note=f"skip_rejected st={st}")
                        except Exception:
                            pass
                        return True
                    if fq <= 0.0:
                        # Recover partial fills for CANCEL/EXPIRE states when fill_qty wasn't captured yet.
                        try:
                            raw0 = rec0.get("final_raw") or rec0.get("ack_raw")
                            if isinstance(raw0, dict):
                                fq2 = float(OrderJournal._order_filled_qty(raw0) or 0.0)
                                if fq2 > 0.0:
                                    fq = fq2
                                    if fp <= 0.0:
                                        try:
                                            fp2 = float(OrderJournal._order_avg_px(raw0, fq2) or 0.0)
                                        except Exception:
                                            fp2 = 0.0
                                        if fp2 > 0.0:
                                            fp = fp2
                        except Exception:
                            pass
                        if fq <= 0.0:
                            if str(st) in filled_states:
                                try:
                                    fq = float(rec0.get("qty") or 0.0)
                                except Exception:
                                    fq = 0.0
                            else:
                                # Do not permanently mark local_applied when the fill is unknown; allow a short
                                # window for reconcile_wallet() to populate fill_qty/fill_px (partial fills on cancel).
                                try:
                                    tsr = float(rec0.get("final_ts") or rec0.get("ack_ts") or rec0.get("ts") or 0.0) or 0.0
                                    tsr = tsr / 1000.0 if tsr and tsr > 1e11 else tsr
                                    if tsr > 0.0:
                                        age_r = float(time.time() - tsr)
                                    else:
                                        age_r = float("inf")
                                except Exception:
                                    age_r = float("inf")
                                try:
                                    retry_sec = float(_env_float("ORDER_FILL_RETRY_SEC", 120.0) or 120.0)
                                except Exception:
                                    retry_sec = 120.0
                                if age_r < float(max(5.0, retry_sec)):
                                    return False
                                try:
                                    oj.mark_local_applied(str(cid0), note=f"skip_not_filled st={st}")
                                except Exception:
                                    pass
                                return True
                    try:
                        fp = float(rec0.get("fill_px") or 0.0)
                    except Exception:
                        fp = 0.0
                    if fp <= 0.0:
                        try:
                            fp = float(rec0.get("price") or 0.0)
                        except Exception:
                            fp = 0.0
                    if fq <= 0.0 or side0 not in ("buy", "sell"):
                        try:
                            oj.mark_local_applied(str(cid0), note=f"skip_side={side0} st={st}")
                        except Exception:
                            pass
                        return True
                    if side0 == "buy":
                        try:
                            cur0 = (getattr(w, "positions", None) or {}).get(sym)
                            if cur0 is None or float(getattr(cur0, "qty", 0.0) or 0.0) <= 0.0:
                                w.positions[sym] = Position(sym, float(fq), float(fp) if float(fp) > 0.0 else float(rec0.get("price") or 0.0), time.time())
                            else:
                                try:
                                    cur_qty = float(getattr(cur0, "qty", 0.0) or 0.0)
                                except Exception:
                                    cur_qty = 0.0
                                add_qty = float(fq)
                                new_qty = float(max(0.0, cur_qty + add_qty))
                                if new_qty > 0.0:
                                    try:
                                        entry_px0 = float(getattr(cur0, "entry_px", 0.0) or 0.0)
                                    except Exception:
                                        entry_px0 = 0.0
                                    fill_px = float(fp) if float(fp) > 0.0 else 0.0
                                    if entry_px0 > 0.0 and fill_px > 0.0 and cur_qty > 0.0:
                                        try:
                                            cur0.entry_px = float((entry_px0 * cur_qty + fill_px * add_qty) / new_qty)
                                        except Exception:
                                            pass
                                    elif entry_px0 <= 0.0 and fill_px > 0.0:
                                        cur0.entry_px = float(fill_px)
                                    cur0.qty = float(new_qty)
                            try:
                                w.last_event = f"BUY_FILLED {sym} qty={float(fq):.6f}"
                            except Exception:
                                pass
                            _set_engine("Run", "BUY_FILLED", reject=False, meta={"sym": sym, "qty": float(fq), "cid": str(cid0), "st": st})
                        except Exception:
                            pass
                    else:
                        try:
                            cur0 = (getattr(w, "positions", None) or {}).get(sym)
                            if cur0 is not None and float(getattr(cur0, "qty", 0.0) or 0.0) > 0.0:
                                close_qty = float(min(float(getattr(cur0, "qty", 0.0) or 0.0), float(fq)))
                                exit_px = float(fp) if float(fp) > 0.0 else float(rec0.get("price") or 0.0)
                                entry_px = float(getattr(cur0, "entry_px", 0.0) or 0.0)
                                entry_known = False
                                try:
                                    entry_known = bool((entry_px > 0.0) and math.isfinite(float(entry_px)))
                                except Exception:
                                    entry_known = False
                                # Unknown entry_px would corrupt PnL/risk accounting; treat as flat and skip stats.
                                if not entry_known:
                                    try:
                                        if exit_px > 0.0 and math.isfinite(float(exit_px)):
                                            entry_px = float(exit_px)
                                        else:
                                            entry_px = 0.0
                                    except Exception:
                                        entry_px = 0.0
                                pnl_quote = (exit_px - entry_px) * close_qty
                                conv_known = True
                                conv_irt = 1.0
                                try:
                                    # USDT-quote pairs need a valid USDTIRT conversion to keep IRT PnL accounting truthful.
                                    if str(sym or "").upper().endswith("USDT"):
                                        conv_known = bool(float(usdt_irt_mid or 0.0) > 0.0 and math.isfinite(float(usdt_irt_mid)))
                                    qm = float(quote_mult or 1.0)
                                    if math.isfinite(qm) and qm > 0.0:
                                        conv_irt = 1.0 / qm
                                except Exception:
                                    conv_known = (not str(sym or "").upper().endswith("USDT"))
                                    conv_irt = 1.0
                                pnl_irt = float(pnl_quote) * float(conv_irt) if conv_known else 0.0
                                if entry_known and conv_known:
                                    try:
                                        w.pnl_realized_irt += float(pnl_irt)
                                    except Exception:
                                        pass
                                pnl_pct = (exit_px - entry_px) / entry_px if entry_px > 0 else 0.0
                                if entry_known and conv_known:
                                    try:
                                        self.risk.register_close(sym, float(pnl_irt), float(pnl_pct), cash_irt=float(max(float(getattr(w, "cash_irt", 0.0) or 0.0), float(cash_irt or 0.0))))
                                    except Exception:
                                        pass
                                    try:
                                        pm = getattr(self, "perf_monitor", None)
                                        if pm is not None:
                                            pm.record_trade(symbol=sym, wallet=str(getattr(w, "name", "")), pnl_irt=float(pnl_irt), pnl_pct=float(pnl_pct))
                                    except Exception:
                                        pass
                                rem = float(max(0.0, float(getattr(cur0, "qty", 0.0) or 0.0) - close_qty))
                                if rem <= 1e-10:
                                    w.positions.pop(sym, None)
                                    try:
                                        m1 = getattr(w, "_last_exit_ts_by_sym", None)
                                        if not isinstance(m1, dict):
                                            m1 = {}
                                        m1[sym] = float(time.time())
                                        setattr(w, "_last_exit_ts_by_sym", m1)
                                    except Exception:
                                        pass
                                else:
                                    cur0.qty = rem
                                try:
                                    if bool(locals().get("conv_known", True)):
                                        w.last_event = f"SELL_FILLED {sym} pnl={float(pnl_irt):.0f}"
                                    else:
                                        w.last_event = f"SELL_FILLED {sym} pnl=?"
                                except Exception:
                                    pass
                                try:
                                    _m0 = {"sym": sym, "qty": close_qty, "pnl_irt": float(pnl_irt), "cid": str(cid0), "st": st, "conv_known": bool(locals().get("conv_known", True))}
                                    if not bool(locals().get("conv_known", True)):
                                        _m0.update({"pnl_quote": float(pnl_quote), "usdt_irt_mid": float(usdt_irt_mid or 0.0)})
                                except Exception:
                                    _m0 = {"sym": sym, "qty": close_qty, "pnl_irt": float(pnl_irt), "cid": str(cid0), "st": st}
                                _set_engine("Run", "SELL_FILLED", reject=False, meta=_m0)
                        except Exception:
                            pass
                    try:
                        oj.mark_local_applied(str(cid0), note=f"applied_{side0} st={st}")
                    except Exception:
                        pass
                    return True
                for cid0 in cand:
                    _apply_one(cid0)
                if not cand:
                    try:
                        last_scan = float(rhb.get("last_resolved_scan_ts", 0.0) or 0.0)
                    except Exception:
                        last_scan = 0.0
                    if (time.time() - last_scan) >= 20.0:
                        rhb["last_resolved_scan_ts"] = float(time.time())
                        _hb_state[sym] = rhb
                        applied = 0
                        for cid0, rec0 in list(resolved.items()):
                            if applied >= 2:
                                break
                            if not isinstance(rec0, dict):
                                continue
                            if rec0.get("local_applied"):
                                continue
                            if str(rec0.get("wallet") or "") != wallet_name:
                                continue
                            if _canon_symbol(rec0.get("symbol") or "") != sym:
                                continue
                            if str(rec0.get("side") or "").lower().strip() not in ("buy", "sell"):
                                continue
                            if _apply_one(str(cid0)):
                                applied += 1
            except Exception:
                pass
        snap_state = "OK"
        snap_conf = 100.0
        snap_size_mult = 1.0
        quote_mult = 1.0
        usdt_px_wait = False
        if sym.endswith("USDT"):
            try:
                usdt_free = float((getattr(w, "assets_snapshot", None) or {}).get("USDT") or 0.0)
            except Exception:
                usdt_free = 0.0
            usdt_irt_mid = 0.0
            try:
                cache = getattr(self.feed, "_cache", None) or {}
                c = cache.get("USDTIRT")
                if c is not None:
                    _ts, _ob = c
                    usdt_irt_mid = float(getattr(_ob, "mid", 0.0) or 0.0)
            except Exception:
                usdt_irt_mid = 0.0
            if usdt_irt_mid <= 0.0:
                try:
                    usdt_irt_mid = float(self.feed.peek_mid("USDTIRT") or 0.0)
                except Exception:
                    usdt_irt_mid = 0.0
            if usdt_irt_mid <= 0.0:
                try:
                    usdt_irt_mid = float(WalletRuntime._LAST_KNOWN_VALID_PRICES.get("USDTIRT", 0.0) or 0.0)
                except Exception:
                    usdt_irt_mid = 0.0
            if usdt_irt_mid <= 0.0:
                # Probe USDTIRT spot price as a last resort (keeps USDT-quote accounting deterministic).
                try:
                    tmo = float(os.getenv("USDT_PX_PROBE_TIMEOUT_SEC", "1.2") or "1.2")
                except Exception:
                    tmo = 1.2
                tmo = max(0.35, min(3.0, float(tmo)))
                try:
                    usdt_px = await asyncio.wait_for(self.feed.fetch_spot("USDTIRT"), timeout=tmo)
                    if usdt_px is not None and float(usdt_px) > 0.0 and math.isfinite(float(usdt_px)):
                        usdt_irt_mid = float(usdt_px)
                except Exception:
                    pass
            if usdt_irt_mid > 0.0 and math.isfinite(float(usdt_irt_mid)):
                try:
                    WalletRuntime.set_last_known_price("USDTIRT", float(usdt_irt_mid))
                except Exception:
                    pass
                try:
                    quote_mult = 1.0 / float(usdt_irt_mid)
                except Exception:
                    quote_mult = 1.0
            if usdt_free > 0.0 and usdt_irt_mid > 0.0 and math.isfinite(float(usdt_irt_mid)):
                cash_irt = float(usdt_free) * float(usdt_irt_mid)
            else:
                if not has_pos:
                    try:
                        w.last_reject_reason = "Wait_X"
                    except Exception:
                        pass
                    w.last_event = f"WAIT_USDT_PX {sym}"
                    usdt_px_wait = True
                    _set_engine('Hold', 'WAIT_USDT_PX', reject=True, meta={'sym': sym, 'stage': 'FSM', 'entry_attempt': (not has_pos)})
        _apply_resolved_fills()
        try:
            pos = (getattr(w, "positions", None) or {}).get(sym)
        except Exception:
            pos = None
        try:
            has_pos = (pos is not None) and float(getattr(pos, "qty", 0.0) or 0.0) > 0.0
        except Exception:
            has_pos = bool(pos)
        _normalize_pos_local()
        async def _rej(reason: str, **meta) -> None:
            r = str(reason or "").upper().strip()
            try:
                meta.setdefault("entry_attempt", (not has_pos))
                meta.setdefault("stage", "ENTRY")
            except Exception:
                pass
            if r in ("LOW_SC","LOW_VOL","TREND_G","SPREAD","DYN_ADJ","NOTIONAL","PROFIT_GATE","MAX_POS","WAIT_X","DATA_HALT",
                     "NOBOOK","STALE_BOOK","NET_SYM_PAUSE","SOFT_BLACKLIST","DATA_RISK_NO_ENTRY","RISK_COOLDOWN"):
                _throttle_entry(reason, **meta)
                return
            st = "Hold" if r in ("BLACKLIST",) else "Run"
            _set_engine(st, str(reason or ""), reject=True, meta=meta)
        try:
            if self.feed.is_ignored(sym):
                w.last_event = f"BLACKLIST {sym}"
                await _rej("BLACKLIST", sym=sym)
                if not has_pos:
                    return
        except Exception:
            pass
        soft_blocked = False
        soft_score = 0.0
        try:
            if hasattr(self, "soft_blacklist"):
                try:
                    soft_score = float(self.soft_blacklist.get_score(sym) or 0.0)
                except Exception:
                    soft_score = 0.0
                try:
                    soft_blocked = bool(self.soft_blacklist.is_blocked(sym))
                except Exception:
                    soft_blocked = False
                if soft_blocked:
                    w.last_event = f"SOFT_BLACKLIST {sym}"
                    await _rej("SOFT_BLACKLIST", sym=sym, score=float(soft_score))
                    if not has_pos:
                        return
        except Exception:
            pass
        net_pause_sec = 0.0
        try:
            if hasattr(self.net, "symbol_pause_remaining") and callable(getattr(self.net, "symbol_pause_remaining")):
                net_pause_sec = float(self.net.symbol_pause_remaining(sym) or 0.0)
            elif hasattr(self.net, "symbol_pause_remaining_sec") and callable(getattr(self.net, "symbol_pause_remaining_sec")):
                net_pause_sec = float(self.net.symbol_pause_remaining_sec(sym) or 0.0)
        except Exception:
            net_pause_sec = 0.0
        if net_pause_sec > 0.0 and (not has_pos):
            w.last_event = f"NET_SYM_PAUSE {sym}"
            await _rej("NET_SYM_PAUSE", sym=sym, pause_sec=float(net_pause_sec))
            return
        force_refresh = False
        try:
            hb_state = getattr(w, "_hb_state", None)
            if isinstance(hb_state, dict):
                rec = hb_state.get(sym) or {}
                last_change = float(rec.get("last_change_ts", 0.0) or 0.0)
                if last_change and (time.time() - last_change) >= 300.0:
                    force_refresh = True
        except Exception:
            force_refresh = False
        _depth_latency_ms = None
        book_ts = None
        spot_ts = None
        book_fallback = False
        try:
            if getattr(self, "obsvc", None) is not None:
                try:
                    self.obsvc.request_refresh(sym, use_disk_cache_on_timeout=w.cfg.price_cache_on_timeout, force_refresh=force_refresh)
                except Exception:
                    pass
                book = self.obsvc.peek(sym)
                try:
                    if book is not None:
                        book_ts = book_ts or getattr(book, 'ts', None) or getattr(book, 'timestamp', None)
                except Exception:
                    pass
            else:
                book = None
                try:
                    c = getattr(self.feed, "_cache", None) or {}
                    rec = c.get(sym)
                    if rec is not None:
                        _ts, book = rec
                        book_ts = _ts
                except Exception:
                    book = None
                try:
                    asyncio.create_task(self.feed.fetch_depth(sym, use_disk_cache_on_timeout=w.cfg.price_cache_on_timeout, force_refresh=force_refresh))
                except Exception:
                    pass
        except Exception as e:
            book = None
            try:
                self._log.warning("event=DEPTH_BG_FAIL sym=%s err=%s", sym, str(e))
            except Exception:
                pass
        # Derive depth data latency/age in ms (used by Sanity + telemetry).
        # If the book object lacks a timestamp, treat the peek time as "now" so Phoenix/Health do not
        # incorrectly mark it as NO_TS / infinite age.
        try:
            if book is not None:
                try:
                    b_age = getattr(book, "age_sec", None)
                    if b_age is not None:
                        a0 = float(b_age or 0.0)
                        if math.isfinite(a0) and a0 >= 0.0:
                            _depth_latency_ms = float(a0 * 1000.0)
                except Exception:
                    pass
                ts_src = _parse_ts_sec(book_ts) or _parse_ts_sec(getattr(book, "ts", None)) or _parse_ts_sec(getattr(book, "timestamp", None))
                if ts_src is None:
                    # Unknown/missing timestamp => treat as stale fallback (fail-closed for entries).
                    book_fallback = True
                    try:
                        setattr(book, "_stale", True)
                        _src0 = str(getattr(book, "_source", "") or "")
                        if _src0:
                            if "NO_TS" not in _src0:
                                setattr(book, "_source", f"{_src0}:NO_TS")
                        else:
                            setattr(book, "_source", "NO_TS")
                    except Exception:
                        pass
                if _depth_latency_ms is None and ts_src is not None:
                    try:
                        age_s = float(time.time()) - float(ts_src or 0.0)
                        if (not math.isfinite(age_s)) or age_s < 0.0:
                            age_s = 0.0
                        _depth_latency_ms = float(age_s * 1000.0)
                    except Exception:
                        _depth_latency_ms = None
        except Exception:
            pass

        if book is None:
            w.last_event = f"{sym} NOBOOK"
            spot_ok = False
            try:
                tmo = float(os.getenv("NOBOOK_SPOT_PROBE_TIMEOUT_SEC", "1.5") or "1.5")
            except Exception:
                tmo = 1.5
            tmo = max(0.4, min(5.0, float(tmo)))
            try:
                px = await asyncio.wait_for(self.feed.fetch_spot(sym), timeout=tmo)
                if px is not None and float(px) > 0.0:
                    spot_ok = True
            except Exception:
                spot_ok = False
            allow_spot_ready = False
            try:
                allow_spot_ready = bool(_env_bool("PHOENIX_ALLOW_SPOT_READY", bool(getattr(self.cfg, "phoenix_allow_spot_ready", False))))
            except Exception:
                allow_spot_ready = False
            spot_ready_mode = bool(spot_ok and allow_spot_ready and bool(getattr(self.cfg, "phoenix_enabled", True)))
            spot_entry_mode = bool((not has_pos) and spot_ready_mode)
            if (not spot_ready_mode):
                await _rej("NOBOOK", sym=sym)
            if not spot_ok:
                try:
                    if hasattr(self, 'soft_blacklist'):
                        self.soft_blacklist.on_error(sym, 'NOBOOK', reason=f"NOBOOK:{sym}")
                except Exception:
                    pass
                try:
                    self.net.on_error(sym, "NOBOOK")
                except Exception:
                    pass
            else:
                try:
                    self._log.warning("event=NOBOOK_SPOT_OK sym=%s spot_entry=%s", sym, int(bool(spot_entry_mode)))
                except Exception:
                    pass
            try:
                pho = None
                spot0 = None
                ts0 = None  # ensure defined even if spot cache access fails
                try:
                    sc = getattr(self.feed, "_spot_cache", None) or {}
                    rec0 = sc.get(sym)
                    ts0 = None
                    now0 = float(time.time())
                    ttl0 = float(getattr(self.feed, "_ttl", 1.2) or 1.2)
                    ttl0 = max(ttl0, 2.0)
                    if rec0 is not None and isinstance(rec0, (tuple, list)) and len(rec0) >= 2:
                        ts0, px0 = rec0[0], rec0[1]
                        try:
                            if px0 is not None and float(px0) > 0.0:
                                spot0 = float(px0)
                        except Exception:
                            spot0 = None
                        try:
                            if (now0 - float(ts0 or 0.0)) > (2.0 * ttl0):
                                asyncio.create_task(self.feed.fetch_spot(sym))
                        except Exception:
                            pass
                    else:
                        try:
                            asyncio.create_task(self.feed.fetch_spot(sym))
                        except Exception:
                            pass
                except Exception:
                    spot0 = None
                # If spot was successfully probed (px) but the spot cache wasn't populated yet,
                # fall back to the probed price so Phoenix can make a consistent decision.
                try:
                    _px_probe = locals().get("px", None)
                    if spot0 is None and _px_probe is not None and float(_px_probe) > 0.0 and math.isfinite(float(_px_probe)):
                        spot0 = float(_px_probe)
                        if ts0 is None:
                            ts0 = float(time.time())
                except Exception:
                    pass
                if bool(getattr(self.cfg, "phoenix_enabled", True)):
                    try:
                        pho = self.phoenix.update(sym, None, None, spot0, depth_latency_ms=None, spot_ts=ts0)
                    except Exception:
                        pho = None
                try:
                    if spot0 is not None:
                        px0 = float(spot0 or 0.0)
                        if px0 > 0.0 and math.isfinite(px0):
                            px_hist = getattr(self, "_phoenix_px_hist", None)
                            if not isinstance(px_hist, dict):
                                px_hist = {}
                                setattr(self, "_phoenix_px_hist", px_hist)
                            try:
                                max_points = int(_env_int("PHOENIX_FLOW_MAX_POINTS", 240) or 240)
                            except Exception:
                                max_points = 240
                            max_points = int(max(60, min(600, max_points)))
                            symk = _canon_symbol(sym)
                            dq = px_hist.get(symk)
                            if dq is None or (not isinstance(dq, deque)):
                                dq = __import__("collections").deque(maxlen=int(max_points))
                                px_hist[symk] = dq
                            now_ts0 = float(time.time())
                            try:
                                accept_dt = float(os.getenv("PHOENIX_FLOW_MIN_DT_SEC", "0.05") or 0.05)
                            except Exception:
                                accept_dt = 0.05
                            if (not dq) or (now_ts0 - float(dq[-1][0] or 0.0)) >= float(accept_dt):
                                dq.append((now_ts0, float(px0)))
                            sym_u = getattr(self, "_phoenix_sym_last_update", None)
                            if not isinstance(sym_u, dict):
                                sym_u = {}
                                setattr(self, "_phoenix_sym_last_update", sym_u)
                            sym_u[symk] = float(now_ts0)
                except Exception:
                    pass
                if pho is None:
                    try:
                        pho = self.phoenix.get_last_decision(sym)
                    except Exception:
                        pho = None
                if pho is None:
                    pho = PhoenixDecision(
                        state="FLAT",
                        confidence=0.0,
                        composite=0.0,
                        rsi=50.0,
                        shadow_score=0.0,
                        shadow_label="NOBOOK",
                        ready=False,
                        reason="NOBOOK",
                    )
                try:
                    w.phoenix_state = str(getattr(pho, "state", "FLAT"))
                    w.phoenix_conf = float(getattr(pho, "confidence", 0.0) or 0.0)
                    w.phoenix_rsi = getattr(pho, "rsi", None)
                    w.phoenix_shadow = getattr(pho, "shadow_score", None)
                    w.phoenix_composite = float(getattr(pho, "composite", 0.0) or 0.0)
                except Exception:
                    pass
            except Exception:
                pass
            if (not has_pos) and (not spot_entry_mode):
                return
            try:
                mid_fb = 0.0
                for _pxc in (locals().get("spot0"), locals().get("px"), None):
                    try:
                        if _pxc is not None and float(_pxc) > 0.0:
                            mid_fb = float(_pxc)
                            break
                    except Exception:
                        continue
                if mid_fb <= 0.0:
                    try:
                        mid_fb = float((WalletRuntime._LAST_KNOWN_VALID_PRICES.get(sym, 0.0)) or 0.0)
                    except Exception:
                        mid_fb = 0.0
                if mid_fb <= 0.0:
                    try:
                        mid_fb = float(getattr(pos, "entry_px", 0.0) or 0.0)
                    except Exception:
                        mid_fb = 0.0
                half_bps = 0.0
                try:
                    half_bps = float(
                        max(
                            5.0,
                            float(getattr(self.cfg, "order_safety_bps", 10.0) or 10.0) + float(getattr(self.cfg, "slippage_bps", 5.0) or 5.0),
                        )
                    )
                except Exception:
                    half_bps = 15.0
                if mid_fb <= 0.0:
                    return
                bid_fb = float(mid_fb) * (1.0 - float(half_bps) / 10000.0)
                ask_fb = float(mid_fb) * (1.0 + float(half_bps) / 10000.0)
                spr_fb = (float(ask_fb) - float(bid_fb)) / float(mid_fb) * 10000.0 if mid_fb > 0 else float(half_bps * 2.0)
                book = OrderBookTop(bid=float(max(1e-9, bid_fb)), ask=float(max(1e-9, ask_fb)), mid=float(mid_fb), spread_bps=float(max(0.0, spr_fb)))
                try:
                    setattr(book, "last_trade_price", float(mid_fb))
                except Exception:
                    pass
                try:
                    setattr(book, "_stale", True)
                    setattr(book, "_source", "SPOT_FALLBACK")
                    setattr(book, "ts", float(time.time()))
                except Exception:
                    pass
                if spot_ready_mode:
                    try:
                        setattr(book, "_stale", False)
                        setattr(book, "_source", "SPOT_READY")
                    except Exception:
                        pass
                book_fallback = bool(getattr(book, "_stale", False))
            except Exception:
                return
        # Treat stale synthetic/timeout books as fallback for exit logic (prevents score-based churn on stale data).
        try:
            book_fallback = bool(book is not None and bool(getattr(book, "_stale", False)))
        except Exception:
            pass

        if not book_fallback:
            try:
                self.net.on_ok(sym)
            except Exception:
                pass
            try:
                if hasattr(self, 'soft_blacklist'):
                    self.soft_blacklist.on_ok(sym)
            except Exception:
                pass
        try:
            mid0 = float(getattr(book, "mid", 0.0) or 0.0)
            if mid0 > 0.0 and math.isfinite(mid0):
                px_hist = getattr(self, "_phoenix_px_hist", None)
                if not isinstance(px_hist, dict):
                    px_hist = {}
                    setattr(self, "_phoenix_px_hist", px_hist)
                try:
                    max_points = int(_env_int("PHOENIX_FLOW_MAX_POINTS", 240) or 240)
                except Exception:
                    max_points = 240
                max_points = int(max(60, min(600, max_points)))
                symk = _canon_symbol(sym)
                dq = px_hist.get(symk)
                if dq is None or (not isinstance(dq, deque)):
                    dq = __import__("collections").deque(maxlen=int(max_points))
                    px_hist[symk] = dq
                now_ts0 = float(time.time())
                try:
                    accept_dt = float(os.getenv("PHOENIX_FLOW_MIN_DT_SEC", "0.05") or 0.05)
                except Exception:
                    accept_dt = 0.05
                _skip_tick = False
                _seed_ref = 0.0
                try:
                    clamp_pct = float(_env_float("TOP8_CHANGE_CLAMP_PCT", 30.0) or 30.0)
                    last_p = float(dq[-1][1] or 0.0) if dq else 0.0
                    _seed_ref = float(last_p)
                    if last_p > 0:
                        one_tick = ((float(mid0) - last_p) / last_p) * 100.0
                        if math.isfinite(one_tick) and abs(one_tick) > float(clamp_pct):
                            _skip_tick = True
                except Exception:
                    _skip_tick = False
                _px_hist_changed = False
                if not dq:
                    if not _skip_tick:
                        dq.append((now_ts0, float(mid0)))
                        _px_hist_changed = True
                elif len(dq) == 1:
                    try:
                        t_last = float(dq[-1][0] or now_ts0)
                    except Exception:
                        t_last = float(now_ts0)
                    if (now_ts0 - t_last) < float(accept_dt):
                        pass
                    else:
                        if not _skip_tick:
                            dq.append((now_ts0, float(mid0)))
                            _px_hist_changed = True
                else:
                    if (now_ts0 - float(dq[-1][0] or 0.0)) >= float(accept_dt):
                        if not _skip_tick:
                            dq.append((now_ts0, float(mid0)))
                            _px_hist_changed = True
                try:
                    if _px_hist_changed and len(dq) >= 2:
                        _dp_map = getattr(self, "_phoenix_flow_dp_pct", None)
                        if not isinstance(_dp_map, dict):
                            _dp_map = {}
                            setattr(self, "_phoenix_flow_dp_pct", _dp_map)
                        _op = float(dq[0][1] or 0.0)
                        _lp = float(dq[-1][1] or 0.0)
                        if _op > 0.0 and _lp > 0.0 and math.isfinite(_op) and math.isfinite(_lp):
                            _dp_map[symk] = ((_lp - _op) / _op) * 100.0
                            _dp_ts = getattr(self, "_phoenix_flow_dp_ts", None)
                            if not isinstance(_dp_ts, dict):
                                _dp_ts = {}
                                setattr(self, "_phoenix_flow_dp_ts", _dp_ts)
                            _dp_ts[symk] = float(now_ts0)
                except Exception:
                    pass
                sym_u = getattr(self, "_phoenix_sym_last_update", None)
                if not isinstance(sym_u, dict):
                    sym_u = {}
                    setattr(self, "_phoenix_sym_last_update", sym_u)
                sym_u[symk] = float(now_ts0)
        except Exception:
            pass
        health_size_mult = 1.0
        health_mode = "NORMAL"
        try:
            now_guard = float(time.time())
            thr = float(getattr(self.cfg, "market_age_skip_sec", 4.0) or 4.0)
            mts = 0.0
            try:
                mts = float(getattr(self, "_market_snapshot_local_ts", 0.0) or 0.0)
            except Exception:
                mts = 0.0
            if mts > 0.0:
                m_age = max(0.0, now_guard - mts)
            else:
                ts_api = None
                try:
                    ts_api = getattr(self, "_last_public_update_ts", None)
                except Exception:
                    ts_api = None
                if ts_api is None:
                    try:
                        pub = getattr(self, "public", None)
                    except Exception:
                        pub = None
                    if pub is not None:
                        for k in ("last_update_time", "last_update_ts", "_last_update_ts", "_last_public_update_ts", "last_ts", "_last_ts"):
                            try:
                                if hasattr(pub, k):
                                    ts_api = getattr(pub, k, None)
                                    if ts_api:
                                        break
                            except Exception:
                                continue
                try:
                    if ts_api is not None:
                        ts_api = float(ts_api or 0.0)
                        ts_api = ts_api / 1000.0 if ts_api and ts_api > 1e11 else ts_api
                        m_age = max(0.0, now_guard - ts_api)
                    else:
                        m_age = float(thr) * 2.0
                except Exception:
                    m_age = float(thr) * 2.0
            b_age = getattr(book, "age_sec", None)
            if b_age is None:
                b_ts = getattr(book, "ts", None)
                if b_ts is not None:
                    try:
                        b_age = max(0.0, now_guard - float(b_ts))
                    except Exception:
                        b_age = None
            b_age_f = float(b_age) if b_age is not None else float("inf")
            try:
                snap_conf = float(getattr(self, "_snap_confidence", 100.0) or 100.0)
            except Exception:
                snap_conf = 100.0
            try:
                snap_state = str(getattr(self, "_snap_state", "OK") or "OK").upper().strip()
            except Exception:
                snap_state = "OK"
            if snap_state not in ("OK", "DEGRADED", "CRITICAL"):
                snap_state = "OK"
            try:
                setattr(w, "snap_confidence", float(snap_conf))
                setattr(w, "snap_state", str(snap_state))
            except Exception:
                pass
            try:
                if snap_state == "DEGRADED":
                    snap_size_mult = max(0.0, min(1.0, float(snap_conf) / 100.0))
                elif snap_state == "CRITICAL":
                    snap_size_mult = 0.0
                else:
                    snap_size_mult = 1.0
            except Exception:
                snap_size_mult = 1.0
            try:
                if math.isfinite(b_age_f):
                    m_age = min(float(m_age), float(b_age_f))
            except Exception:
                pass
            try:
                sym_u = getattr(self, "_phoenix_sym_last_update", None)
                if isinstance(sym_u, dict):
                    ts_u = sym_u.get(sym)
                    if ts_u is not None:
                        sym_age = max(0.0, now_guard - float(ts_u))
                        thr_sym = float(os.getenv("PHOENIX_FLOW_TARGET_FRESH_SEC", "30") or 30.0)
                        if math.isfinite(sym_age) and sym_age <= thr_sym:
                            m_age = min(float(m_age), float(sym_age))
            except Exception:
                pass
            try:
                skew = float(getattr(self, "_market_age_s", 0.0) or 0.0)
            except Exception:
                skew = 0.0
            try:
                sym_u = getattr(self, "_phoenix_sym_last_update", None)
                if isinstance(sym_u, dict):
                    ts_u = sym_u.get(sym)
                    if ts_u is not None:
                        sym_age = max(0.0, now_guard - float(ts_u))
                        thr_sym = float(os.getenv("PHOENIX_FLOW_TARGET_FRESH_SEC", "30") or 30.0)
                        if math.isfinite(sym_age) and sym_age <= thr_sym:
                            skew = min(float(skew), float(sym_age))
            except Exception:
                pass
            try:
                if not math.isfinite(float(skew)):
                    skew = 0.0
            except Exception:
                skew = 0.0
            hc = getattr(self, "health_ctrl", None)
            if hc is not None:
                mid0 = None
                try:
                    mid0 = float(getattr(book, "mid", None) or getattr(book, "mid_price", None) or 0.0)
                    if mid0 <= 0.0 or not math.isfinite(mid0):
                        mid0 = None
                except Exception:
                    mid0 = None
                grace = 1.0
                try:
                    grace = _adaptive_timeout_grace_mult(self)
                except Exception:
                    grace = 1.0
                h = hc.evaluate(sym, m_age, b_age_f, skew, mid=mid0, now_ts=now_guard, grace_mult=grace)
                health_mode = str(getattr(h, "mode", "NORMAL") or "NORMAL")
                health_size_mult = float(getattr(h, "size_mult", 1.0) or 1.0)
                try:
                    setattr(w, "health_mode", health_mode)
                    setattr(w, "health_severity", float(getattr(h, "severity", 0.0) or 0.0))
                except Exception:
                    pass
                try:
                    pm = getattr(self, "perf_monitor", None)
                    stp = str(getattr(pm, "state", "HEALTHY") if pm is not None else "HEALTHY" or "HEALTHY").upper()
                    if stp == "DEGRADED":
                        health_size_mult *= 0.5
                    elif stp == "CRITICAL":
                        health_size_mult *= 0.0
                    try:
                        setattr(w, "perf_state", stp)
                    except Exception:
                        pass
                except Exception:
                    pass
                if health_mode == "HALT":
                    try:
                        w.last_event = f"{sym} DATA_HALT mkt={m_age:.1f}s book={b_age_f:.1f}s skew={skew:.1f}s"
                    except Exception:
                        pass
                    await _rej("DATA_HALT", mkt_age=m_age, book_age=b_age_f, skew=skew)
                    if not has_pos:
                        return
                elif health_mode in ("DEGRADED", "SOFT"):
                    try:
                        w.last_event = f"{sym} {health_mode} mkt={m_age:.1f}s book={b_age_f:.1f}s skew={skew:.1f}s"
                    except Exception:
                        pass
                    await _rej(f"DATA_{health_mode}", mkt_age=m_age, book_age=b_age_f, skew=skew, soft=True)
                    if not has_pos:
                        return
        except Exception:
            pass
        risk_decision: Optional[RiskDecision] = None
        try:
            rm = getattr(self, "risk", None)
            if rm is not None and hasattr(rm, "escalation"):
                comps: Dict[str, float] = {}
                try:
                    hs = float(getattr(w, "health_severity", 0.0) or 0.0)
                    comps["health"] = float(clamp(hs / 10.0, 0.0, 1.0))
                except Exception:
                    pass
                try:
                    if bool(soft_score) or bool(soft_blocked):
                        thr = 1.0
                        try:
                            thr = float(getattr(getattr(self, "soft_blacklist", None), "block_threshold", 1.0) or 1.0)
                        except Exception:
                            thr = 1.0
                        thr = float(max(1e-9, thr))
                        comps["soft_blacklist"] = float(clamp(float(soft_score) / thr, 0.0, 1.0))
                        if bool(soft_blocked):
                            comps["soft_blacklist"] = 1.0
                except Exception:
                    pass
                try:
                    if float(net_pause_sec) > 0.0:
                        comps["net_pause"] = 1.0
                except Exception:
                    pass
                try:
                    ss = str(getattr(self, "_snap_state", "OK") or "OK").upper().strip()
                    sc = float(getattr(self, "_snap_confidence", 100.0) or 100.0)
                except Exception:
                    ss, sc = "OK", 100.0
                if ss == "CRITICAL":
                    comps["snapshot"] = 1.0
                elif ss == "DEGRADED":
                    comps["snapshot"] = float(clamp(1.0 - (sc / 100.0), 0.0, 1.0))
                else:
                    comps["snapshot"] = 0.0
                risk_decision = rm.escalation.assess(w.name, sym, comps, now=now_guard)
                try:
                    rm.set_runtime_risk(w.name, sym, risk_decision)
                except Exception:
                    pass
                try:
                    rr = getattr(w, "risk_by_sym", None)
                    if not isinstance(rr, dict):
                        rr = {}
                    rr[sym] = {
                        "level": int(getattr(risk_decision, "level", 0)),
                        "score": float(getattr(risk_decision, "composite", 0.0)),
                        "size_mult": float(getattr(risk_decision, "size_mult", 1.0)),
                        "cooldown_until": float(getattr(risk_decision, "cooldown_until", 0.0)),
                        "reasons": dict(getattr(risk_decision, "reasons", {}) or {}),
                    }
                    setattr(w, "risk_by_sym", rr)
                    setattr(w, "risk_level", int(getattr(risk_decision, "level", 0)))
                    setattr(w, "risk_score", float(getattr(risk_decision, "composite", 0.0)))
                except Exception:
                    pass
        except Exception:
            pass
        sig = w.alpha.evaluate(sym, book)

        # Normalize non-standard action labels (ENTRY/EXIT/CLOSE) to canonical BUY/SELL/HOLD.
        try:
            _act0 = str(getattr(sig, "action", "") or "").strip().upper()
            if _act0 == "ENTRY":
                sig.action = "BUY"
            elif _act0 in ("EXIT", "CLOSE"):
                sig.action = "SELL"
        except Exception:
            pass

        # Sanity: make signal numerics finite to avoid NaN/inf corrupting sizing and comparisons.
        try:
            _sc = float(getattr(sig, "score", 0.0) or 0.0)
            _cf = float(getattr(sig, "confidence", 0.0) or 0.0)
            _bad_num = (not math.isfinite(_sc)) or (not math.isfinite(_cf))
            if not math.isfinite(_sc):
                _sc = 0.0
            if not math.isfinite(_cf):
                _cf = 0.0
            sig.score = float(clamp(_sc, -1.0, 1.0))
            sig.confidence = float(clamp(_cf, 0.0, 1.0))
            if _bad_num:
                try:
                    _a0 = str(getattr(sig, "action", "") or "").strip().upper()
                    if _a0 in ("BUY", "SELL"):
                        sig.action = "HOLD"
                        rs = str(getattr(sig, "reason", "") or "").strip()
                        if "NAN_GUARD" not in rs:
                            sig.reason = (rs or "EDGE") + "+NAN_GUARD"
                except Exception:
                    pass
        except Exception:
            pass

        w.last_event = f"{sym} mid={float(getattr(book, 'mid', 0.0) or 0.0):,.0f}"
        try:
            boot_ts = float(globals().get("_BOOT_TS", time.time()) or time.time())
        except Exception:
            boot_ts = float(time.time())
        try:
            up_sec = float(time.time() - boot_ts)
        except Exception:
            up_sec = 0.0
        try:
            warmup_sec = float(_env_float("BOT_WARMUP_SEC", 30.0) or 30.0)
        except Exception:
            warmup_sec = 30.0
        warmup_sec = float(max(1.0, warmup_sec))
        has_valid_candle = False
        try:
            px_hist = getattr(self, "_phoenix_px_hist", None)
            dq = px_hist.get(sym) if isinstance(px_hist, dict) else None
            if dq and len(dq) >= 1:
                try:
                    _ts0, _px0 = dq[-1]
                    _px0 = float(_px0)
                    if math.isfinite(_px0) and _px0 > 0.0:
                        has_valid_candle = True
                except Exception:
                    pass
        except Exception:
            pass
        if not has_valid_candle:
            try:
                _m0 = float(getattr(book, "mid", 0.0) or 0.0)
                if math.isfinite(_m0) and _m0 > 0.0:
                    has_valid_candle = True
            except Exception:
                pass
        fsm_state = "RUNNING" if (up_sec >= warmup_sec and has_valid_candle) else "WARMUP"
        try:
            setattr(w, "fsm_state", str(fsm_state))
            setattr(w, "fsm_up_sec", float(up_sec))
            setattr(w, "fsm_warmup_sec", float(warmup_sec))
        except Exception:
            pass
        try:
            if hasattr(self, "dzh"):
                self.dzh.observe_alpha(w, sig)
        except Exception:
            pass
        advanced_analysis = None
        if bool(getattr(self.cfg, "advanced_analytics_enabled", True)) and self.advanced_analytics is not None and book is not None:
            try:
                advanced_analysis = await self.advanced_analytics.analyze_symbol(sym, book)
                composite_score = float(advanced_analysis.get("composite_score", 0.0) or 0.0)
                signal_boost = float(advanced_analysis.get("signal_boost", 1.0) or 1.0)
                confidence_boost = float(advanced_analysis.get("confidence_boost", 1.0) or 1.0)
                original_score = float(sig.score)
                original_confidence = float(sig.confidence)
                if composite_score > 0.3 and float(sig.score) > 0.0:
                    sig.score = float(sig.score) * signal_boost
                    sig.confidence = float(sig.confidence) * confidence_boost
                elif composite_score < -0.3 and float(sig.score) < 0.0:
                    sig.score = float(sig.score) * signal_boost
                    sig.confidence = float(sig.confidence) * confidence_boost
                elif composite_score * float(sig.score) < -0.1:
                    sig.score = float(sig.score) * 0.5
                    sig.confidence = float(sig.confidence) * 0.7
                sig.score = float(clamp(float(sig.score), -1.0, 1.0))
                sig.confidence = float(clamp(float(sig.confidence), 0.0, 1.0))
                try:
                    buy_thr = float(getattr(w.cfg, "buy_threshold", 0.20) or 0.20)
                    sell_thr = float(getattr(w.cfg, "sell_threshold", 0.20) or 0.20)
                    act_u = str(getattr(sig, "action", "") or "").strip().upper()
                    sc = float(getattr(sig, "score", 0.0) or 0.0)
                    if act_u == "BUY" and sc < buy_thr:
                        sig.action = "HOLD"
                        rs = str(getattr(sig, "reason", "") or "").strip()
                        if "AA_HOLD" not in rs:
                            sig.reason = (rs or "EDGE") + "+AA_HOLD"
                    elif act_u in ("SELL", "EXIT", "CLOSE") and sc > -abs(float(sell_thr)):
                        sig.action = "HOLD"
                        rs = str(getattr(sig, "reason", "") or "").strip()
                        if "AA_HOLD" not in rs:
                            sig.reason = (rs or "EDGE") + "+AA_HOLD"
                except Exception:
                    pass
                if isinstance(sig.meta, dict):
                    layers = advanced_analysis.get("layers") or {}
                    sig.meta["advanced_analysis"] = {
                        "composite_score": composite_score,
                        "recommendation": advanced_analysis.get("recommendation"),
                        "layers": {
                            k: (v.get("score") if isinstance(v, dict) else (len(v) if isinstance(v, list) else v))
                            for k, v in (layers or {}).items()
                        },
                    }
                if abs(original_score - float(sig.score)) > 0.10:
                    self._log.info(
                        "AA adjusted %s: score %.3f->%.3f (boost %.2f) conf %.2f->%.2f (boost %.2f) comp=%.3f",
                        sym, original_score, float(sig.score), signal_boost,
                        original_confidence, float(sig.confidence), confidence_boost,
                        composite_score,
                    )
            except Exception as e:
                self._log.error("Advanced analytics failed for %s: %s", sym, e)
        try:
            c0 = float(getattr(self, "_cycle_best_conf", 0.0) or 0.0)
            c1 = float(getattr(sig, "confidence", 0.0) or 0.0)
            if c1 > c0:
                self._cycle_best_conf = float(c1)
        except Exception:
            pass
        try:
            pos = (getattr(w, "positions", None) or {}).get(sym)
        except Exception:
            pos = None
        try:
            has_pos = (pos is not None) and float(getattr(pos, "qty", 0.0) or 0.0) > 0.0
        except Exception:
            has_pos = bool(pos)
        _normalize_pos_local()
        try:
            _hb_mark(f"{'POS' if (pos is not None) else 'FLAT'}|{str(getattr(sig,'action',''))}|{str(getattr(sig,'reason',''))}")
        except Exception:
            pass
        spot = None
        spot_allowed = True
        try:
            dl = float(getattr(w, "_hb_deadline", 0.0) or 0.0)
            pr = set(getattr(w, "_hb_priority_syms", set()) or set())
            if dl and (dl - time.time()) < 1.35 and sym not in pr:
                spot_allowed = False
        except Exception:
            spot_allowed = True
        if spot_allowed and (bool(getattr(self.cfg, "phoenix_enabled", True)) or bool(getattr(self.cfg, "sanity_enabled", True))):
            try:
                spot = await self.feed.fetch_spot(sym)
                try:
                    rec_sp = (getattr(self.feed, '_spot_cache', {}) or {}).get(sym)
                    if rec_sp is not None and isinstance(rec_sp, (tuple, list)) and len(rec_sp) >= 2:
                        spot_ts = rec_sp[0]
                except Exception:
                    pass
                try:
                    if spot is not None and float(spot) <= 0.0:
                        spot = None
                except Exception:
                    pass
            except (TradingHalt, TemporaryPause):
                raise
            except Exception:
                spot = None
        pho = None
        if bool(getattr(self.cfg, "phoenix_enabled", True)):
            try:
                pho = self.phoenix.update(sym, sig, book, spot, depth_latency_ms=_depth_latency_ms, book_ts=book_ts, spot_ts=spot_ts)
            except Exception:
                pho = PhoenixDecision(
                    state="FLAT",
                    confidence=0.0,
                    composite=0.0,
                    rsi=50.0,
                    shadow_score=None,
                    shadow_label="ERR",
                    ready=False,
                    reason="PHOENIX_ERR",
                )
        else:
            pho = PhoenixDecision(
                state="FLAT",
                confidence=0.0,
                composite=0.0,
                rsi=50.0,
                shadow_score=None,
                shadow_label="OFF",
                ready=False,
                reason="PHOENIX_DISABLED",
            )
        try:
            w.phoenix_state = str(getattr(pho, "state", "FLAT"))
            w.phoenix_conf = float(getattr(pho, "confidence", 0.0) or 0.0)
            w.phoenix_rsi = getattr(pho, "rsi", None)
            w.phoenix_shadow = getattr(pho, "shadow_score", None)
            w.phoenix_composite = float(getattr(pho, "composite", 0.0) or 0.0)
        except Exception:
            pass
        try:
            if isinstance(getattr(sig, "meta", None), dict):
                sig.meta.update({
                    "phoenix_state": str(getattr(pho, "state", "FLAT")),
                    "phoenix_conf": float(getattr(pho, "confidence", 0.0) or 0.0),
                    "phoenix_score": float(getattr(pho, "composite", 0.0) or 0.0),
                    "phoenix_rsi": (float(getattr(pho, "rsi", 0.0)) if getattr(pho, "rsi", None) is not None else None),
                    "phoenix_shadow_score": (float(getattr(pho, "shadow_score", 0.0)) if getattr(pho, "shadow_score", None) is not None else None),
                    "phoenix_shadow_lbl": str(getattr(pho, "shadow_label", "")),
                    "phoenix_ready": bool(getattr(pho, "ready", False)),
                    "spot_last": (float(spot) if spot is not None else None),
                    "depth_latency_ms": (_depth_latency_ms if _depth_latency_ms is not None else None),
                })
        except Exception:
            pass
        try:
            if pos is None and bool(getattr(self.cfg, "phoenix_action_override", True)) and bool(getattr(self.cfg, "phoenix_enabled", True)):
                ph_state = str(getattr(pho, "state", "FLAT") or "FLAT").upper()
                ph_ready = bool(getattr(pho, "ready", False))
                ph_conf = float(getattr(pho, "confidence", 0.0) or 0.0)
                ph_comp = float(getattr(pho, "composite", 0.0) or 0.0)
                spot_ready = False
                try:
                    if book is not None:
                        src0 = str(getattr(book, "_source", "") or "").upper().strip()
                        spot_ready = (src0 == "SPOT_READY") and (not bool(getattr(book, "_stale", False)))
                except Exception:
                    spot_ready = False
                thr = float(getattr(self.cfg, "phoenix_entry_thr", 0.20) or 0.20)
                minc = float(getattr(self.cfg, "phoenix_min_conf", 0.20) or 0.20)
                rescue_mult = 1.0
                rescue_on = False
                rescue_tag = ""
                try:
                    thr, minc, rescue_mult, rescue_on, rescue_tag = _termux_adaptive_phoenix_gate(self.cfg)
                except Exception:
                    pass
                ph_conf = float(ph_conf) if math.isfinite(float(ph_conf)) else 0.0
                ph_comp = float(ph_comp) if math.isfinite(float(ph_comp)) else 0.0
                thr = float(thr) if math.isfinite(float(thr)) else 0.20
                minc = float(minc) if math.isfinite(float(minc)) else 0.20
                if ph_ready and (ph_state == "LONG") and (ph_comp >= abs(thr)) and (ph_conf >= abs(minc)):
                    base_act = str(getattr(sig, "action", "") or "").upper()
                    base_score = float(getattr(sig, "score", 0.0) or 0.0)
                    base_conf = float(getattr(sig, "confidence", 0.0) or 0.0)
                    base_reason_u = str(getattr(sig, "reason", "") or "").upper()
                    if (base_act not in ("SELL", "EXIT", "CLOSE", "SHORT")) and ("SPREAD" not in base_reason_u) and ("AA_HOLD" not in base_reason_u):
                        try:
                            if not math.isfinite(float(base_score)):
                                base_score = 0.0
                        except Exception:
                            base_score = 0.0
                        buy_thr0 = 0.20
                        try:
                            buy_thr0 = abs(float(getattr(w.cfg, "buy_threshold", 0.20) or 0.20))
                            if not math.isfinite(float(buy_thr0)):
                                buy_thr0 = 0.20
                        except Exception:
                            buy_thr0 = 0.20
                        if spot_ready or (base_act == "BUY"):
                            try:
                                sig.action = "BUY"
                                if spot_ready and base_act != "BUY":
                                    sig.score = float(max(ph_comp, buy_thr0))
                                else:
                                    sig.score = float(max(base_score, ph_comp))
                                sig.confidence = float(max(float(getattr(sig, "confidence", 0.0) or 0.0), ph_conf))
                                sig.score = float(clamp(float(sig.score), -1.0, 1.0))
                                sig.confidence = float(clamp(float(sig.confidence), 0.0, 1.0))
                                try:
                                    if rescue_on and float(rescue_mult) < 1.0:
                                        prev = float(getattr(sig, "dzh_entry_mult", 1.0) or 1.0)
                                        newm = float(min(prev, float(rescue_mult)))
                                        setattr(sig, "dzh_entry_mult", float(newm))
                                        setattr(sig, "dzh_reason", f"TERMUX_{(rescue_tag or 'RESCUE')[:48]}")
                                except Exception:
                                    pass

                                try:
                                    if base_act != "BUY":
                                        wm0 = float(getattr(self.cfg, "phoenix_warmup_size_mult", 0.65) or 0.65)
                                        if float(wm0) < 1.0:
                                            prev = float(getattr(sig, "dzh_entry_mult", 1.0) or 1.0)
                                            setattr(sig, "dzh_entry_mult", float(min(prev, float(clamp(wm0, 0.05, 1.0)))))
                                            if not str(getattr(sig, "dzh_reason", "") or "").strip():
                                                setattr(sig, "dzh_reason", "PHX_OVERRIDE_SIZE")
                                except Exception:
                                    pass
                                sig.reason = f"{str(getattr(sig,'reason','') or '').strip() or 'EDGE'}+PHX"
                                if isinstance(getattr(sig, "meta", None), dict):
                                    sig.meta["phoenix_action_override"] = True
                            except Exception:
                                pass
        except Exception:
            pass
        try:
            _flow_dp = None
            try:
                _fd = getattr(self, "_phoenix_flow_dp_pct", None)
                if isinstance(_fd, dict):
                    _k = None
                    try:
                        _k = _canon_symbol(sym)
                    except Exception:
                        _k = None
                    if _k in _fd:
                        _flow_dp = float(_fd.get(_k))
                    elif sym in _fd:
                        _flow_dp = float(_fd.get(sym))
            except Exception:
                _flow_dp = None
            _dash_param_update(
                self,
                wallet=str(getattr(w, "name", "") or getattr(w, "id", "") or ""),
                sym=str(sym or ""),
                fields={
                    "sig_action": str(getattr(sig, "action", "") or ""),
                    "sig_reason": str(getattr(sig, "reason", "") or ""),
                    "sig_score": float(getattr(sig, "score", 0.0) or 0.0),
                    "sig_conf": float(getattr(sig, "confidence", 0.0) or 0.0),
                    "ph_state": str(getattr(pho, "state", "") or ""),
                    "ph_ready": bool(getattr(pho, "ready", False)),
                    "ph_reason": str(getattr(pho, "reason", "") or ""),
                    "ph_conf": float(getattr(pho, "confidence", 0.0) or 0.0),
                    "ph_comp": float(getattr(pho, "composite", 0.0) or 0.0),
                    "ph_rsi": (float(getattr(pho, "rsi", 0.0) or 0.0) if getattr(pho, "rsi", None) is not None else None),
                    "ph_shadow": (float(getattr(pho, "shadow_score", 0.0) or 0.0) if getattr(pho, "shadow_score", None) is not None else None),
                    "mid": float(getattr(book, "mid", 0.0) or 0.0),
                    "spr_bps": float(getattr(book, "spread_bps", 0.0) or 0.0),
                    "flow_dp": _flow_dp,
                    "snap_state": str(snap_state or ""),
                    "snap_conf": float(snap_conf or 0.0),
                    "risk_level": (int(getattr(risk_decision, "level", 0) or 0) if risk_decision is not None else 0),
                    "risk_score": (float(getattr(risk_decision, "composite", 0.0) or 0.0) if risk_decision is not None else 0.0),
                    "size_mult": (float(getattr(risk_decision, "size_mult", 1.0) or 1.0) if risk_decision is not None else 1.0),
                },
            )
        except Exception:
            pass
        block_entries = False
        sanity_reason = ""
        try:
            block_entries, sanity_reason = self.sanity.evaluate(w, sym, book, spot, _depth_latency_ms, pho)
        except Exception:
            block_entries, sanity_reason = False, ""
        if block_entries and pos is None:
            w.last_event = f"SANITY_BLOCK {sym}"
            _set_engine("Hold", f"SANITY:{sanity_reason or 'BLOCK'}", reject=True, meta={"sym": sym, "reason": sanity_reason})
            return
        if pos is None:
            try:
                if bool(getattr(book, "_stale", False)):
                    try:
                        w.last_event = f"STALE_BOOK {sym}"
                    except Exception:
                        pass
                    await _rej(
                        "STALE_BOOK",
                        sym=sym,
                        source=str(getattr(book, "_source", "") or ""),
                        age_sec=float(getattr(book, "age_sec", 0.0) or 0.0),
                    )
                    return
            except Exception:
                pass
        try:
            if bool(getattr(w, "sanity_halt", False)):
                if pos is not None:
                    try:
                        if hasattr(self, "dzh"):
                            await self.dzh.maybe_ai_rescue(self, w, sym, book)
                    except Exception:
                        pass
                w.last_event = f"SANITY_HALT {sym}"
                _set_engine("Hold", f"SANITY_HALT:{str(getattr(w,'sanity_reason','') or '').strip() or 'ON'}", reject=True, meta={"sym": sym})
                if not has_pos:
                    return
        except Exception:
            pass
        # Fail-closed (NOBOOK): if an entry BUY leaks through without any orderbook, reject before any sizing.
        if pos is None and str(getattr(sig, "action", "") or "").strip().upper() == "BUY" and book is None:
            await _rej("NOBOOK", sym=sym)
            return

        if pos is None and str(getattr(sig, "action", "") or "").strip().upper() == "BUY" and bool(getattr(self.cfg, "phoenix_enabled", True)):
            gate_mode = str(getattr(self.cfg, "phoenix_gate_mode", "soft") or "soft").strip().lower()
            try:
                if bool(book_fallback):
                    gate_mode = "hard"
            except Exception:
                pass
            # In SPOT_READY mode (no real depth), Phoenix must be the authoritative entry gate.
            try:
                src0 = str(getattr(book, "_source", "") or "").upper().strip() if book is not None else ""
                if src0 == "SPOT_READY":
                    gate_mode = "hard"
            except Exception:
                pass
            thr = float(getattr(self.cfg, "phoenix_entry_thr", 0.20) or 0.20)
            min_conf = float(getattr(self.cfg, "phoenix_min_conf", 0.20) or 0.20)
            try:
                _thr_tmp, _minc_tmp, _sm_tmp, _resc_on, _tag_tmp = _termux_adaptive_phoenix_gate(self.cfg)
                thr = float(_thr_tmp)
                min_conf = float(_minc_tmp)
                try:
                    if bool(_resc_on) and float(_sm_tmp) < 1.0:
                        prev = float(getattr(sig, "dzh_entry_mult", 1.0) or 1.0)
                        setattr(sig, "dzh_entry_mult", float(min(prev, float(_sm_tmp))))
                        if _tag_tmp:
                            setattr(sig, "dzh_reason", f"TERMUX_{str(_tag_tmp)[:48]}")
                except Exception:
                    pass
            except Exception:
                pass
            thr = float(thr) if math.isfinite(float(thr)) else 0.20
            min_conf = float(min_conf) if math.isfinite(float(min_conf)) else 0.20
            fb_conf = float(getattr(self.cfg, "phoenix_fallback_raz_conf", 0.60) or 0.60)
            fb_score = float(getattr(self.cfg, "phoenix_fallback_raz_score", 0.22) or 0.22)
            fb_conf = float(fb_conf) if math.isfinite(float(fb_conf)) else 0.60
            fb_score = float(fb_score) if math.isfinite(float(fb_score)) else 0.22
            ready = bool(getattr(pho, "ready", False))
            st0 = str(getattr(pho, "state", "FLAT") or "FLAT").upper()
            pconf = float(getattr(pho, "confidence", 0.0) or 0.0)
            pcomp = float(getattr(pho, "composite", 0.0) or 0.0)
            pconf = float(pconf) if math.isfinite(float(pconf)) else 0.0
            pcomp = float(pcomp) if math.isfinite(float(pcomp)) else 0.0
            block = False
            if gate_mode in ("hard", "strict", "1", "true", "on"):
                block = (not ready) or (st0 != "LONG") or (pconf < abs(min_conf)) or (pcomp < abs(thr))
            elif gate_mode in ("soft", "adaptive"):
                raz_conf = float(getattr(sig, "confidence", 0.0) or 0.0)
                raz_score = float(getattr(sig, "score", 0.0) or 0.0)
                raz_conf = float(raz_conf) if math.isfinite(float(raz_conf)) else 0.0
                raz_score = float(raz_score) if math.isfinite(float(raz_score)) else 0.0
                # Soft/adaptive gate: allow RAZ-only entries only during Phoenix warmup (ready=False).
                # Once Phoenix is READY, it must not contradict the entry direction (no conflicting signals).
                if ready and (st0 == "SHORT"):
                    block = True
                if not ready:
                    if (raz_conf < fb_conf) or (raz_score < fb_score):
                        block = True
                elif (st0 != "LONG"):
                    block = True
                elif (pconf < abs(min_conf)) or (pcomp < abs(thr)):
                    if (raz_conf < fb_conf) or (raz_score < fb_score):
                        block = True
            else:
                block = False
            if (pos is None) and block:
                w.last_event = f"PHOENIX_BLOCK {sym}"
                _set_engine("Hold", f"PHX:st={st0},ready={int(ready)},conf={pconf:.2f},comp={pcomp:.2f}", reject=True, meta={"sym": sym})
                return
        if pos is None:
            try:
                if str(snap_state or "").upper() == "CRITICAL":
                    w.last_event = f"{sym} SNAP_CRITICAL conf={float(snap_conf or 0.0):.0f}"
                    _set_engine("Hold", f"MKT:CRITICAL({int(float(snap_conf or 0.0))}%)", reject=True, meta={"sym": sym, "snap_conf": float(snap_conf or 0.0), "entry_attempt": (not has_pos), "stage": "ENTRY"})
                    _hb_mark(f"FLAT|CRITICAL|{int(float(snap_conf or 0.0))}")
                    return
            except Exception:
                pass
            try:
                if str(getattr(sig, "action", "") or "").strip().upper() != "BUY":
                    rsn = str(getattr(sig, "reason", "") or "").upper()
                    if ("LOW_SC" in rsn) or rsn in ("LOWSC", "LOW_SCORE"):
                        try:
                            _obs_trace(w, "SCAN", symbol=sym, reason="LOW_SC", meta={"score": float(getattr(sig, "score", 0.0) or 0.0)})
                        except Exception:
                            pass
                        _set_engine("Run", "SCAN_LOW_SC", reject=False)
                        try:
                            _record_why_no_trade(
                                self,
                                wallet=str(getattr(w, "name", "") or getattr(w, "id", "") or ""),
                                sym=str(sym or ""),
                                status="ENTRY_SKIP",
                                reason="LOW_SC",
                                meta={
                                    "entry_attempt": (not has_pos),
                                    "stage": "SIGNAL",
                                    "score": float(getattr(sig, "score", 0.0) or 0.0),
                                    "sig_action": str(getattr(sig, "action", "") or ""),
                                    "sig_reason": str(getattr(sig, "reason", "") or ""),
                                },
                            )
                        except Exception:
                            pass
                        _hb_mark(f"FLAT|{str(getattr(sig,'action',''))}|{str(getattr(sig,'reason',''))}")
                        return
            except Exception:
                pass
            if str(getattr(sig, "action", "") or "").strip().upper() != "BUY":
                if self.recorder:
                    equity = self._estimate_equity_irt(cash_irt, w.positions, current_sym=sym, current_mid=book.mid)
                    await self._low_priority_call(
                        self.recorder.record_tick,
                        time.time(), w.name, sym, book.bid, book.ask, book.mid, book.spread_bps, sig.score,
                        equity=equity, quote_free=cash_irt, asset_free=None
                    )
                _set_engine('Run', f"SIG:{str(getattr(sig,'action','') or '').upper() or 'HOLD'}", reject=False)
                try:
                    _actu = str(getattr(sig, "action", "") or "").upper().strip() or "HOLD"
                except Exception:
                    _actu = "HOLD"
                _why_sig = f"NO_SIGNAL:{_actu}"
                try:
                    if bool(getattr(self.cfg, "phoenix_enabled", True)):
                        _pr = bool(getattr(pho, "ready", False))
                        _ps = str(getattr(pho, "state", "FLAT") or "FLAT").upper()
                        _pc = float(getattr(pho, "confidence", 0.0) or 0.0)
                        _minc = float(getattr(self.cfg, "phoenix_min_conf", 0.20) or 0.20)
                        if not _pr:
                            _why_sig = "WARMUP:PHX_NOT_READY"
                        elif _ps != "LONG" and (_actu in ("HOLD", "FLAT")):
                            _why_sig = f"PHX_STATE:{_ps}"
                        elif _ps == "LONG" and _pc < abs(_minc):
                            _why_sig = "LOW_CONF"
                except Exception:
                    pass
                try:
                    _record_why_no_trade(
                        self,
                        wallet=str(getattr(w, "name", "") or getattr(w, "id", "") or ""),
                        sym=str(sym or ""),
                        status="ENTRY_SKIP",
                        reason=str(_why_sig),
                        meta={
                            "entry_attempt": (not has_pos),
                            "stage": "SIGNAL",
                            "score": float(getattr(sig, "score", 0.0) or 0.0),
                            "conf": float(getattr(sig, "confidence", 0.0) or 0.0),
                            "phoenix_ready": bool(getattr(pho, "ready", False)),
                            "phoenix_state": str(getattr(pho, "state", "") or ""),
                            "phoenix_conf": float(getattr(pho, "confidence", 0.0) or 0.0),
                            "phoenix_score": float(getattr(pho, "composite", 0.0) or 0.0),
                            "phoenix_reason": str(getattr(pho, "reason", "") or ""),
                            "phoenix_rsi": (float(getattr(pho, "rsi", 0.0) or 0.0) if getattr(pho, "rsi", None) is not None else None),
                            "phoenix_shadow": (float(getattr(pho, "shadow_score", 0.0) or 0.0) if getattr(pho, "shadow_score", None) is not None else None),
                            "sig_action": str(getattr(sig, "action", "") or ""),
                            "sig_reason": str(getattr(sig, "reason", "") or ""),
                        },
                    )
                except Exception:
                    pass
                _hb_mark(f"FLAT|{str(getattr(sig,'action',''))}|{str(getattr(sig,'reason',''))}")
                return
            try:
                _fs = str(fsm_state or "").upper().strip()
            except Exception:
                _fs = ""
            if _fs and _fs != "RUNNING":
                _set_engine(
                    "WARMUP",
                    "FSM_STATE_LOCK",
                    reject=True,
                    meta={
                        "sym": sym,
                        "fsm_state": _fs,
                        "up_sec": float(up_sec),
                        "warmup_sec": float(warmup_sec),
                        "entry_attempt": True,
                        "stage": "FSM",
                    },
                )
                return
            if bool(locals().get("usdt_px_wait", False)):
                _set_engine(
                    "Hold",
                    "NO_DATA:USDT_PX",
                    reject=True,
                    meta={"sym": sym, "entry_attempt": True, "stage": "DATA"},
                )
                return
            open_n = 0
            try:
                for _ps, _p in (getattr(w, "positions", None) or {}).items():
                    try:
                        if _p is None:
                            continue
                        if float(getattr(_p, "qty", 0.0) or 0.0) > 0.0:
                            open_n += 1
                    except Exception:
                        continue
            except Exception:
                try:
                    open_n = len(getattr(w, "positions", None) or {})
                except Exception:
                    open_n = 0
            pend_n = 0
            try:
                pend = self.orders.pending() if hasattr(self, "orders") else {}
                if isinstance(pend, dict) and pend:
                    wallet_name = str(getattr(w, "name", "") or getattr(w, "id", "") or getattr(w, "wallet", "") or "")
                    pend_syms = set()
                    for _cid0, _rec0 in pend.items():
                        if not isinstance(_rec0, dict):
                            continue
                        if str(_rec0.get("wallet") or "") != wallet_name:
                            continue
                        if str(_rec0.get("side") or "").lower().strip() != "buy":
                            continue
                        psym = _canon_symbol(_rec0.get("symbol") or "")
                        if psym:
                            pend_syms.add(psym)
                    if sym in pend_syms:
                        try:
                            _p0 = (getattr(w, "positions", None) or {}).get(sym)
                            if _p0 is None or float(getattr(_p0, "qty", 0.0) or 0.0) <= 0.0:
                                await _rej("LOCKED:PENDING_BUY", sym=sym)
                                return
                        except Exception:
                            await _rej("LOCKED:PENDING_BUY", sym=sym)
                            return
                    for psym in pend_syms:
                        try:
                            _p0 = (getattr(w, "positions", None) or {}).get(psym)
                            if _p0 is not None and float(getattr(_p0, "qty", 0.0) or 0.0) > 0.0:
                                continue
                        except Exception:
                            pass
                        pend_n += 1
            except Exception:
                pend_n = 0
            open_eff = int(open_n) + int(pend_n)
            mx_pos = int(getattr(w.cfg, "max_open_positions", 0) or 0)
            if mx_pos > 0 and open_eff >= mx_pos:
                await _rej('MAX_POS', sym=sym, max=int(getattr(w.cfg,'max_open_positions',0) or 0), open=int(open_n), pending=int(pend_n), open_eff=int(open_eff))
                return
            try:
                if risk_decision is not None and int(getattr(risk_decision, "level", 0)) >= 4:
                    w.last_event = f"RISK_L{int(getattr(risk_decision,'level',4))}_NO_ENTRY {sym}"
                    await _rej("DATA_RISK_NO_ENTRY", sym=sym,
                         level=int(getattr(risk_decision, "level", 0)),
                         score=float(getattr(risk_decision, "composite", 0.0)))
                    return
            except Exception:
                pass
            try:
                if risk_decision is not None:
                    cd_u = float(getattr(risk_decision, "cooldown_until", 0.0) or 0.0)
                    if cd_u and time.time() < cd_u:
                        w.last_event = f"RISK_COOLDOWN {sym}"
                        await _rej(
                            "RISK_COOLDOWN",
                            sym=sym,
                            until=float(cd_u),
                            level=int(getattr(risk_decision, "level", 0) or 0),
                            score=float(getattr(risk_decision, "composite", 0.0) or 0.0),
                        )
                        return
            except Exception:
                pass
            try:
                if hasattr(self, "dzh"):
                    self.dzh.tune_wallet(w)
            except Exception:
                pass
            mids = None
            try:
                st = getattr(self.phoenix, "_st", {}) or {}
                sym_st = st.get(sym)
                mids = list(getattr(sym_st, "mids", []) or []) if sym_st is not None else None
            except Exception:
                mids = None
            top8_row = None
            try:
                for r in (self.get_top8_snapshot() or []):
                    if _canon_symbol(str(r.get("symbol") or "")) == sym:
                        top8_row = r
                        break
            except Exception:
                top8_row = None
            allowed, why2 = True, "OK"
            try:
                if hasattr(self, "dzh"):
                    allowed, why2 = self.dzh.evaluate_entry(w, sym, book, sig, pho, top8_row, mids=mids)
            except Exception:
                allowed, why2 = False, "DZH_ERR"
            if not allowed:
                w.last_event = f"DZH_VETO {sym} {why2}"
                _set_engine("Hold", f"DZH:{str(why2 or '').strip() or 'VETO'}", reject=True, meta={"sym": sym})
                return
            base_cap = cash_irt * float(getattr(w, "dyn_max_notional_frac", 0.0) or w.cfg.max_notional_frac)
            base_cap = float(_env_float("BASE_CAP_IRT", base_cap))
            notional = self.risk.size_notional(cash_irt, base_cap, sig.confidence)
            try:
                if risk_decision is not None:
                    sm = float(getattr(risk_decision, "size_mult", 1.0) or 1.0)
                    sm = float(clamp(sm, 0.0, 1.5))
                    if sm != 1.0:
                        notional *= sm
                        try:
                            setattr(w, "risk_size_mult", float(sm))
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                notional *= float(clamp(float(health_size_mult), 0.0, 1.0))
            except Exception:
                pass
            try:
                notional *= float(clamp(float(snap_size_mult), 0.0, 1.0))
            except Exception:
                pass
            try:
                if getattr(self, "_ai_trader", None) is not None and bool(getattr(w.cfg, "autonomous_ai", False)) and bool(_env_bool("OPENAI_TRADE_ENABLE", False)) and bool(_env_bool("OPENAI_TRADE_ALLOW_ND", False)):
                    ai = getattr(self, "_ai_trader", None)
                    if ai is not None and bool(getattr(ai, "enabled", lambda: False)()):
                        payload = {
                            "sym": str(sym),
                            "wallet": str(getattr(w, "name", "")),
                            "sig": str(getattr(sig, "action", "") or getattr(sig, "side", "") or ""),
                            "sig_conf": float(getattr(sig, "confidence", 0.0) or 0.0),
                            "px_mid": float(getattr(book, "mid", 0.0) or 0.0),
                            "px_bid": float(getattr(book, "bid", 0.0) or 0.0),
                            "px_ask": float(getattr(book, "ask", 0.0) or 0.0),
                            "phoenix": {
                                "state": str(getattr(pho, "state", "") or ""),
                                "rsi": float(getattr(pho, "rsi", 0.0) or 0.0),
                                "shadow": float(getattr(pho, "shadow_score", 0.0) or 0.0),
                                "conf": float(getattr(pho, "confidence", 0.0) or 0.0),
                            },
                            "budget_irt": float(cash_irt),
                            "base_notional_irt": float(notional),
                        }
                        rec = await ai.recommend(payload)
                        if isinstance(rec, dict):
                            try:
                                c = float(rec.get("confidence") or 0.0)
                            except Exception:
                                c = 0.0
                            rf = str(rec.get("risk_flag") or "OK").upper()
                            try:
                                sm = float(rec.get("size_modifier") or 1.0)
                            except Exception:
                                sm = 1.0
                            sm = float(clamp(sm, 0.0, 2.0))
                            if c >= 70.0 and rf != "CRITICAL":
                                try:
                                    w.last_reject_meta = dict(getattr(w, "last_reject_meta", {}) or {})
                                    w.last_reject_meta["ai"] = {"confidence": c, "risk_flag": rf, "size_modifier": sm, "applied": False, "reason": str(rec.get("reason") or "")[:120]}
                                except Exception:
                                    pass
            except Exception:
                pass
            try:
                if bool(getattr(self.cfg, "phoenix_enabled", True)):
                    gm = str(getattr(self.cfg, "phoenix_gate_mode", "soft") or "soft").strip().lower()
                    if gm in ("soft", "adaptive") and (not bool(getattr(pho, "ready", False))):
                        wm = float(getattr(self.cfg, "phoenix_warmup_size_mult", 0.65) or 0.65)
                        notional *= float(clamp(wm, 0.05, 1.0))
            except Exception:
                pass
            try:
                dzh_mult = float(getattr(sig, "dzh_entry_mult", 1.0) or 1.0)
            except Exception:
                dzh_mult = 1.0
            if float(dzh_mult) < 1.0:
                try:
                    before = float(notional)
                    notional *= float(clamp(float(dzh_mult), 0.05, 1.0))
                    try:
                        setattr(w, "dzh_size_mult", float(dzh_mult))
                        setattr(w, "dzh_last_reason", str(getattr(sig, "dzh_reason", "") or "DZH_SOFT"))
                    except Exception:
                        pass
                    try:
                        self._log.info(
                            "event=DZH_SOFT_SIZE wallet=%s sym=%s mult=%.2f notional_before=%.0f notional_after=%.0f why=%s",
                            w.name, sym, float(dzh_mult), float(before), float(notional), str(getattr(sig, "dzh_reason", "") or "")
                        )
                    except Exception:
                        pass
                except Exception:
                    pass
            mult = 1.0
            ci_meta = {}
            try:
                mult, ci_meta = w.cortex.entry_multiplier(sym, sig, book, depth_data=None)
            except Exception:
                mult, ci_meta = 1.0, {}
            if isinstance(ci_meta, dict) and ci_meta.get("veto"):
                self._log.warning(
                    "event=PARISA_VETO wallet=%s sym=%s raz_conf=%.2f parisa_delta=%.3f veto_thr=%.3f",
                    w.name,
                    sym,
                    float(getattr(sig, "confidence", 0.0) or 0.0),
                    float(ci_meta.get("parisa_delta", 0.0) or 0.0),
                    float(ci_meta.get("parisa_veto_thr", -0.35) or -0.35),
                )
                _set_engine('Hold', 'PARISA_VETO', reject=True, meta={'sym': sym, **(ci_meta or {})})
                return
            if float(mult) > 1.0:
                before = float(notional)
                notional = float(notional) * float(mult)
                hard_cap = float(cash_irt) * float(w.cfg.collective_max_notional_frac)
                if notional > hard_cap:
                    notional = float(hard_cap)
                self._log.info(
                    "event=COLLECTIVE_BOOST wallet=%s sym=%s raz_conf=%.2f parisa_delta=%.3f mult=%.2f notional_before=%.0f notional_after=%.0f",
                    w.name, sym, float(sig.confidence), float(ci_meta.get("parisa_delta", 0.0) or 0.0), float(mult), float(before), float(notional)
                )
            risk_level = "OFF"
            try:
                risk_level = self.risk.safe_level() if hasattr(self.risk, "safe_level") else ("SOFT" if bool(self.risk.safe_mode) else "OFF")
            except Exception:
                risk_level = "SOFT" if bool(getattr(self.risk, "safe_mode", False)) else "OFF"
            net_safe = False
            net_sym_safe = False
            net_reason = ""
            try:
                net_safe = bool(self.net.is_safe_mode()) if hasattr(self.net, "is_safe_mode") else False
                if not net_safe:
                    if hasattr(self.net, "should_block_symbol") and callable(getattr(self.net, "should_block_symbol")):
                        net_sym_safe = bool(self.net.should_block_symbol(sym))
                    elif hasattr(self.net, "symbol_pause_remaining") and callable(getattr(self.net, "symbol_pause_remaining")):
                        net_sym_safe = float(self.net.symbol_pause_remaining(sym) or 0.0) > 0.0
                net_reason = str(self.net.safe_reason() if hasattr(self.net, "safe_reason") else "")
            except Exception:
                net_safe = False
                net_sym_safe = False
                net_reason = ""
            if net_safe:
                w.last_event = f"NET_SAFE {net_reason or 'GLOBAL'}"
                _set_engine('Hold', f"NET_SAFE:{(net_reason or 'GLOBAL')[:60]}", reject=True, meta={'sym': sym, 'net_reason': net_reason, 'scope': 'GLOBAL'})
                return
            if net_sym_safe:
                w.last_event = f"NET_SAFE {net_reason or sym}"
                _set_engine('Hold', f"NET_SAFE:{(net_reason or sym)[:60]}", reject=True, meta={'sym': sym, 'net_reason': net_reason})
                return
            try:
                pol = getattr(self, "trade_policy", None)
                _hs = str(getattr(self, "_hw_state", "") or "")
                allow = True
                why = ""
                try:
                    if pol is not None and hasattr(pol, "allow"):
                        allow, why = pol.allow("ENTRY")
                except Exception:
                    allow, why = True, ""
                try:
                    _record_why_no_trade(
                        self,
                        wallet=str(getattr(w, 'name', '') or getattr(w, 'id', '') or ''),
                        sym=str(sym or ''),
                        status=("ENTRY_ALLOW" if bool(allow) else "ENTRY_DENY"),
                        reason=str(why or ''),
                        meta={
                            'policy': str(why or ''),
                            'entry_attempt': True,
                            'allow': bool(allow),
                            'health_state': str(_hs or ''),
                            'health_score': getattr(self, "_hw_score", None),
                        },
                    )
                except Exception:
                    pass
                if not bool(allow):
                    try:
                        w.last_event = f"HEALTH_BLOCK_ENTRY:{_hs}"
                    except Exception:
                        pass
                    try:
                        deny_reason = str(why or "").strip()
                    except Exception:
                        deny_reason = ""
                    if not deny_reason:
                        try:
                            deny_reason = f"HEALTH_STATE:{_hs}"
                        except Exception:
                            deny_reason = "HEALTH_DENY"
                    _set_engine(
                        "Hold",
                        str(deny_reason),
                        reject=True,
                        meta={'sym': sym, 'health_state': _hs, 'health_score': getattr(self, "_hw_score", None), 'policy': why, 'deny_reason': deny_reason},
                    )
                    return
            except Exception:
                pass
                pass
            if (risk_level == "SOFT" and bool(getattr(self.risk, "safe_mode", False))):
                soft_mult = float(_env_float("SOFT_SAFE_ENTRY_MULT", 0.25))
                soft_frac = float(_env_float("SOFT_SAFE_MAX_NOTIONAL_FRAC", 0.03))
                soft_mult = clamp(soft_mult, 0.0, 1.0)
                soft_frac = clamp(soft_frac, 0.0, 1.0)
                cap = float(cash_irt) * float(soft_frac)
                before_n = float(notional)
                notional = min(float(notional) * float(soft_mult), cap)
                if notional < float(self.cfg.min_notional_irt):
                    w.last_event = f"SAFE:NOTIONAL_SMALL {sym}"
                    _set_engine('Hold', 'SAFE:NOTIONAL_SMALL', reject=True, meta={'sym': sym, 'notional': float(notional), 'entry_attempt': (not has_pos), 'stage': 'ENTRY'})
                    return
                self._log.warning(
                    "event=SOFT_SAFE_ENTRY wallet=%s sym=%s risk=%s net_safe=%s notional_before=%.0f notional_after=%.0f cap=%.0f",
                    w.name, sym, str(risk_level), bool(net_safe), float(before_n), float(notional), float(cap),
                )
            ok_open, why, meta = self.risk.can_open_explain(
                sym,
                notional,
                cash_irt,
                max_notional_frac=float(getattr(w, "dyn_max_notional_frac", 0.0) or w.cfg.max_notional_frac),
            )
            try:
                self.logger.info(
                    "event=RISK_OPEN_DECISION wallet=%s sym=%s ok_open=%s why=%s confidence=%s",
                    getattr(w, "name", None),
                    sym,
                    ok_open if "ok_open" in locals() else None,
                    why if "why" in locals() else None,
                    getattr(sig, "confidence", None),
                )
            except Exception:
                pass
            if not ok_open:
                try:
                    wu0 = str(why or '').upper()
                except Exception:
                    wu0 = ''
                mapped_why = str(why or '').strip() or 'RISK_DENY'
                if 'MIN_NOTIONAL' in wu0 or 'NOTIONAL_SMALL' in wu0 or ('NOTIONAL' in wu0 and 'MIN' in wu0):
                    mapped_why = 'RISK_MIN_NOTIONAL'
                elif 'COOLDOWN' in wu0 or ('LOCK' in wu0 and 'FSM' not in wu0):
                    mapped_why = 'RISK_COOLDOWN_LOCK'
                elif wu0.startswith('RISK_'):
                    mapped_why = str(wu0)
                else:
                    try:
                        mapped_why = 'RISK:' + str(why or '').strip()
                    except Exception:
                        mapped_why = 'RISK_DENY'
                _obs_reject(w, mapped_why, symbol=sym, meta=meta)
                try:
                    wu = str(why or "").upper()
                except Exception:
                    wu = ""
                if ("LOCK" in wu) or ("OPEN_ORD" in wu) or ("OPEN_ORDER" in wu):
                    try:
                        if not float(getattr(w, "_locked_since_ts", 0.0) or 0.0):
                            setattr(w, "_locked_since_ts", float(time.time()))
                    except Exception:
                        pass
                    _set_engine('LOCKED', str(mapped_why or ''), reject=True, meta=meta)
                    return
                soft = False
                for _k in ("SCORE", "LOW_SC", "SPREAD", "VOL", "LIQ", "TREND", "DYN", "CAP", "NOTIONAL", "PROFIT", "WAIT", "MAX_POS"):
                    if _k in wu:
                        soft = True
                        break
                if soft:
                    try:
                        sec = float(getattr(self.cfg, "entry_throttle_sec", 2.0) or 2.0)
                    except Exception:
                        sec = 2.0
                    now0 = time.time()
                    try:
                        until0 = float(getattr(w, "_entry_throttle_until", 0.0) or 0.0)
                    except Exception:
                        until0 = 0.0
                    try:
                        setattr(w, "_entry_throttle_until", float(max(until0, now0 + max(0.2, sec))))
                    except Exception:
                        pass
                    _set_engine('Run', str(why or ''), reject=True, meta=meta)
                    return
                _set_engine('Hold', str(why or ''), reject=False, meta=meta)
                return
            if w.cfg.min_net_profit_irt > 0:
                netp = self._expected_net_profit_irt(notional, target_move_bps=35.0, cfg=w.cfg)
                if netp < w.cfg.min_net_profit_irt:
                    w.last_event = f"SKIP:PROFIT<{w.cfg.min_net_profit_irt:.0f}"
                    try:
                        sec = float(getattr(self.cfg, "entry_throttle_sec", 2.0) or 2.0)
                    except Exception:
                        sec = 2.0
                    now0 = time.time()
                    try:
                        until0 = float(getattr(w, "_entry_throttle_until", 0.0) or 0.0)
                    except Exception:
                        until0 = 0.0
                    try:
                        setattr(w, "_entry_throttle_until", float(max(until0, now0 + max(0.2, sec))))
                    except Exception:
                        pass
                    _set_engine('Run', f"PROFIT_LOW<{w.cfg.min_net_profit_irt:.0f}", reject=True, meta={'sym': sym, 'netp': float(netp), 'entry_attempt': (not has_pos), 'stage': 'ENTRY'})
                    return
            spend = _fee_aware_spend(cash_irt, notional, w.cfg.fee_bps, w.cfg.slippage_bps, w.cfg.order_safety_bps)
            # Ensure exchange min notional is respected after fee-aware spend shrink.
            # Otherwise the engine may repeatedly attempt orders that the exchange rejects.
            try:
                _min_n = float(getattr(self.cfg, "min_notional_irt", 0.0) or 0.0)
            except Exception:
                _min_n = 0.0
            if _min_n > 0.0 and float(spend) > 0.0 and float(spend) < float(_min_n):
                try:
                    w.last_event = f"RISK_MIN_NOTIONAL {sym}"
                except Exception:
                    pass
                _throttle_entry("RISK_MIN_NOTIONAL", sym=sym, notional=float(notional), spend=float(spend), min_notional=float(_min_n))
                return
            if (not math.isfinite(float(spend))) or spend <= 0:
                try:
                    w.last_event = f"SPEND_ZERO {sym}"
                except Exception:
                    pass
                _set_engine(
                    "Run",
                    "SPEND_ZERO",
                    reject=True,
                    meta={"sym": sym, "entry_attempt": (not has_pos), "stage": "ENTRY", "notional": float(notional or 0.0), "cash_irt": float(cash_irt or 0.0)},
                )
                return
            # Fail-closed: never allow ENTRY when book is truly missing (NOBOOK).
            # This guards against any accidental entry-path leakage when depth+spot are unavailable.
            if book is None:
                await _rej("NOBOOK", sym=sym)
                return

            qty = (spend * quote_mult) / book.ask if book.ask > 0 else 0.0
            if (not math.isfinite(float(qty))) or qty <= 0:
                await _rej("NOBOOK", sym=sym, ask=float(getattr(book, "ask", 0.0) or 0.0))
                return
            if getattr(self.risk, "hard_blocks_all_orders", lambda *a, **k: False)(side="buy", reduce_only=False):
                if self.recorder:
                    equity = self._estimate_equity_irt(cash_irt, w.positions, current_sym=sym, current_mid=book.mid)
                    await self._low_priority_call(
                        self.recorder.record_tick,
                        time.time(), w.name, sym, book.bid, book.ask, book.mid, book.spread_bps, sig.score,
                        equity=equity, quote_free=cash_irt, asset_free=None
                    )
                w.last_event = f"SAFE:ORDERS_BLOCKED {sym}"
                _set_engine('Hold', 'SAFE:ORDERS_BLOCKED', reject=True, meta={'sym': sym, 'entry_attempt': (not has_pos), 'stage': 'ENTRY'})
                return
            try:
                thr_u = float(getattr(w, "_entry_throttle_until", 0.0) or 0.0)
            except Exception:
                thr_u = 0.0
            if thr_u and time.time() < thr_u:
                w.last_event = f"ENTRY_THROTTLED {sym}"
                _set_engine("Run", "ENTRY_THROTTLED", reject=True, meta={"sym": sym, "until": float(thr_u), "entry_attempt": (not has_pos), "stage": "ENTRY"})
                return
            # --- FIX: prevent BUY if exchange still has an open BUY for this symbol (restart-safe) ---
            try:
                obm = getattr(w, "_open_orders_by_sym", None)
                if isinstance(obm, dict):
                    rec = obm.get(sym)
                    if isinstance(rec, dict) and (rec.get("buy") or 0) > 0:
                        w.last_event = f"OPEN_BUY_EXISTS {sym}"
                        _set_engine("Run", "OPEN_BUY_EXISTS", reject=True, meta={"sym": sym, "stage": "ENTRY", "open_buy": int(rec.get("buy") or 0)})
                        return
            except Exception:
                pass
            if _pending_guard("buy", stage="ENTRY"):
                return
            try:
                re_cd = float(getattr(getattr(w, "cfg", None), "min_hold_sec", None) or getattr(self.cfg, "min_hold_sec", 0.0) or 0.0)
            except Exception:
                re_cd = 0.0
            if re_cd > 0.0:
                try:
                    m0 = getattr(w, "_last_exit_ts_by_sym", None)
                    if not isinstance(m0, dict):
                        m0 = {}
                    last_exit = float(m0.get(sym, 0.0) or 0.0)
                except Exception:
                    last_exit = 0.0
                if last_exit > 0.0:
                    dt = float(time.time() - float(last_exit))
                    if dt >= 0.0 and dt < float(re_cd):
                        try:
                            w.last_event = f"REENTRY_COOLDOWN {sym}"
                        except Exception:
                            pass
                        _set_engine(
                            "Run",
                            "REENTRY_COOLDOWN",
                            reject=True,
                            meta={"sym": sym, "entry_attempt": (not has_pos), "stage": "ENTRY",
                                  "remain": float(max(0.0, float(re_cd - dt))), "cooldown": float(re_cd), "last_exit": float(last_exit)},
                        )
                        return
            if not self._idem_ok(w.name, sym, "buy", ttl_sec=w.cfg.idempotency_ttl_sec):
                try:
                    w.last_event = f"IDEMPOTENCY {sym}"
                except Exception:
                    pass
                _set_engine(
                    "Run",
                    "IDEMPOTENCY",
                    reject=True,
                    meta={"sym": sym, "entry_attempt": (not has_pos), "stage": "ENTRY", "ttl": float(getattr(w.cfg, "idempotency_ttl_sec", 0.0) or 0.0)},
                )
                return
            try:
                setattr(w, "_last_order_action_ts", float(time.time()))
            except Exception:
                pass
            try:
                _ctx_tok = None
                try:
                    if risk_decision is not None:
                        _ctx_tok = _CTX_SKIP_RUNTIME_RISK_MULT.set(True)
                except Exception:
                    _ctx_tok = None
                try:
                    if bool(getattr(w.cfg, "laddering", False)) and int(getattr(w.cfg, "ladder_steps", 1) or 1) > 1:
                        resp = await w.exec.place_ladder(sym, "buy", qty, book.ask, float(notional))
                    else:
                        resp = await w.exec.place_limit(sym, "buy", qty, book.ask, float(notional))
                finally:
                    if _ctx_tok is not None:
                        try:
                            _CTX_SKIP_RUNTIME_RISK_MULT.reset(_ctx_tok)
                        except Exception:
                            pass
                try:
                    rhb = _hb_state.get(sym) or {}
                    if not isinstance(rhb, dict):
                        rhb = {}
                    cids = []
                    if isinstance(resp, dict) and resp.get("ladder") and isinstance(resp.get("children"), list):
                        for ch in (resp.get("children") or []):
                            if not isinstance(ch, dict):
                                continue
                            c = ch.get("cid") or ch.get("client_id") or ch.get("clientId") or ch.get("client_order_id") or ch.get("clientOrderId")
                            if c:
                                cids.append(str(c))
                    elif isinstance(resp, dict):
                        c = resp.get("cid") or resp.get("client_id") or resp.get("clientId") or resp.get("client_order_id") or resp.get("clientOrderId")
                        if c:
                            cids.append(str(c))
                    if cids:
                        rhb["last_buy_cid"] = str(cids[-1])
                        rhb["last_buy_cids"] = list(cids)
                        _hb_state[sym] = rhb
                except Exception:
                    pass
            except asyncio.CancelledError:
                raise
            except Exception as e:
                try:
                    w.last_event = f"EXEC_ERROR {sym}"
                except Exception:
                    pass
                _set_engine(
                    "Hold",
                    "EXEC_ERROR",
                    reject=True,
                    meta={"sym": sym, "entry_attempt": (not has_pos), "stage": "EXEC", "err": str(e)[:180]},
                )
                try:
                    self._idem_forget(str(getattr(w, "name", "") or ""), sym, "buy")
                except Exception:
                    pass
                return
            ok_resp = False
            if isinstance(resp, dict):
                ok_resp = bool(resp.get("ok"))
                if not ok_resp:
                    try:
                        ok_resp = int(float(resp.get("status") or resp.get("code") or 0)) in (200, 201)
                    except Exception:
                        ok_resp = False
            if isinstance(resp, dict) and resp.get("skipped") and str(resp.get("reason") or "").upper() == "DUPLICATE_PREVENTED":
                try:
                    w.last_event = f"DUPLICATE_SKIPPED {sym}"
                except Exception:
                    pass
                _set_engine("Run", "DUPLICATE_SKIPPED", reject=False, meta={"sym": sym, "stage": "EXEC", "entry_attempt": (not has_pos)})
                return
            if (not ok_resp) and (not bool(getattr(self.cfg, "dry_run", False))):
                try:
                    w.last_event = f"ORDER_REJECT {sym}"
                except Exception:
                    pass
                meta_r = {"sym": sym, "entry_attempt": (not has_pos), "stage": "EXEC", "ok": False}
                try:
                    if isinstance(resp, dict):
                        for k in ("status", "code", "error", "message", "msg", "reason", "detail"):
                            if resp.get(k) is not None:
                                meta_r[k] = resp.get(k)
                        oid = resp.get("order_id") or resp.get("orderId") or resp.get("id")
                        if oid is not None:
                            meta_r["order_id"] = oid
                except Exception:
                    pass
                _set_engine("Run", "ORDER_REJECT", reject=True, meta=meta_r)
                return
            if ok_resp or bool(getattr(self.cfg, "dry_run", False)):
                tag = " CIx2" if float(mult) > 1.0 else ""
                if bool(getattr(self.cfg, "dry_run", False)):
                    w.positions[sym] = Position(sym, qty, book.ask, time.time())
                    w.last_event = f"BUY {sym} qty={qty:.6f}{tag}"
                else:
                    w.last_event = f"BUY_SENT {sym} qty={qty:.6f}{tag}"
                try:
                    sec = float(getattr(self.cfg, "entry_throttle_sec", 2.0) or 2.0)
                    now_t = float(time.time())
                    until0 = float(getattr(w, "_entry_throttle_until", 0.0) or 0.0)
                    setattr(w, "_entry_throttle_until", float(max(until0, now_t + max(0.2, sec))))
                except Exception:
                    pass
                _set_engine("Run", "BUY_SENT", reject=False)
        else:
            score_for_exit = float(getattr(sig, "score", 0.0) or 0.0)
            spot_ready = False
            try:
                src0 = str(getattr(book, "_source", "") or "").upper().strip()
                spot_ready = (src0 == "SPOT_READY") and (not bool(getattr(book, "_stale", False)))
            except Exception:
                spot_ready = False
            # In pure fallback mode (stale synthetic book), avoid score-based exits to prevent noisy churn.
            # In SPOT_READY mode (fresh spot), allow score-based exits (safer to exit than hold).
            if book_fallback and (not spot_ready):
                score_for_exit = 0.0
            try:
                if not math.isfinite(float(score_for_exit)):
                    score_for_exit = 0.0
            except Exception:
                score_for_exit = 0.0
            try:
                act_u = str(getattr(sig, "action", "") or "").upper().strip()
            except Exception:
                act_u = ""
            # Avoid contradictory HOLD/AA_HOLD signals triggering a "SIGNAL_REVERSAL" exit.
            # If the signal explicitly says SELL (and we have a real book), force the score into the
            # reversal domain so RiskManager.should_exit can act deterministically.
            try:
                _sth = float(getattr(getattr(w, "cfg", None), "sell_threshold", None) or getattr(self.cfg, "sell_threshold", 0.20) or 0.20)
            except Exception:
                _sth = abs(float(getattr(self.cfg, "sell_threshold", 0.20) or 0.20))
            if act_u == "SELL" and ((not book_fallback) or spot_ready):
                score_for_exit = -max(abs(float(score_for_exit)), abs(float(_sth)))
            else:
                # Allow score-driven reversal even if action isn't SELL, but only when the score is
                # firmly below -sell_threshold and the signal isn't a spread/AA hold artifact.
                try:
                    _c0 = float(getattr(sig, "confidence", 0.0) or 0.0)
                except Exception:
                    _c0 = 0.0
                try:
                    _ru = str(getattr(sig, "reason", "") or "").upper()
                except Exception:
                    _ru = ""
                if ((not book_fallback) or spot_ready) and (float(score_for_exit) <= -abs(float(_sth))) and (_c0 >= 0.25) and ("SPREAD" not in _ru) and ("AA_HOLD" not in _ru):
                    score_for_exit = float(score_for_exit)
                else:
                    score_for_exit = 0.0
            ph_shadow_exit = False
            try:
                thr = float(getattr(self.cfg, "phoenix_shadow_exit_thr", 0.72) or 0.72)
                sh = getattr(pho, "shadow_score", None)
                lbl = str(getattr(pho, "shadow_label", "") or "").upper()
                if sh is not None and float(sh) <= -abs(thr):
                    if bool(getattr(pho, "ready", False)) or (lbl == "OK"):
                        ph_shadow_exit = True
            except Exception:
                ph_shadow_exit = False
            ph_short_exit = False
            ph_long_hold = False
            try:
                if bool(getattr(self.cfg, "phoenix_enabled", True)):
                    ph_state = str(getattr(pho, "state", "FLAT") or "FLAT").upper().strip()
                    ph_ready = bool(getattr(pho, "ready", False))
                    ph_conf = float(getattr(pho, "confidence", 0.0) or 0.0)
                    ph_comp = float(getattr(pho, "composite", 0.0) or 0.0)
                    minc = float(getattr(self.cfg, "phoenix_min_conf", 0.20) or 0.20)
                    thrx = float(getattr(self.cfg, "phoenix_entry_thr", 0.20) or 0.20)
                    if ph_ready and ph_state == "LONG" and ph_conf >= abs(minc) and ph_comp >= abs(float(thrx)):
                        ph_long_hold = True
                    if ph_ready and ph_state == "SHORT" and ph_conf >= abs(minc) and ph_comp <= -abs(float(thrx)):
                        ph_short_exit = True
                        if float(score_for_exit) > -abs(float(_sth)):
                            score_for_exit = -abs(float(_sth))
            except Exception:
                ph_short_exit = False
                ph_long_hold = False
            should_exit, why = self.risk.should_exit(pos, book, score_for_exit, cfg=getattr(w, 'cfg', None))
            if should_exit and str(why or "") == "SIGNAL_REVERSAL" and ph_short_exit and act_u != "SELL":
                why = "PHOENIX_SHORT_REVERSAL"
            if (not should_exit) and ph_shadow_exit:
                should_exit, why = True, "PHOENIX_SHADOW_EXIT"
            if should_exit and str(why or "") == "SIGNAL_REVERSAL" and ph_long_hold and (not ph_short_exit) and (not ph_shadow_exit):
                should_exit, why = False, "PHOENIX_LONG_HOLD"
            try:
                setattr(w, 'last_exit_why', str(why or ''))
            except Exception:
                pass
            if not should_exit:
                if act_u == "SELL":
                    try:
                        sig.action = "HOLD"
                        rs = str(getattr(sig, "reason", "") or "").strip()
                        tag = str(why or "SELL_BLOCKED")
                        if tag:
                            sig.reason = (rs or "EDGE") + "+" + tag
                    except Exception:
                        pass
                    try:
                        w.last_event = f"EXIT_HOLD {sym} {str(why or '')[:32]}"
                    except Exception:
                        pass
                    _set_engine("Run", str(why or "EXIT_HOLD"), reject=False, meta={"sym": sym, "stage": "EXIT"})
                if self.recorder:
                    equity = self._estimate_equity_irt(cash_irt, w.positions, current_sym=sym, current_mid=book.mid)
                    await self._low_priority_call(
                        self.recorder.record_tick,
                        time.time(), w.name, sym, book.bid, book.ask, book.mid, book.spread_bps, sig.score,
                        equity=equity, quote_free=cash_irt, asset_free=None
                    )
                return
            if getattr(self.risk, "hard_blocks_all_orders", lambda *a, **k: False)(side="sell", reduce_only=True):
                if self.recorder:
                    equity = self._estimate_equity_irt(cash_irt, w.positions, current_sym=sym, current_mid=book.mid)
                    await self._low_priority_call(
                        self.recorder.record_tick,
                        time.time(), w.name, sym, book.bid, book.ask, book.mid, book.spread_bps, sig.score,
                        equity=equity, quote_free=cash_irt, asset_free=None
                    )
                w.last_event = f"SAFE:ORDERS_BLOCKED {sym}"
                return
            try:
                # Exit safety: never send an exit SELL while there are outstanding BUY orders for this symbol.
                # This prevents accidental re-entry after the exit (especially with laddering) and also covers
                # order-journal desync cases by checking the exchange open orders directly when possible.
                if hasattr(w, "ex"):
                    wallet_name = str(getattr(w, "name", "") or getattr(w, "id", "") or getattr(w, "wallet", "") or "")
                    have_buy_pending = False
                    try:
                        pend = self.orders.pending() if hasattr(self, "orders") else {}
                    except Exception:
                        pend = {}
                    if isinstance(pend, dict) and pend:
                        for _cid, _rec in pend.items():
                            if not isinstance(_rec, dict):
                                continue
                            if str(_rec.get("wallet") or "") != wallet_name:
                                continue
                            if _canon_symbol(_rec.get("symbol") or "") != sym:
                                continue
                            if str(_rec.get("side") or "").lower().strip() == "buy":
                                have_buy_pending = True
                                break
                    try:
                        obm = getattr(w, "_open_orders_by_sym", None)
                        if isinstance(obm, dict):
                            rec = obm.get(sym)
                            if isinstance(rec, dict) and (rec.get("buy") or 0) > 0:
                                have_buy_pending = True
                    except Exception:
                        pass
                    open_buy_ids: List[str] = []
                    try:
                        resp0 = await w.ex.list_orders(symbol=sym, status="open")
                        orders0 = OrderJournal._extract_orders(resp0)
                        for o0 in (orders0 or []):
                            try:
                                s0 = str(o0.get("side") or o0.get("type") or "").lower().strip()
                                if not s0.startswith("buy"):
                                    continue
                                oid0 = OrderJournal._order_id(o0)
                                if oid0:
                                    open_buy_ids.append(str(oid0))
                            except Exception:
                                continue
                    except Exception:
                        open_buy_ids = []
                    if have_buy_pending or open_buy_ids:
                        rhb = _hb_state.get(sym) or {}
                        if not isinstance(rhb, dict):
                            rhb = {}
                        now_can = float(time.time())
                        last_can = float(rhb.get("last_cancel_pending_buy_ts", 0.0) or 0.0)
                        min_gap = float(_env_float("EXIT_CANCEL_PENDING_BUY_MIN_GAP_SEC", 3.0) or 3.0)
                        if (now_can - last_can) >= max(0.5, min_gap):
                            rhb["last_cancel_pending_buy_ts"] = now_can
                            _hb_state[sym] = rhb
                            try:
                                if open_buy_ids:
                                    for oid0 in open_buy_ids:
                                        try:
                                            await w.ex.cancel_order(oid0)
                                        except Exception:
                                            continue
                                else:
                                    # If we couldn't enumerate open orders, fall back to cancel-all for this symbol.
                                    await w.ex.cancel_all_orders(symbol=sym)
                            except Exception:
                                try:
                                    await w.ex.cancel_all_orders(symbol=sym)
                                except Exception:
                                    pass
                        try:
                            w.last_event = f"WAIT_CANCEL_BUY {sym}"
                        except Exception:
                            pass
                        _set_engine("Run", "WAIT_CANCEL_BUY", reject=True, meta={"sym": sym, "stage": "EXIT"})
                        return
            except Exception:
                # Fail-safe: if we cannot validate/cancel BUY orders, do not place an exit SELL in this cycle.
                try:
                    w.last_event = f"WAIT_CANCEL_BUY {sym}"
                except Exception:
                    pass
                _set_engine("Run", "WAIT_CANCEL_BUY", reject=True, meta={"sym": sym, "stage": "EXIT", "err": "CANCEL_BUY_GUARD_FAIL"})
                return
            # Guard: if the exchange already has an open SELL for this symbol, do not send another exit SELL.
            # This prevents duplicate exits / oversell after restarts or order-journal desync.
            try:
                obm = getattr(w, "_open_orders_by_sym", None)
                if isinstance(obm, dict):
                    rec = obm.get(sym)
                    if isinstance(rec, dict) and (rec.get("sell") or 0) > 0:
                        try:
                            w.last_event = f"OPEN_SELL_EXISTS {sym}"
                        except Exception:
                            pass
                        _set_engine("Run", "OPEN_SELL_EXISTS", reject=True,
                                    meta={"sym": sym, "entry_attempt": False, "stage": "EXIT", "open_sell": int(rec.get("sell") or 0)})
                        return
            except Exception:
                pass

            if _pending_guard("sell", stage="EXIT"):
                return
            if not self._idem_ok(w.name, sym, "sell", ttl_sec=w.cfg.idempotency_ttl_sec):
                try:
                    w.last_event = f"IDEMPOTENCY {sym}"
                except Exception:
                    pass
                _set_engine(
                    "Run",
                    "IDEMPOTENCY",
                    reject=True,
                    meta={"sym": sym, "entry_attempt": False, "stage": "EXIT", "ttl": float(getattr(w.cfg, "idempotency_ttl_sec", 0.0) or 0.0)},
                )
                return
            # Use an execution price consistent with the exit decision price (stale/spot books use mid).
            sell_px = float(getattr(book, "bid", 0.0) or 0.0)
            try:
                if bool(getattr(book, "_stale", False)):
                    sell_px = float(getattr(book, "mid", sell_px) or sell_px)
                else:
                    src0 = str(getattr(book, "_source", "") or "").lower().strip()
                    if src0.startswith(("spot", "synth", "disk")):
                        sell_px = float(getattr(book, "mid", sell_px) or sell_px)
            except Exception:
                pass
            if (not math.isfinite(float(sell_px))) or float(sell_px) <= 0.0:
                try:
                    w.last_event = f"EXIT_NO_PX {sym}"
                except Exception:
                    pass
                _set_engine("Hold", "EXIT_NO_PX", reject=True, meta={"sym": sym, "entry_attempt": False, "stage": "EXIT"})
                return
            sell_notional = float(pos.qty) * float(sell_px)
            try:
                qm = float(quote_mult or 1.0)
                if math.isfinite(qm) and qm > 0.0:
                    sell_notional = float(sell_notional) * float(1.0 / qm)
            except Exception:
                pass
            try:
                setattr(w, "_last_order_action_ts", float(time.time()))
            except Exception:
                pass
            try:
                if bool(getattr(w.cfg, "laddering", False)) and int(getattr(w.cfg, "ladder_steps", 1) or 1) > 1:
                    resp = await w.exec.place_ladder(sym, "sell", pos.qty, float(sell_px), float(sell_notional))
                else:
                    resp = await w.exec.place_limit(sym, "sell", pos.qty, float(sell_px), float(sell_notional))
            except asyncio.CancelledError:
                raise
            except Exception as e:
                try:
                    w.last_event = f"EXEC_ERROR {sym}"
                except Exception:
                    pass
                _set_engine(
                    "Hold",
                    "EXEC_ERROR",
                    reject=True,
                    meta={"sym": sym, "entry_attempt": False, "stage": "EXIT_EXEC", "err": str(e)[:180]},
                )
                try:
                    self._idem_forget(str(getattr(w, "name", "") or ""), sym, "sell")
                except Exception:
                    pass
                return
            try:
                rhb = _hb_state.get(sym) or {}
                if not isinstance(rhb, dict):
                    rhb = {}
                cids = []
                if isinstance(resp, dict) and resp.get("ladder") and isinstance(resp.get("children"), list):
                    for ch in (resp.get("children") or []):
                        if not isinstance(ch, dict):
                            continue
                        c = ch.get("cid") or ch.get("client_id") or ch.get("clientId") or ch.get("client_order_id") or ch.get("clientOrderId")
                        if c:
                            cids.append(str(c))
                elif isinstance(resp, dict):
                    c = resp.get("cid") or resp.get("client_id") or resp.get("clientId") or resp.get("client_order_id") or resp.get("clientOrderId")
                    if c:
                        cids.append(str(c))
                if cids:
                    rhb["last_sell_cid"] = str(cids[-1])
                    rhb["last_sell_cids"] = list(cids)
                    _hb_state[sym] = rhb
            except Exception:
                pass
            ok_resp = False
            if isinstance(resp, dict):
                ok_resp = bool(resp.get("ok"))
                if not ok_resp:
                    try:
                        ok_resp = int(float(resp.get("status") or resp.get("code") or 0)) in (200, 201)
                    except Exception:
                        ok_resp = False
            if isinstance(resp, dict) and resp.get("skipped") and str(resp.get("reason") or "").upper() == "DUPLICATE_PREVENTED":
                try:
                    w.last_event = f"DUPLICATE_SKIPPED {sym}"
                except Exception:
                    pass
                _set_engine("Run", "DUPLICATE_SKIPPED", reject=False, meta={"sym": sym, "stage": "EXIT", "entry_attempt": False})
                return
            if (not ok_resp) and (not self.cfg.dry_run):
                try:
                    w.last_event = f"ORDER_REJECT {sym}"
                except Exception:
                    pass
                meta_r = {"sym": sym, "entry_attempt": False, "stage": "EXIT", "ok": False}
                try:
                    if isinstance(resp, dict):
                        for k in ("status", "code", "error", "message", "msg", "reason", "detail"):
                            if resp.get(k) is not None:
                                meta_r[k] = resp.get(k)
                        oid = resp.get("order_id") or resp.get("orderId") or resp.get("id")
                        if oid is not None:
                            meta_r["order_id"] = oid
                except Exception:
                    pass
                _set_engine("Run", "ORDER_REJECT", reject=True, meta=meta_r)
                try:
                    self._idem_forget(str(getattr(w, "name", "") or ""), sym, "sell")
                except Exception:
                    pass
                return
            if ok_resp or self.cfg.dry_run:
                if self.cfg.dry_run:
                    pnl_quote = (float(sell_px) - pos.entry_px) * pos.qty
                    conv_irt = 1.0
                    try:
                        qm = float(quote_mult or 1.0)
                        if math.isfinite(qm) and qm > 0.0:
                            conv_irt = 1.0 / qm
                    except Exception:
                        conv_irt = 1.0
                    pnl_irt = float(pnl_quote) * float(conv_irt)
                    try:
                        w.pnl_realized_irt += float(pnl_irt)
                    except Exception:
                        pass
                    pnl_pct = (float(sell_px) - pos.entry_px) / pos.entry_px if pos.entry_px > 0 else 0.0
                    self.risk.register_close(sym, pnl_irt, pnl_pct, cash_irt=float(max(float(getattr(w, "cash_irt", 0.0) or 0.0), float(cash_irt or 0.0))))
                    try:
                        pm = getattr(self, "perf_monitor", None)
                        if pm is not None:
                            pm.record_trade(symbol=sym, wallet=str(getattr(w, "name", "")), pnl_irt=float(pnl_irt), pnl_pct=float(pnl_pct))
                    except Exception:
                        pass
                    w.positions.pop(sym, None)
                    try:
                        m1 = getattr(w, "_last_exit_ts_by_sym", None)
                        if not isinstance(m1, dict):
                            m1 = {}
                        m1[sym] = float(time.time())
                        setattr(w, "_last_exit_ts_by_sym", m1)
                    except Exception:
                        pass
                    w.last_event = f"SELL {sym} pnl={pnl_irt:.0f}"
                else:
                    try:
                        w.last_event = f"SELL_SENT {sym} qty={float(getattr(pos,'qty',0.0) or 0.0):.6f}"
                    except Exception:
                        pass
                    _set_engine("Run", "SELL_SENT", reject=False)
        if self.recorder:
            equity = self._estimate_equity_irt(cash_irt, w.positions, current_sym=sym, current_mid=book.mid)
            await self._low_priority_call(
                self.recorder.record_tick,
                time.time(), w.name, sym, book.bid, book.ask, book.mid, book.spread_bps, sig.score,
                equity=equity, quote_free=cash_irt, asset_free=None
            )
        self._log.info("[%s:%s] score=%.4f conf=%.2f action=%s px=%.0f spr=%.1f event=%s",
                       w.name, sym, sig.score, sig.confidence, sig.action, sig.price, book.spread_bps, w.last_event)
    def _flash_ref_symbols(self) -> List[str]:
        refs = list(getattr(self.cfg, "flash_ref_symbols", []) or [])
        refs = [_canon_symbol(s) for s in refs if str(s).strip()]
        if refs:
            return refs
        pr = list(getattr(self.cfg, "symbol_priority", []) or [])
        pr = [_canon_symbol(s) for s in pr if str(s).strip()]
        if pr:
            return pr[:3]
        syms = list(getattr(self.cfg, "symbols", []) or [])
        syms = [_canon_symbol(s) for s in syms if str(s).strip()]
        for s in ("BTCIRT", "BTCUSDT", "BTC-USDT"):
            if any(_canon_symbol(x) == _canon_symbol(s) for x in syms):
                return [_canon_symbol(s)]
        return [syms[0]] if syms else ["BTCIRT"]
    async def _check_flash_crash_once(self) -> Optional[dict]:
        if not bool(getattr(self.cfg, "flash_crash_enabled", True)):
            return None
        if self._global_exit_fired:
            return {"already_fired": True}
        now = time.time()
        if (now - float(self._flash_last_check_ts)) < 0.35:
            return None
        self._flash_last_check_ts = now
        if self.global_exit.should_rate_limit():
            return None
        refs = self._flash_ref_symbols()
        confirm_need = int(getattr(self.cfg, "flash_min_confirmations", 1) or 1)
        confirm = 0
        worst = None
        for sym in refs:
            sym = _canon_symbol(sym)
            try:
                book = await asyncio.wait_for(
                    self.feed.fetch_depth(sym, use_disk_cache_on_timeout=self.cfg.price_cache_on_timeout),
                    timeout=min(0.9, float(self.cfg.symbol_timeout_sec)),
                )
            except Exception:
                continue
            if not book or book.mid is None:
                continue
            self.global_exit.observe(sym, float(book.mid), ts=now)
            trig = self.global_exit.check_symbol(sym)
            if trig:
                confirm += 1
                if worst is None or float(trig.get("drop", 0.0)) > float(worst.get("drop", 0.0)):
                    worst = trig
        if worst and confirm >= confirm_need:
            worst["confirmations"] = int(confirm)
            worst["confirm_need"] = int(confirm_need)
            return worst
        return None
    async def _cancel_open_orders(self, w: WalletRuntime) -> int:
        try:
            resp = await w.ex.list_orders()
            orders = OrderJournal._extract_orders(resp)
        except Exception as e:
            self._log.warning("event=GLOBAL_EXIT_LIST_ORDERS_FAIL wallet=%s err=%s", w.name, e)
            return 0
        canceled = 0
        for o in orders:
            try:
                st = OrderJournal._order_status(o)
                if OrderJournal._is_terminal_status(st):
                    continue
                oid = OrderJournal._order_id(o)
                if not oid:
                    continue
                c_to = max(2.5, float(getattr(self.cfg, "low_priority_timeout_sec", 0.8) or 0.8))
                for _try in range(2):
                    try:
                        await asyncio.wait_for(w.ex.cancel_order(oid), timeout=c_to)
                        canceled += 1
                        break
                    except Exception:
                        if _try == 0:
                            await asyncio.sleep(0.25)
                        continue
            except Exception:
                continue
        if canceled:
            self._log.warning("event=GLOBAL_EXIT_CANCELLED wallet=%s canceled=%d", w.name, canceled)
        return int(canceled)
    async def _liquidate_positions(self, w: WalletRuntime, reason: str) -> dict:
        if (not self.cfg.dry_run) and (not bool(getattr(self.cfg, "global_exit_armed", False))):
            self._log.critical("event=GLOBAL_EXIT_NOT_ARMED wallet=%s reason=%s (LIVE) -> HALT_ONLY", w.name, reason)
            return {"armed": False, "attempted": 0, "closed": 0}
        sl_bps = float(getattr(self.cfg, "global_exit_slippage_bps", 80.0) or 80.0)
        attempted = 0
        closed = 0
        details = []
        for sym, pos in list(w.positions.items()):
            sym = _canon_symbol(sym)
            qty = float(getattr(pos, "qty", 0.0) or 0.0)
            if qty <= 0:
                continue
            attempted += 1
            try:
                book = await asyncio.wait_for(
                    self.feed.fetch_depth(sym, use_disk_cache_on_timeout=w.cfg.price_cache_on_timeout),
                    timeout=min(1.2, float(w.cfg.symbol_timeout_sec)),
                )
                if not book or book.bid is None:
                    raise RuntimeError("no_book")
                bid = float(book.bid)
                px = max(1.0, bid * (1.0 - sl_bps / 10000.0))
                notion = float(qty) * float(px)
                self._ctx_enter(sym, "SELL")
                try:
                    _CTX_SKIP_RUNTIME_RISK_MULT.set(True)
                    resp = await asyncio.wait_for(
                        w.exec.place_limit(sym, "sell", qty, px, float(notion)),
                        timeout=3.5,
                    )
                finally:
                    _CTX_SKIP_RUNTIME_RISK_MULT.set(False)
                    self._ctx_exit(sym, "SELL")
                ok_resp = bool(getattr(resp, "ok", False)) or bool(getattr(resp, "data", None)) or self.cfg.dry_run
                if not ok_resp:
                    try:
                        _body = getattr(resp, "error", None) or getattr(resp, "data", None) or repr(resp)
                        _err = ExchangeClient._safe_body_for_log(_body, limit=120)
                        try:
                            self._log.error("event=GLOBAL_EXIT_PLACE_LIMIT_NOT_OK sym=%s qty=%s px=%s err=%s", sym, qty, px, _err)
                        except Exception:
                            pass
                        details.append({"sym": sym, "qty": qty, "px": px, "ok": False, "err": _err})
                    except Exception:
                        try:
                            self._log.error("event=GLOBAL_EXIT_PLACE_LIMIT_NOT_OK sym=%s qty=%s px=%s err=order_not_ok", sym, qty, px)
                        except Exception:
                            pass
                        details.append({"sym": sym, "qty": qty, "px": px, "ok": False, "err": "order_not_ok"})
                    continue
                w.last_event = f"GLOBAL_EXIT:{reason}"
                details.append({"sym": sym, "qty": qty, "px": px, "ok": True})
            except Exception as e:
                details.append({"sym": sym, "qty": qty, "ok": False, "err": ExchangeClient._safe_body_for_log(f"{type(e).__name__}: {str(e) or repr(e)}", limit=120)})
                continue
        if not self.cfg.dry_run:
            try:
                await asyncio.sleep(0.4)
            except Exception:
                pass
        if self.cfg.dry_run:
            closed = attempted
            w.positions.clear()
        else:
            closed = 0
        return {"armed": bool(getattr(self.cfg, "global_exit_armed", False)) or self.cfg.dry_run, "attempted": attempted, "closed": closed, "details": details}
    async def _execute_global_exit(self, trigger: dict) -> None:
        if self._global_exit_fired:
            return
        self._global_exit_fired = True
        self.global_exit.mark_fired()
        sym = str(trigger.get("symbol", ""))
        peak = float(trigger.get("peak", 0.0) or 0.0)
        last = float(trigger.get("last", 0.0) or 0.0)
        drop = float(trigger.get("drop", 0.0) or 0.0) * 100.0
        reason = f"FLASH_CRASH drop>={float(getattr(self.cfg, 'flash_crash_pct', 0.05))*100:.1f}%"
        self.risk.halt_new_trades(f"GLOBAL_EXIT:{reason}")
        self._log.critical(
            "event=GLOBAL_EXIT_FIRED reason=%s ref=%s drop_pct=%.2f peak=%.0f last=%.0f confirmations=%s/%s",
            reason, sym, drop, peak, last, str(trigger.get("confirmations")), str(trigger.get("confirm_need")),
        )
        for w in self.wallets.values():
            try:
                await self._cancel_open_orders(w)
            except Exception:
                pass
            try:
                out = await self._liquidate_positions(w, reason="FLASH_CRASH")
                self._log.critical("event=GLOBAL_EXIT_WALLET wallet=%s attempted=%s closed=%s armed=%s",
                                   w.name, str(out.get("attempted")), str(out.get("closed")), str(out.get("armed")))
            except Exception as e:
                self._log.critical("event=GLOBAL_EXIT_WALLET_FAIL wallet=%s err=%s", w.name, e)
        try:
            self._save_state_if_needed(force=True)
        except Exception:
            pass
    async def cycle_wallet(self, w: WalletRuntime) -> None:
        try:
            _wdu = float(getattr(w, "_balance_disabled_until", 0.0) or 0.0)
            _now = time.time()
            if _wdu > _now:
                try:
                    self._log.warning(
                        "event=WALLET_BALANCE_COOLDOWN wallet=%s phase=cycle_wallet retry_in=%.1f fail_count=%s",
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
                self._log.warning(
                    "event=WALLET_BAL_REFRESH_FAIL wallet=%s phase=cycle_wallet err=%s",
                    getattr(w, "name", "?"),
                    e,
                )
            except Exception:
                pass
            try:
                print(
                    f"ISOCHK phase=cycle_wallet wallet={getattr(w, 'name', '?')} err={type(e).__name__}:{e} fail_count={_fc}",
                    flush=True,
                )
            except Exception:
                pass
            try:
                self._log.warning(
                    "event=WALLET_ISOLATED wallet=%s phase=cycle_wallet reason=%s fail_count=%s cooldown_sec=120",
                    getattr(w, "name", "?"),
                    str(e),
                    _fc,
                )
            except Exception:
                pass
            return
        w.cash_irt = cash_irt
        try:
            if getattr(self, 'risk', None) is not None:
                self.risk.update_wallet_balance_snapshot(
                    str(getattr(w, 'name', '') or ''),
                    float(getattr(w, 'cash_irt', 0.0) or 0.0),
                    float(getattr(w, 'cash_total_irt', 0.0) or getattr(w, 'cash_irt', 0.0) or 0.0),
                    bool(getattr(w, 'last_balance_ok', False)),
                    ts=float(getattr(w, 'last_balance_ts', 0.0) or time.time()),
                )
        except Exception:
            pass
        try:
            await self._refresh_orders_if_needed(w)
        except Exception:
            pass
        try:
            interval = float(getattr(self.cfg, 'orders_reconcile_interval_sec', 30.0) or 30.0)
            if (not bool(getattr(self.cfg, 'dry_run', False))) and interval > 0.0:
                last_rec = float(getattr(w, 'last_reconcile_ts', 0.0) or 0.0)
                now = time.time()
                if (now - last_rec) >= interval:
                    w.last_reconcile_ts = float(now)
                    unknown = int(await self.orders.reconcile_wallet(w.ex, w.name)) if hasattr(self, 'orders') else 0
                    if unknown and _env_bool('LIVE_TRADING', False) and _env_bool("SAFE_RECONCILE", True):
                        w.sanity_halt = True
                        w.sanity_reason = f'ORDER_DESYNC unknown={unknown}'
                        try:
                            hold = float(getattr(self.cfg, 'sanity_hold_sec', 8.0) or 8.0)
                            w.sanity_until_ts = float(now + max(2.0, hold))
                        except Exception:
                            w.sanity_until_ts = float(now + 8.0)
                        _obs_trace(w, "ORDERS_RECONCILE_UNKNOWN", reason=str(unknown), meta={})
                        try:
                            if _env_bool("SAFE_RECONCILE_STRICT", True) and _env_bool("GLOBAL_SAFE_ON_ORDER_DESYNC", False):
                                self.risk.halt_new_trades(f'ORDER_RECONCILE_UNKNOWN:{unknown}')
                        except Exception:
                            pass
        except Exception as e:
            self._log.warning('event=ORDERS_RECONCILE_RUNTIME_FAIL wallet=%s err=%s', w.name, e)
            _obs_trace(w, "ORDERS_RECONCILE_FAIL", reason=f"{type(e).__name__}: {e}"[:120], meta={})
            if _env_bool('LIVE_TRADING', False) and _env_bool("SAFE_RECONCILE", True) and _env_bool("SAFE_RECONCILE_STRICT", True) and _env_bool("GLOBAL_SAFE_ON_ORDER_DESYNC", False):
                try:
                    self.risk.halt_new_trades('ORDER_RECONCILE_FAIL')
                except Exception:
                    pass
        t0 = time.time()
        budget = float(getattr(self.cfg, "cycle_budget_sec", 0.0) or 0.0)
        deadline = (t0 + budget) if budget > 0 else None
        syms_all = list(self._symbols_priority_order(w.cfg, w))
        try:
            _msw = int(os.getenv("MAX_SYMBOLS_PER_WALLET", "0") or "0")
        except Exception:
            _msw = 0
        if _msw and int(_msw) > 0:
            try:
                syms_all = syms_all[:max(1, int(_msw))]
            except Exception:
                pass
        syms = syms_all
        try:
            if budget > 0.0 and len(syms_all) > 0:
                st = float(getattr(w.cfg, "symbol_timeout_sec", 3.2) or 3.2)
                per_sym = max(1.10, min(2.60, 0.78 * st + 0.35))
                headroom = max(1.80, min(6.00, 0.42 * budget + 1.30))
                max_syms = int(max(1.0, math.floor(max(0.0, budget - headroom) / per_sym)))
                max_syms = max(1, min(max_syms, len(syms_all)))
                if max_syms < len(syms_all):
                    fixed = syms_all[: min(2, max_syms)]
                    rest = syms_all[len(fixed):]
                    take = max(0, max_syms - len(fixed))
                    if rest and take > 0:
                        if not hasattr(self, "_rr_sym_offset"):
                            self._rr_sym_offset = {}
                        off = int(self._rr_sym_offset.get(w.name, 0) or 0)
                        start = off % len(rest)
                        rotated = rest[start:] + rest[:start]
                        syms = fixed + rotated[:take]
                        self._rr_sym_offset[w.name] = (off + take) % max(1, len(rest))
                    else:
                        syms = fixed
        except Exception:
            syms = syms_all
        try:
            topn_q = int(_env_int("QUALITY_TOPN", 9) or 9)
            ttl_q = float(_env_float("QUALITY_REFRESH_SEC", 20.0) or 20.0)
            now_q = time.time()
            last_q = float(getattr(self, "_quality_last_ts", 0.0) or 0.0)
            if (now_q - last_q) >= max(5.0, ttl_q) or not getattr(self, "_quality_syms", None):
                ranked = []
                try:
                    for r in (self.get_top8_snapshot() or []):
                        s0 = _canon(str((r or {}).get("symbol") or ""))
                        if s0 and s0 not in ranked:
                            ranked.append(s0)
                except Exception:
                    pass
                for s in (syms_all or []):
                    s0 = _canon(s)
                    if s0 and s0 not in ranked:
                        ranked.append(s0)
                self._quality_syms = ranked[: max(1, min(32, topn_q))]
                self._quality_last_ts = float(now_q)
            quality_syms = list(getattr(self, "_quality_syms", []) or [])
        except Exception:
            quality_syms = []
        try:
            if _env_bool("AUTO_UPGRADE_WALLETS", True) and quality_syms:
                min_iv = float(_env_float("UPGRADE_MIN_INTERVAL", 60.0) or 60.0)
                last_up = float(getattr(w, "last_upgrade_ts", 0.0) or 0.0)
                now_u = time.time()
                if (now_u - last_up) >= max(10.0, min_iv):
                    if int(getattr(w, "open_orders_exch", 0) or 0) == 0 and not bool(getattr(w, "sanity_halt", False)):
                        lows = []
                        for sym, pos in (getattr(w, "positions", {}) or {}).items():
                            s0 = _canon(sym)
                            if s0 and (s0 not in quality_syms):
                                lows.append((s0, pos))
                        if lows:
                            lows.sort(key=lambda it: float(getattr(it[1], "entry_ts", 0.0) or 0.0))
                            sym_low, pos_low = lows[0]
                            qty = float(getattr(pos_low, "qty", 0.0) or 0.0)
                            if qty > 0.0:
                                ob = None
                                try:
                                    ob = self.feed._cache.get(sym_low, (None, None))[1] if hasattr(self.feed, "_cache") else None
                                except Exception:
                                    ob = None
                                bid = float(getattr(ob, "bid", 0.0) or 0.0) if ob else 0.0
                                mid = float(getattr(ob, "mid", 0.0) or 0.0) if ob else 0.0
                                px0 = bid if bid > 0 else mid
                                if px0 > 0.0:
                                    slip_bps = float(_env_float("UPGRADE_SLIP_BPS", 12.0) or 12.0)
                                    px = float(px0 * (1.0 - max(0.0, slip_bps) / 10000.0))
                                    await w.exec.place_limit(sym_low, "sell", qty, px, float(qty * px))
                                    w.last_upgrade_ts = float(now_u)
                                    try:
                                        w.last_event = "UPGRADE_SELL"
                                    except Exception:
                                        pass
        except (TradingHalt, TemporaryPause):
            raise
        except Exception:
            pass
        try:
            try:
                try:
                    import asyncio as _pp_asyncio
                except:
                    pass
            except:
                pass
        except Exception:
            _pp_asyncio = None
        max_conc = 1  #
        if _pp_asyncio is None:
            for sym in syms:
                if deadline is not None and time.time() >= deadline:
                    self._log.warning("event=HEARTBEAT_BUDGET_EXCEEDED wallet=%s budget=%.2f", w.name, budget)
                    break
                await self._process_symbol_heartbeat(w, sym, float(cash_irt) * self._focus_weight_for(sym))
                if bool(getattr(w, 'sanity_halt', False)):
                    break
        else:
            sem = _pp_asyncio.Semaphore(max_conc)
            _halt_t = globals().get("TradingHalt")
            _pause_t = globals().get("TemporaryPause")
            async def _hb_one(_sym: str):
                async with sem:
                    return await self._process_symbol_heartbeat(w, _sym, float(cash_irt) * self._focus_weight_for(_sym))
            for i in range(0, len(syms), max_conc):
                if bool(getattr(w, 'sanity_halt', False)):
                    break
                if deadline is not None:
                    remaining = float(deadline - time.time())
                    if remaining <= 0.0:
                        self._log.warning("event=HEARTBEAT_BUDGET_EXCEEDED wallet=%s budget=%.2f", w.name, budget)
                        break
                else:
                    remaining = None
                batch = syms[i:i + max_conc]
                tasks = [_pp_asyncio.create_task(_hb_one(s)) for s in batch]
                try:
                    if remaining is not None:
                        results = await _pp_asyncio.wait_for(
                            _pp_asyncio.gather(*tasks, return_exceptions=True),
                            timeout=max(0.05, remaining),
                        )
                    else:
                        results = await _pp_asyncio.gather(*tasks, return_exceptions=True)
                except _pp_asyncio.TimeoutError:
                    self._log.warning("event=HEARTBEAT_BUDGET_EXCEEDED wallet=%s budget=%.2f", w.name, budget)
                    for t in tasks:
                        try:
                            if not t.done():
                                t.cancel()
                        except Exception:
                            pass
                    try:
                        await _pp_asyncio.wait_for(_pp_asyncio.gather(*tasks, return_exceptions=True), timeout=0.2)
                    except Exception:
                        pass
                    break
                try:
                    for r in results:
                        if _halt_t is not None and isinstance(r, _halt_t):
                            raise r
                        if _pause_t is not None and isinstance(r, _pause_t):
                            raise r
                except Exception:
                    raise
        try:
            if hasattr(self, "dzh"):
                await self.dzh.update_wallet_metrics(self, w)
        except Exception:
            pass
    async def _assert_ordpos_invariant(self, w: WalletRuntime, *, where: str = "") -> None:
        try:
            oo = int(getattr(w, "open_orders_exch", 0) or 0)
        except Exception:
            oo = 0
        try:
            pc = int(len(getattr(w, "positions", {}) or {}))
        except Exception:
            pc = 0
        now0 = time.time()
        if not (oo > 0 and pc == 0):
            try:
                setattr(w, "_orphan_first_ts", 0.0)
            except Exception:
                pass
            try:
                setattr(w, "_orphan_cancel_cooldown_ts", 0.0)
            except Exception:
                pass
            return
        try:
            cool_until = float(getattr(w, "_orphan_cancel_cooldown_ts", 0.0) or 0.0)
        except Exception:
            cool_until = 0.0
        if cool_until and now0 < cool_until:
            return
        try:
            grace = float(_env_float("ORPHAN_GRACE_SEC", 10.0) or 10.0)
        except Exception:
            grace = 10.0
        grace = max(2.0, float(grace))
        oldest_age = None
        try:
            oa = float(getattr(w, "open_orders_oldest_age_sec", 0.0) or 0.0)
            if oa > 0.0 and math.isfinite(oa):
                oldest_age = oa
        except Exception:
            oldest_age = None
        try:
            first_ts = float(getattr(w, "_orphan_first_ts", 0.0) or 0.0)
        except Exception:
            first_ts = 0.0
        if not first_ts:
            try:
                setattr(w, "_orphan_first_ts", float(now0))
            except Exception:
                pass
            try:
                setattr(w, "last_engine_status", "WARN")
                setattr(w, "last_engine_reason", "ORPHAN_PENDING_SYNC")
                setattr(w, "last_engine_ts", float(now0))
            except Exception:
                pass
            try:
                w.sanity_halt = True
                w.sanity_reason = "ORPHAN_PENDING_SYNC"
                w.sanity_since_ts = float(now0)
                w.sanity_until_ts = float(now0 + min(3.0, grace))
            except Exception:
                pass
            try:
                setattr(w, "last_orders_ts", 0.0)
            except Exception:
                pass
            return
        seen_age = max(0.0, float(now0 - first_ts))
        if (seen_age < grace) and (oldest_age is None or oldest_age < grace):
            try:
                setattr(w, "last_engine_status", "WARN")
                setattr(w, "last_engine_reason", "ORPHAN_GRACE_WAIT")
                setattr(w, "last_engine_ts", float(now0))
            except Exception:
                pass
            try:
                w.sanity_halt = True
                w.sanity_reason = "ORPHAN_GRACE_WAIT"
                if not float(getattr(w, "sanity_since_ts", 0.0) or 0.0):
                    w.sanity_since_ts = float(now0)
                w.sanity_until_ts = float(now0 + min(3.0, max(1.5, grace - seen_age)))
            except Exception:
                pass
            try:
                setattr(w, "last_orders_ts", 0.0)
            except Exception:
                pass
            return
        try:
            _obs_trace(w, "ASSERT_ORDPOS_ORPHAN", reason="ORD>0 POS=0", meta={"oo": int(oo), "seen_age_s": float(seen_age), "oldest_s": oldest_age, "where": str(where or "")})
        except Exception:
            pass
        try:
            setattr(w, "last_engine_status", "LOCKED")
            setattr(w, "last_engine_reason", "ORPHAN_CANCEL_SCHEDULED")
            setattr(w, "last_engine_ts", float(now0))
        except Exception:
            pass
        try:
            hold_sec = float(getattr(self.cfg, "orphan_hold_sec", 4.0) or 4.0)
        except Exception:
            hold_sec = 4.0
        hold_sec = max(2.0, float(hold_sec))
        try:
            w.sanity_halt = True
            w.sanity_reason = "ORPHAN_CANCEL_SCHEDULED"
            w.sanity_since_ts = float(now0)
            w.sanity_until_ts = float(now0 + hold_sec)
        except Exception:
            pass
        try:
            setattr(w, "_orphan_cancel_cooldown_ts", float(now0 + max(hold_sec, 8.0)))
        except Exception:
            pass
        try:
            inflight = bool(getattr(w, "_orphan_cancel_inflight", False))
        except Exception:
            inflight = False
        if not inflight:
            try:
                setattr(w, "_orphan_cancel_inflight", True)
            except Exception:
                pass
            async def _do_cancel() -> None:
                try:
                    to = float(_env_float("ORPHAN_CANCEL_TIMEOUT_SEC", 20.0) or 20.0)
                except Exception:
                    to = 20.0
                to = max(5.0, float(to))
                try:
                    await asyncio.wait_for(self._cancel_open_orders(w), timeout=to)
                except Exception as e:
                    try:
                        self._log.warning("event=ORPHAN_CANCEL_FAIL wallet=%s err=%s", str(getattr(w, "name", "")), str(e)[:200])
                    except Exception:
                        pass
                    try:
                        async def _retry_once() -> None:
                            try:
                                await asyncio.sleep(5)
                            except Exception:
                                pass
                            try:
                                await asyncio.wait_for(self._cancel_open_orders(w), timeout=to)
                            except Exception:
                                pass
                            try:
                                setattr(w, "last_orders_ts", 0.0)
                            except Exception:
                                pass
                            try:
                                await self._refresh_orders_if_needed(w)
                            except Exception:
                                pass
                        asyncio.create_task(_retry_once(), name=f"orphan_cancel_retry_{str(getattr(w,'name','W'))}")
                    except Exception:
                        pass
                finally:
                    try:
                        setattr(w, "_orphan_cancel_inflight", False)
                    except Exception:
                        pass
                    try:
                        setattr(w, "_orphan_first_ts", 0.0)
                    except Exception:
                        pass
                    try:
                        setattr(w, "last_orders_ts", 0.0)
                    except Exception:
                        pass
                    try:
                        asyncio.create_task(self._refresh_orders_if_needed(w), name=f"orphan_refresh_{str(getattr(w,'name','W'))}")
                    except Exception:
                        try:
                            asyncio.create_task(self._refresh_orders_if_needed(w))
                        except Exception:
                            pass
            try:
                asyncio.create_task(_do_cancel(), name=f"orphan_cancel_{str(getattr(w,'name','W'))}")
            except Exception:
                try:
                    setattr(w, "_orphan_cancel_inflight", False)
                except Exception:
                    pass
        try:
            setattr(w, "last_orders_ts", 0.0)
        except Exception:
            pass
    def _derive_market_regime(self) -> str:
        snap = []
        try:
            snap = list(self.get_top8_snapshot() or [])
        except Exception:
            snap = []
        changes = []
        for r in (snap or []):
            try:
                if not isinstance(r, dict):
                    continue
                for k in ("change24h", "change_24h", "pct", "pct_change", "change", "chg", "changePct", "pct_24h", "pct24h"):
                    if k in r:
                        v = r.get(k)
                        if v is None:
                            continue
                        changes.append(float(v))
                        break
            except Exception:
                continue
        if not changes:
            return str(getattr(self, "_market_regime", "") or "UNKNOWN")
        try:
            bull_thr = float(getattr(self.cfg, "market_bull_thr_pct", 0.35) or 0.35)
        except Exception:
            bull_thr = 0.35
        avg = sum(changes) / max(1.0, float(len(changes)))
        return "BULL" if avg >= bull_thr else "BEAR"
    async def _market_regime_reeval(self) -> None:
        now0 = time.time()
        new_reg = self._derive_market_regime()
        old_reg = str(getattr(self, "_market_regime", "") or "")
        if not old_reg:
            old_reg = "UNKNOWN"
        if new_reg and new_reg != old_reg:
            try:
                setattr(self, "_market_regime", str(new_reg))
                setattr(self, "_market_regime_last_ts", float(now0))
            except Exception:
                pass
            try:
                burst = float(getattr(self.cfg, "market_reeval_burst_sec", 15.0) or 15.0)
            except Exception:
                burst = 15.0
            for w in (getattr(self, "wallets", {}) or {}).values():
                try:
                    setattr(w, "_force_state_reset_until", float(now0 + max(5.0, burst)))
                except Exception:
                    pass
                try:
                    setattr(w, "_entry_throttle_until", 0.0)
                except Exception:
                    pass
                try:
                    rs = str(getattr(w, "last_engine_reason", "") or "").upper()
                    if ("LOW_SC" in rs) or ("TREND" in rs) or ("VOL" in rs) or ("LIQ" in rs) or ("SPREAD" in rs) or ("DYN" in rs) or ("CAP" in rs) or ("PROFIT" in rs):
                        setattr(w, "last_engine_status", "Run")
                        setattr(w, "last_engine_reason", f"MKT_REEVAL {old_reg}->{new_reg}")
                        setattr(w, "last_engine_ts", float(now0))
                except Exception:
                    pass
            try:
                self._log.info("event=MARKET_REGIME_CHANGE old=%s new=%s", old_reg, new_reg)
            except Exception:
                pass
    async def cycle_wallet_cleanup(self, w: WalletRuntime) -> None:
        if bool(getattr(w, 'wallet_disabled', False)):
            try:
                await _autonomy_refresh_wallet_token(self, w)
            except Exception:
                pass
            if bool(getattr(w, 'wallet_disabled', False)):
                return
        try:
            pm = getattr(self, "perf_monitor", None)
            if pm is not None:
                now_ts = float(time.time())
                last = float(getattr(self, "_autonomy_last_perf_tick_ts", 0.0) or 0.0)
                if (now_ts - last) >= float(_env_float("PERF_TICK_INTERVAL_SEC", 30.0) or 30.0):
                    met = pm.tick()
                    try:
                        setattr(self, "_autonomy_last_perf_tick_ts", now_ts)
                    except Exception:
                        pass
                    st = str(met.get("state") or "HEALTHY").upper()
                    try:
                        setattr(w, "perf_state", st)
                    except Exception:
                        pass
                    if st == "CRITICAL":
                        try:
                            self.risk.set_safe(True, "PERF_CRITICAL")
                        except Exception:
                            pass
        except Exception:
            pass
        try:
            await self._refresh_orders_if_needed(w)
        except Exception:
            pass
        await self._assert_ordpos_invariant(w, where="cleanup_pre")
        try:
            oo = int(getattr(w, "open_orders_exch", 0) or 0)
        except Exception:
            oo = 0
        try:
            pc = int(len(getattr(w, "positions", {}) or {}))
        except Exception:
            pc = 0
        if oo > 0 and pc == 0:
            now0 = time.time()
            try:
                if not float(getattr(w, "_locked_since_ts", 0.0) or 0.0):
                    setattr(w, "_locked_since_ts", float(now0))
            except Exception:
                pass
            try:
                locked_since = float(getattr(w, "_locked_since_ts", now0) or now0)
            except Exception:
                locked_since = now0
            age = max(0.0, float(now0 - locked_since))
            try:
                force_sec = float(getattr(self.cfg, "locked_force_cancel_sec", 120.0) or 120.0)
            except Exception:
                force_sec = 120.0
            if age >= max(5.0, force_sec):
                try:
                    _obs_trace(w, "LOCKED_FORCE_CANCEL", reason="timeout", meta={"age_sec": age, "oo": int(oo)})
                except Exception:
                    pass
                try:
                    async def _locked_force_cancel() -> None:
                        try:
                            to2 = float(_env_float("ORPHAN_CANCEL_TIMEOUT_SEC", 20.0) or 20.0)
                        except Exception:
                            to2 = 20.0
                        to2 = max(5.0, float(to2))
                        try:
                            await asyncio.wait_for(self._cancel_open_orders(w), timeout=to2)
                        except Exception:
                            pass
                        finally:
                            try:
                                setattr(w, "last_orders_ts", 0.0)
                            except Exception:
                                pass
                            try:
                                asyncio.create_task(self._refresh_orders_if_needed(w), name=f"locked_force_refresh_{getattr(w,'name','')}")
                            except Exception:
                                try:
                                    asyncio.create_task(self._refresh_orders_if_needed(w))
                                except Exception:
                                    pass
                    asyncio.create_task(_locked_force_cancel(), name=f"locked_force_cancel_{getattr(w,'name','')}")
                except Exception:
                    pass
                try:
                    setattr(w, "last_orders_ts", 0.0)
                except Exception:
                    pass
        try:
            interval = float(getattr(self.cfg, 'orders_reconcile_interval_sec', 30.0) or 30.0)
            if (not bool(getattr(self.cfg, 'dry_run', False))) and interval > 0.0:
                last_rec = float(getattr(w, 'last_reconcile_ts', 0.0) or 0.0)
                now = time.time()
                if (now - last_rec) >= interval:
                    w.last_reconcile_ts = float(now)
                    unknown = int(await self.orders.reconcile_wallet(w.ex, w.name)) if hasattr(self, 'orders') else 0
                    if unknown and _env_bool('LIVE_TRADING', False) and _env_bool("SAFE_RECONCILE", True):
                        w.sanity_halt = True
                        w.sanity_reason = f'ORDER_DESYNC unknown={unknown}'
                        try:
                            hold = float(getattr(self.cfg, 'sanity_hold_sec', 8.0) or 8.0)
                            w.sanity_until_ts = float(now + max(2.0, hold))
                        except Exception:
                            w.sanity_until_ts = float(now + 8.0)
                        _obs_trace(w, "ORDERS_RECONCILE_UNKNOWN", reason=str(unknown), meta={})
        except Exception:
            pass
        try:
            syms_all = list(self._symbols_priority_order(w.cfg, w))
            topn_q = int(_env_int("QUALITY_TOPN", 9) or 9)
            ttl_q = float(_env_float("QUALITY_REFRESH_SEC", 20.0) or 20.0)
            now_q = time.time()
            last_q = float(getattr(self, "_quality_last_ts", 0.0) or 0.0)
            if (now_q - last_q) >= max(5.0, ttl_q) or not getattr(self, "_quality_syms", None):
                ranked = []
                try:
                    for r in (self.get_top8_snapshot() or []):
                        s0 = _canon(str((r or {}).get("symbol") or ""))
                        if s0 and s0 not in ranked:
                            ranked.append(s0)
                except Exception:
                    pass
                for s0 in (syms_all or []):
                    ss = _canon(s0)
                    if ss and ss not in ranked:
                        ranked.append(ss)
                self._quality_syms = ranked[: max(1, min(32, topn_q))]
                self._quality_last_ts = float(now_q)
            quality_syms = list(getattr(self, "_quality_syms", []) or [])
            if _env_bool("AUTO_UPGRADE_WALLETS", True) and quality_syms:
                min_iv = float(_env_float("UPGRADE_MIN_INTERVAL", 60.0) or 60.0)
                last_up = float(getattr(w, "last_upgrade_ts", 0.0) or 0.0)
                now_u = time.time()
                if (now_u - last_up) >= max(10.0, min_iv):
                    if int(getattr(w, "open_orders_exch", 0) or 0) == 0 and not bool(getattr(w, "sanity_halt", False)):
                        lows = []
                        for sym, pos in (getattr(w, "positions", {}) or {}).items():
                            s0 = _canon(sym)
                            if s0 and (s0 not in quality_syms):
                                lows.append((s0, pos))
                        if lows:
                            lows.sort(key=lambda it: float(getattr(it[1], "entry_ts", 0.0) or 0.0))
                            sym_low, pos_low = lows[0]
                            qty = float(getattr(pos_low, "qty", 0.0) or 0.0)
                            if qty > 0.0:
                                ob = None
                                try:
                                    ob = self.feed._cache.get(sym_low, (None, None))[1] if hasattr(self.feed, "_cache") else None
                                except Exception:
                                    ob = None
                                bid = float(getattr(ob, "bid", 0.0) or 0.0) if ob else 0.0
                                mid = float(getattr(ob, "mid", 0.0) or 0.0) if ob else 0.0
                                px0 = bid if bid > 0 else mid
                                if px0 > 0.0:
                                    slip_bps = float(_env_float("UPGRADE_SLIP_BPS", 12.0) or 12.0)
                                    px = float(px0 * (1.0 - max(0.0, slip_bps) / 10000.0))
                                    await w.exec.place_limit(sym_low, "sell", qty, px, float(qty * px))
                                    w.last_upgrade_ts = float(now_u)
                                    try:
                                        w.last_event = "UPGRADE_SELL"
                                    except Exception:
                                        pass
        except Exception:
            pass
        await self._assert_ordpos_invariant(w, where="cleanup_post")
    async def cycle_wallet_dashboard(self, w: WalletRuntime) -> None:
        if bool(getattr(w, 'wallet_disabled', False)):
            return
        try:
            if hasattr(self, "dzh"):
                await self.dzh.update_wallet_metrics(self, w)
        except Exception:
            return
    async def execute_order_v121(
        self,
        current_price: float,
        balance: float,
        symbol: Optional[str] = None,
        wallet: Optional[str] = None,
        current_volume: Optional[float] = None,
        volume_history: Optional[List[float]] = None,
    ) -> None:
        if not hasattr(self, "sovereign") or getattr(self, "sovereign", None) is None:
            self.sovereign = SovereignEngine()
        if not hasattr(self, "analyzer") or getattr(self, "analyzer", None) is None:
            self.analyzer = _VolatilityAnalyzer()
        w = None
        if wallet:
            w = (getattr(self, "wallets", {}) or {}).get(str(wallet))
        if w is None:
            w = next(iter((getattr(self, "wallets", {}) or {}).values()), None)
        if w is None:
            return
        sym = _canon_symbol(symbol or "")
        if not sym:
            try:
                pri = list(getattr(w.cfg, "symbol_priority", []) or [])
                sym = _canon_symbol(pri[0]) if pri else ""
            except Exception:
                sym = ""
        if not sym:
            try:
                syms = list(getattr(w.cfg, "symbols", []) or [])
                sym = _canon_symbol(syms[0]) if syms else ""
            except Exception:
                sym = ""
        if not sym:
            return
        px = float(current_price or 0.0)
        if px <= 0:
            return
        ts_ms = None
        for attr in (
            "last_exchange_ts_ms",
            "last_tick_ts_ms",
            "last_market_ts_ms",
            "last_ts_ms",
            "exchange_ts_ms",
        ):
            v = getattr(self, attr, None)
            if isinstance(v, (int, float)) and float(v) > 0:
                ts_ms = float(v)
                break
        if ts_ms is None:
            ts_ms = time.time() * 1000.0
        ok, _lag = self.sovereign.monitor.check_lag(ts_ms)
        if not ok:
            return
        try:
            self.analyzer.update(sym, px)
        except Exception:
            pass
        try:
            sigma = float(getattr(self.analyzer, "get_sigma", self.analyzer.get_volatility)(sym))
        except Exception:
            try:
                sigma = float(self.analyzer.get_volatility(sym))
            except Exception:
                sigma = 0.001
        whale_active = False
        try:
            cv = None
            if current_volume is not None:
                cv = float(current_volume)
            else:
                for attr in ("last_volume", "last_tick_volume", "last_trade_volume", "current_volume", "volume"):
                    v = getattr(self, attr, None)
                    if isinstance(v, dict):
                        v = v.get(sym) or v.get(str(sym))
                    if isinstance(v, (int, float)) and float(v) > 0:
                        cv = float(v)
                        break
            vh = volume_history
            if vh is None:
                for attr in ("volume_history", "vol_hist", "volumes", "volume_window", "volume_deque"):
                    v = getattr(self, attr, None)
                    if isinstance(v, dict):
                        v = v.get(sym) or v.get(str(sym))
                    if v is not None and hasattr(v, "__iter__"):
                        try:
                            vh = list(v)
                            break
                        except Exception:
                            pass
            if cv is not None and float(cv) > 0:
                whale_active = bool(self.sovereign.monitor.detect_whale_activity(float(cv), vh))
                self.sovereign.monitor.update_volume(float(cv))
        except Exception:
            whale_active = False
        effective_sigma = float(sigma) * 2.0 if whale_active else float(sigma)
        try:
            smart_ladder = list(self.sovereign.evolution.get_exponential_ladder(px, effective_sigma, side="buy", levels=5))
        except Exception:
            smart_ladder = [px * 0.995]
        if not smart_ladder:
            return
        try:
            safe_qty_total = float(self.sovereign.risk.calculate_kelly_size(float(balance), price=px))
        except Exception:
            safe_qty_total = max(0.0, float(balance) * 0.12 / px) if px > 0 else 0.0
        if safe_qty_total <= 0:
            return
        try:
            if abs(px - float(smart_ladder[0])) / px < 0.001:
                smart_ladder[0] = px
        except Exception:
            pass
        qty_each = safe_qty_total / float(len(smart_ladder))
        api = getattr(self, "api", None)
        for target_px in smart_ladder:
            tp = float(target_px)
            if tp <= 0:
                continue
            notional = float(qty_each) * float(tp)
            try:
                await w.exec.place_limit(sym, "buy", float(qty_each), float(tp), float(notional))
                continue
            except Exception:
                pass
            if api and hasattr(api, "place_limit") and callable(getattr(api, "place_limit")):
                try:
                    await api.place_limit(sym, "buy", float(qty_each), float(tp))
                    continue
                except Exception:
                    pass
        try:
            gc.collect()
        except Exception:
            pass
    async def run(self: "TradingBot") -> None:
        global TERMUX_MODE
        try:
            TERMUX_MODE = bool(os.environ.get("TERMUX_VERSION") or os.environ.get("TERMUX_MODE") == "1" or ("com.termux" in str(os.environ.get("PREFIX", ""))))
        except Exception:
            TERMUX_MODE = False
        try:
            os.nice(-10)
        except Exception:
            pass
        stop_ev = None
        try:
            stop_ev = GLOBAL_SHUTDOWN.bind_asyncio_event()
        except Exception:
            stop_ev = asyncio.Event()
        try:
            if not hasattr(self, "_cycle_count"):
                self._cycle_count = 0
            if not hasattr(self, "_cycle_best_conf"):
                self._cycle_best_conf = 0.0
        except Exception:
            pass
        try:
            try:
                loop = asyncio.get_running_loop()
                def _pp200_asyncio_handler(_loop, context):
                    try:
                        exc = context.get("exception") or Exception(context.get("message", "asyncio"))
                        _pp200_report(exc, tag="ASYNCIO", ctx={"message": str(context.get("message", ""))[:200]}, logger=getattr(self, "_log", None))
                    except Exception:
                        pass
                loop.set_exception_handler(_pp200_asyncio_handler)
            except Exception:
                pass
        except Exception:
            pass
        self._log.info(
            "event=BOT_RUN_START live=%s dry_run=%s wallets=%s symbols=%s",
            str(_env_bool("LIVE_TRADING", False)),
            str(bool(getattr(self.cfg, "dry_run", False))),
            str(len(getattr(self, "wallets", {}) or {})),
            ",".join(list(getattr(self.cfg, "symbols", []) or [])[:12]),
        )
        try:
            if not hasattr(self, "_rtp_boot_ts") or float(getattr(self, "_rtp_boot_ts", 0.0) or 0.0) <= 0.0:
                setattr(self, "_rtp_boot_ts", float(time.time()))
        except Exception:
            pass
        try:
            if not hasattr(self, "_boot_ts") or float(getattr(self, "_boot_ts", 0.0) or 0.0) <= 0.0:
                setattr(self, "_boot_ts", float(getattr(self, "_rtp_boot_ts", time.time()) or time.time()))
        except Exception:
            pass
        try:
            asyncio.create_task(self._refresh_market_snapshot_if_needed(), name="prime_snapshot")
        except Exception:
            pass
        try:
            asyncio.create_task(self._refresh_market_focus_if_needed(), name="prime_focus")
        except Exception:
            pass
        try:
            asyncio.create_task(self._refresh_top8_if_needed(), name="prime_top8")
        except Exception:
            pass
        dash = None
        try:
            if bool(getattr(self.cfg, "dash_enabled", False)):
                dash = DashboardManager(
                    self,
                    refresh_sec=float(getattr(self.cfg, "dash_refresh_sec", 1.5) or 1.5),
                    screen=bool(getattr(self.cfg, "dash_screen", False)),
                )
                dash.start()
        except Exception:
            dash = None
        try:
            exec_interval = float(getattr(self.cfg, "exec_loop_interval_sec", 0.6) or 0.6)
        except Exception:
            exec_interval = 0.6
        try:
            cleanup_interval = float(getattr(self.cfg, "cleanup_loop_interval_sec", 1.8) or 1.8)
        except Exception:
            cleanup_interval = 1.8
        try:
            dash_interval = float(getattr(self.cfg, "dash_loop_interval_sec", float(getattr(self.cfg, "dash_refresh_sec", 1.5) or 1.5)) or 1.5)
        except Exception:
            dash_interval = 1.5
        async def _safe_bg(tag: str, coro) -> None:
            try:
                if coro is None:
                    return
                await coro
            except asyncio.CancelledError:
                raise
            except Exception as e:
                try:
                    self._log.exception("event=BG_ERR tag=%s err=%s", str(tag), str(e)[:200])
                except Exception:
                    logging.exception("event=BG_ERR tag=%s", str(tag))
        def _bg_once(tag: str, coro) -> None:
            try:
                if coro is None:
                    return
                attr = f"_bg_{tag}_task"
                t = getattr(self, attr, None)
                if t is None or bool(getattr(t, "done", lambda: True)()):
                    setattr(self, attr, asyncio.create_task(_safe_bg(tag, coro), name=f"bg_{tag}"))
                    try:
                        setattr(self, f"_bg_{tag}_start_ts", float(time.time()))
                    except Exception:
                        pass
                else:
                    try:
                        now = float(_rt_now(self))
                        st_attr = f"_bg_{tag}_start_ts"
                        st = float(getattr(self, st_attr, 0.0) or 0.0)
                        if st <= 0.0:
                            try:
                                setattr(self, st_attr, float(now))
                                st = float(now)
                            except Exception:
                                st = float(now)
                        hard = 0.0
                        ttag = str(tag)
                        if ttag == "top8":
                            try:
                                hard = float(os.getenv("TOP8_BG_HARD_TIMEOUT_SEC", "20") or "12")
                            except Exception:
                                hard = 12.0
                        elif ttag == "focus":
                            try:
                                hard = float(os.getenv("FOCUS_BG_HARD_TIMEOUT_SEC", "30") or "25")
                            except Exception:
                                hard = 25.0
                        elif ttag == "snapshot":
                            try:
                                hard = float(os.getenv("SNAPSHOT_BG_HARD_TIMEOUT_SEC", "30") or "25")
                            except Exception:
                                hard = 25.0
                        else:
                            try:
                                hard = float(os.getenv("BG_HARD_TIMEOUT_SEC", "0") or "0")
                            except Exception:
                                hard = 0.0
                        if float(hard) > 0.0 and (now - st) > float(hard):
                            try:
                                t.cancel()
                            except Exception:
                                pass
                            try:
                                setattr(self, attr, asyncio.create_task(_safe_bg(tag, coro), name=f"bg_{tag}"))
                                try:
                                    setattr(self, st_attr, float(now))
                                except Exception:
                                    pass
                                return
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        if asyncio.iscoroutine(coro):
                            coro.close()
                    except Exception:
                        pass
            except Exception:
                try:
                    if asyncio.iscoroutine(coro):
                        coro.close()
                except Exception:
                    pass
        async def _exec_loop() -> None:
            for _omega_guard in range(1000000):
                if stop_ev.is_set() or bool(getattr(self, "_global_exit_fired", False)):
                    return
                t0 = time.time()
                now0 = float(t0)
                deadline0 = float(t0 + exec_interval)
                try:
                    self._last_cycle_ts = float(t0)
                    self._cycle_count = int(getattr(self, "_cycle_count", 0) or 0) + 1
                    try:
                        self._cycle_best_conf = 0.0
                    except Exception:
                        pass
                except Exception:
                    pass
                wallets = list((getattr(self, "wallets", {}) or {}).values())
                try:
                    wc = int(getattr(self.cfg, "wallet_concurrency", 0) or 0)
                except Exception:
                    wc = 0
                if wc <= 0:
                    try:
                        wc = int(_env_int("WALLET_CONCURRENCY", 0) or 0)
                    except Exception:
                        wc = 0
                if wc <= 0:
                    wc = len(wallets) if wallets else 1
                wc = max(1, min(10, wc))
                async def _cycle_one_wallet_exec(w: WalletRuntime) -> object | None:
                    if stop_ev.is_set() or bool(getattr(self, "_global_exit_fired", False)):
                        return None
                    try:
                        if bool(getattr(w, "sanity_halt", False)):
                            until = float(getattr(w, "sanity_until_ts", 0.0) or 0.0)
                            if until and time.time() < until:
                                _obs_trace(w, "SANITY_HOLD", reason=str(getattr(w, "sanity_reason", "") or "")[:120], meta={"until": until})
                                return None
                            w.sanity_halt = False
                            w.sanity_reason = ""
                    except Exception:
                        pass
                    try:
                        await self.cycle_wallet_execution(w, float(now0), float(deadline0) if deadline0 is not None else None)
                        try:
                            if hasattr(self, "net"):
                                self.net.on_ok()
                        except Exception:
                            pass
                        return None
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        try:
                            if hasattr(self, "net"):
                                self.net.on_error("", str(type(e).__name__)[:32])
                        except Exception:
                            pass
                        try:
                            try:
                                now_ts = float(time.time())
                                dq = getattr(self, "_wd_wallet_exec_fail_ts", None)
                                if dq is None:
                                    dq = __import__("collections").deque(maxlen=4096)
                                    setattr(self, "_wd_wallet_exec_fail_ts", dq)
                                dq.append(now_ts)
                                dqw = getattr(self, "_wd_wallet_exec_fail_by_wallet", None)
                                if dqw is None or not isinstance(dqw, dict):
                                    dqw = {}
                                    setattr(self, "_wd_wallet_exec_fail_by_wallet", dqw)
                                wn = str(getattr(w, "name", "?") or "?")
                                dqw[wn] = int(dqw.get(wn, 0) or 0) + 1
                                try:
                                    if hasattr(self, "_bump_warn_event"):
                                        self._bump_warn_event("WALLET_EXEC_FAIL")
                                except Exception:
                                    pass
                                k = f"WALLET_EXEC_FAIL:{wn}"
                                min_iv = float(_env_float("WALLET_EXEC_FAIL_LOG_MIN_INTERVAL_SEC", 30.0) or 30.0)
                                allow = True
                                try:
                                    if hasattr(self, "_log_throttled"):
                                        allow = bool(self._log_throttled(k, min_iv))
                                except Exception:
                                    allow = True
                                if allow:
                                    self._log.warning("event=WALLET_EXEC_FAIL wallet=%s err=%s", wn, e)
                            except Exception:
                                pass
                        except Exception:
                            pass
                        return e
                if wc <= 1 or len(wallets) <= 1:
                    for w in wallets:
                        await _cycle_one_wallet_exec(w)
                else:
                    sem = asyncio.Semaphore(wc)
                    async def _wrap(w: WalletRuntime):
                        async with sem:
                            return await _cycle_one_wallet_exec(w)
                    await asyncio.gather(*[asyncio.create_task(_wrap(w)) for w in wallets], return_exceptions=True)
                dt = time.monotonic() - t0
                target = float(exec_interval)
                try:
                    base = float(exec_interval)
                    try:
                        li = float(getattr(self.cfg, "loop_interval_sec", base * 4.0) or (base * 4.0))
                        base = float(clamp(base, float(li) * 0.20, float(li) * 0.35))
                    except Exception:
                        pass
                    target = float(base)
                    prox = 0.0
                    try:
                        thr_eff, _minc_eff, _szm, _resc, _tag = _termux_adaptive_phoenix_gate(self.cfg, now=time.time())
                        thr_eff = float(max(1e-6, thr_eff))
                    except Exception:
                        thr_eff = 0.20
                    try:
                        mx = 0.0
                        for _w in wallets:
                            try:
                                sc = float(getattr(_w, "phoenix_composite", 0.0) or 0.0)
                            except Exception:
                                sc = 0.0
                            if math.isfinite(sc):
                                mx = max(mx, float(sc))
                        prox = float(clamp(mx / float(thr_eff), 0.0, 1.5))
                    except Exception:
                        prox = 0.0
                    idle_s = 0.0
                    try:
                        idle_s = max(0.0, float(time.time()) - float(_TERMUX_LAST_ORDER_TS or _TERMUX_BOOT_TS))
                    except Exception:
                        idle_s = 0.0
                    tmin = float(_env_float("TERMUX_EXEC_MIN_SEC", 0.35) or 0.35)
                    tmax = float(_env_float("TERMUX_EXEC_MAX_SEC", 1.05) or 1.05)
                    hot_mult = float(_env_float("TERMUX_EXEC_HOT_MULT", 0.70) or 0.70)
                    near_mult = float(_env_float("TERMUX_EXEC_NEAR_MULT", 0.80) or 0.80)
                    ultra = float(_env_float("TERMUX_EXEC_ULTRA_SEC", 0.5) or 0.5)
                    ultra = float(max(0.20, min(2.0, ultra)))
                    if prox >= 0.85:
                        target = max(tmin, min(base * hot_mult, ultra))
                    elif prox >= 0.65:
                        target = max(tmin, ultra)
                    if prox < 0.30:
                        if idle_s >= 3600.0:
                            target = min(tmax, base * float(_env_float("TERMUX_EXEC_IDLE_MULT_60M", 1.45) or 1.45))
                        elif idle_s >= 1800.0:
                            target = min(tmax, base * float(_env_float("TERMUX_EXEC_IDLE_MULT_30M", 1.35) or 1.35))
                        elif idle_s >= 600.0:
                            target = min(tmax, base * float(_env_float("TERMUX_EXEC_IDLE_MULT_10M", 1.25) or 1.25))
                    now_mono = time.monotonic()
                    cool = False
                    try:
                        any_pos = any(bool(getattr(_w, "positions", {}) or {}) for _w in wallets)
                        all_hold = all(str(getattr(_w, "last_engine_status", "") or "").upper().startswith("HOLD") for _w in wallets)
                        cool = (not any_pos) and all_hold and (prox < 0.30)
                    except Exception:
                        cool = False
                    if cool:
                        if not getattr(self, "_cool_since_mono", 0.0):
                            setattr(self, "_cool_since_mono", now_mono)
                    else:
                        setattr(self, "_cool_since_mono", 0.0)
                    cool_dur = 0.0
                    try:
                        tcs = float(getattr(self, "_cool_since_mono", 0.0) or 0.0)
                        cool_dur = (now_mono - tcs) if tcs > 0 else 0.0
                    except Exception:
                        cool_dur = 0.0
                    if cool_dur >= 600.0:
                        target = min(tmax, float(target) + 0.5)
                except Exception:
                    target = float(exec_interval)
                await _sleep_or_stop(stop_ev, max(0.02, float(target) - dt))
        async def _cleanup_loop() -> None:
            try:
                _bg_once("snapshot", self._refresh_market_snapshot_if_needed())
            except Exception:
                pass
            try:
                _bg_once("focus", self._refresh_market_focus_if_needed())
            except Exception:
                pass
            try:
                _bg_once("top8", self._refresh_top8_if_needed())
            except Exception:
                pass
            for _omega_guard in range(1000000):
                if stop_ev.is_set() or bool(getattr(self, "_global_exit_fired", False)):
                    return
                t0 = time.time()
                try:
                    self._save_bot_state()
                except Exception:
                    pass
                try:
                    _bg_once("snapshot", self._refresh_market_snapshot_if_needed())
                except Exception:
                    pass
                try:
                    _bg_once("focus", self._refresh_market_focus_if_needed())
                except Exception:
                    pass
                try:
                    _bg_once("top8", self._refresh_top8_if_needed())
                except Exception:
                    pass
                try:
                    await self._market_regime_reeval()
                except Exception:
                    pass
                try:
                    trig = await self._check_flash_crash_once()
                    if trig:
                        await self._execute_global_exit(trig)
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    try:
                        self._log.warning("event=FLASH_CHECK_FAIL err=%s", e)
                    except Exception:
                        pass
                if bool(getattr(self, "_global_exit_fired", False)):
                    return
                wallets = list((getattr(self, "wallets", {}) or {}).values())
                try:
                    wc = int(getattr(self.cfg, "wallet_cleanup_concurrency", 2) or 2)
                except Exception:
                    wc = 2
                wc = max(1, min(10, wc))
                async def _cycle_one_wallet_cleanup(w: WalletRuntime) -> object | None:
                    try:
                        await self.cycle_wallet_cleanup(w)
                        return None
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        try:
                            self._log.warning("event=WALLET_CLEANUP_FAIL wallet=%s err=%s", getattr(w, "name", "?"), e)
                        except Exception:
                            pass
                        return e
                if wc <= 1 or len(wallets) <= 1:
                    for w in wallets:
                        await _cycle_one_wallet_cleanup(w)
                else:
                    sem = asyncio.Semaphore(wc)
                    async def _wrap(w: WalletRuntime):
                        async with sem:
                            return await _cycle_one_wallet_cleanup(w)
                    await asyncio.gather(*[asyncio.create_task(_wrap(w)) for w in wallets], return_exceptions=True)
                dt = time.time() - t0
                await _sleep_or_stop(stop_ev, max(0.05, cleanup_interval - dt))
        async def _dashboard_loop() -> None:
            if not bool(getattr(self.cfg, "dash_enabled", False)):
                return
            for _omega_guard in range(1000000):
                if stop_ev.is_set() or bool(getattr(self, "_global_exit_fired", False)):
                    return
                t0 = time.time()
                try:
                    for w in (getattr(self, "wallets", {}) or {}).values():
                        try:
                            await self.cycle_wallet_dashboard(w)
                        except Exception:
                            continue
                except Exception:
                    pass
                dt = time.time() - t0
                await _sleep_or_stop(stop_ev, max(0.2, dash_interval - dt))
        async def _build_watch_symbols() -> tuple[list[str], list[str]]:
            """Build a stable symbol set for heartbeat/watchers (TOP8 + focus + holdings + cfg)."""
            dq = "IRT"
            try:
                dq = str(getattr(getattr(self, "cfg", None), "quote", "IRT") or "IRT").upper()
            except Exception:
                dq = "IRT"
            try:
                cfg_syms = list(getattr(self.cfg, "symbols", []) or [])
            except Exception:
                cfg_syms = []
            resolved_map: Dict[str, str] = {}
            try:
                resolved_map = await _fetch_active_symbols(getattr(self, "public", None))
            except Exception:
                resolved_map = {}
            try:
                setattr(self, "_resolved_symbol_map", dict(resolved_map))
                setattr(self, "_resolved_major_map", dict(resolved_map))
            except Exception:
                pass
            try:
                pho0 = getattr(self, "phoenix", None)
                if pho0 is not None:
                    setattr(pho0, "_symbol_map", dict(resolved_map))
            except Exception:
                pass
            majors_assets = ("BTC", "ETH", "USDT", "PAXG", "BNB", "SOL", "XRP", "ZEC", "TON")
            majors_pairs: list[str] = []
            for a in majors_assets:
                s = str(resolved_map.get(a) or "").strip().upper()
                if s:
                    majors_pairs.append(s)
            if not cfg_syms:
                if majors_pairs:
                    cfg_syms = list(majors_pairs[:8])
                else:
                    cfg_syms = ["BTCIRT", "ETHIRT", "USDTIRT", "PAXGIRT"]
            candidates: list[str] = []
            candidates.extend(list(cfg_syms or []))
            try:
                candidates.extend(list(self._phoenix_target_symbols() or []))
            except Exception:
                pass
            try:
                fs = str(getattr(self, "_focus_symbol", "") or "").strip().upper()
                if fs:
                    candidates.append(fs)
            except Exception:
                pass
            try:
                for w in (getattr(self, "wallets", {}) or {}).values():
                    try:
                        hs = str(getattr(w, "holding_symbol", "") or "").strip().upper()
                        if hs:
                            candidates.append(hs)
                    except Exception:
                        continue
            except Exception:
                pass
            candidates.extend(list(majors_pairs[:8] if majors_pairs else []))
            out: list[str] = []
            seen: set[str] = set()
            for s in candidates:
                try:
                    cs = _canon_pair(s, dq)
                except Exception:
                    cs = str(s or "").strip().upper()
                if not cs:
                    continue
                if cs not in seen:
                    seen.add(cs)
                    out.append(cs)
            try:
                max_watch = int(_env_int("WATCH_SYMBOLS_MAX", 18) or 18)
            except Exception:
                max_watch = 18
            max_watch = max(6, min(40, int(max_watch)))
            watch_symbols = out[:max_watch]
            try:
                hb_max = int(_env_int("MKT_HEARTBEAT_SYMS_MAX", 10) or 10)
            except Exception:
                hb_max = 10
            hb_max = max(2, min(max_watch, int(hb_max)))
            hb_syms = watch_symbols[:hb_max]
            if not hb_syms:
                hb_syms = ["BTCIRT", "USDTIRT"]
            return watch_symbols, hb_syms
        async def _market_heartbeat_loop(symbols: List[str]) -> None:
            """Keeps market snapshot timestamps 'truthful' under jitter (best-effort)."""
            try:
                if not bool(_env_bool("MKT_HEARTBEAT_ENABLE", True)):
                    return
            except Exception:
                pass
            log = getattr(self, "_log", logging.getLogger(__name__))
            try:
                interval = float(_env_float("MKT_HEARTBEAT_INTERVAL_SEC", 3.0) or 3.0)
            except Exception:
                interval = 3.0
            interval = float(max(0.8, min(15.0, interval)))
            try:
                timeout = float(_env_float("MKT_HEARTBEAT_TIMEOUT_SEC", max(6.0, interval * 3.0)) or max(6.0, interval * 3.0))
            except Exception:
                timeout = max(6.0, interval * 3.0)
            timeout = float(max(2.0, min(25.0, timeout)))
            try:
                ok_age = float(_env_float("MKT_HEARTBEAT_MAX_DATA_AGE_SEC", max(12.0, interval * 4.0)) or max(12.0, interval * 4.0))
            except Exception:
                ok_age = max(12.0, interval * 4.0)
            ok_age = float(max(4.0, min(120.0, ok_age)))
            syms: list[str] = []
            seen: set[str] = set()
            dq = "IRT"
            try:
                dq = str(getattr(getattr(self, "cfg", None), "quote", "IRT") or "IRT").upper()
            except Exception:
                dq = "IRT"
            for s in (symbols or []):
                try:
                    cs = _canon_pair(s, dq)
                except Exception:
                    cs = str(s or "").strip().upper()
                if cs and cs not in seen:
                    seen.add(cs)
                    syms.append(cs)
            if not syms:
                syms = ["BTCIRT", "USDTIRT"]
            i = 0
            fail = 0
            for _omega_guard in range(150000):
                sym = syms[i % len(syms)]
                i += 1
                now_epoch = float(time.time())
                now_mono = float(time.monotonic())
                ok = False
                src = "-"
                age: Optional[float] = None
                mid_used: float = 0.0
                try:
                    ob = await asyncio.wait_for(
                        self.feed.fetch_depth(sym, use_disk_cache_on_timeout=True, force_refresh=True),
                        timeout=timeout,
                    )
                    bid0 = float(getattr(ob, "bid", 0.0) or 0.0) if ob else 0.0
                    mid0 = float(getattr(ob, "mid", 0.0) or 0.0) if ob else 0.0
                    mid_used = mid0 if mid0 > 0.0 else bid0
                    if ob and (bid0 > 0.0 or mid0 > 0.0):
                        src = str(getattr(ob, "_source", "") or "").lower().strip() or "depth"
                        ts0 = None
                        try:
                            ts0 = _epoch_to_sec(getattr(ob, "ts", 0.0) or 0.0)
                        except Exception:
                            ts0 = None
                        if ts0 and float(ts0) > 0.0:
                            age = max(0.0, float(now_epoch) - float(ts0))
                        else:
                            age = 0.0
                        if src != "disk_cache" or (age is not None and float(age) <= ok_age):
                            ok = True
                except asyncio.TimeoutError:
                    ok = False
                except Exception as e:
                    ok = False
                    try:
                        log.warning("event=MKT_HB_DEPTH_FAIL sym=%s err=%s", sym, str(e)[:220])
                    except Exception:
                        pass
                if not ok:
                    try:
                        px = await asyncio.wait_for(self.feed.fetch_spot(sym), timeout=min(6.0, float(timeout)))
                        if px is not None and float(px or 0.0) > 0.0:
                            src = "spot"
                            mid_used = float(px)
                            age = 0.0
                            ok = True
                    except asyncio.TimeoutError:
                        ok = False
                    except Exception as e:
                        ok = False
                        try:
                            log.warning("event=MKT_HB_SPOT_FAIL sym=%s err=%s", sym, str(e)[:220])
                        except Exception:
                            pass
                if ok:
                    fail = 0
                    try:
                        if mid_used and float(mid_used) > 0.0:
                            ana = getattr(self, "analyzer", None)
                            if ana is None or not hasattr(ana, "update"):
                                try:
                                    ana = _VolatilityAnalyzer(maxlen=int(_env_int("DASH_HIST_POINTS", 240) or 240))
                                    setattr(self, "analyzer", ana)
                                except Exception:
                                    ana = None
                            if ana is not None and hasattr(ana, "update"):
                                ana.update(sym, float(mid_used))
                    except Exception:
                        pass
                    try:
                        setattr(self, "_market_snapshot_local_ts", float(now_epoch))
                        setattr(self, "_market_snapshot_mono_ts", float(now_mono))
                        try:
                            ts_ok_epoch = float(now_epoch)
                            try:
                                if age is not None:
                                    ts_ok_epoch = float(now_epoch) - float(age)
                            except Exception:
                                ts_ok_epoch = float(now_epoch)
                            try:
                                if ts_ok_epoch > (float(now_epoch) + 300.0) or ts_ok_epoch <= 0.0:
                                    ts_ok_epoch = float(now_epoch)
                            except Exception:
                                ts_ok_epoch = float(now_epoch)
                            pub = getattr(self, "public", None)
                            if pub is not None:
                                try:
                                    setattr(pub, "_last_ok_ts", float(ts_ok_epoch))
                                except Exception:
                                    pass
                                try:
                                    if str(src or "").lower().strip() in ("live", "spot"):
                                        setattr(pub, "last_update_time", float(ts_ok_epoch))
                                except Exception:
                                    pass
                            try:
                                setattr(self, "_last_public_update_ts", float(ts_ok_epoch))
                            except Exception:
                                pass
                            try:
                                setattr(self, "_mkt_hb_last_data_ts", float(ts_ok_epoch))
                            except Exception:
                                pass
                        except Exception:
                            pass
                        setattr(self, "_mkt_hb_last_ok_mono", float(now_mono))
                        setattr(self, "_mkt_hb_last_ok_epoch", float(now_epoch))
                        setattr(self, "_mkt_hb_last_sym", sym)
                        setattr(self, "_mkt_hb_last_src", src)
                        setattr(self, "_mkt_hb_last_age", None if age is None else float(age))
                        setattr(self, "_mkt_hb_fail_streak", 0)
                    except Exception:
                        pass
                else:
                    fail += 1
                    try:
                        setattr(self, "_mkt_hb_fail_streak", int(fail))
                    except Exception:
                        pass
                    if fail in (3, 6, 12, 24):
                        try:
                            self.feed.surgical_reset_symbol(sym)
                            log.warning("event=MKT_HB_SURGICAL_RESET sym=%s fail_streak=%d", sym, int(fail))
                        except Exception:
                            pass
                await _sleep_or_stop(stop_ev, interval)
        async def _health_watchdog_loop() -> None:
            """Deterministic health FSM with hysteresis + burst-tolerant N/A semantics."""
            try:
                if not bool(_env_bool("HEALTH_WD_ENABLE", True)):
                    return
            except Exception:
                pass
            try:
                interval = float(_env_float("HEALTH_WD_INTERVAL_SEC", 1.0) or 1.0)
            except Exception:
                interval = 1.0
            interval = float(max(0.4, min(5.0, interval)))
            def _f(name: str, default: float) -> float:
                try:
                    return float(_env_float(name, default) or default)
                except Exception:
                    return float(default)
            mkt_warn = _f("HEALTH_WD_MKT_WARN_SEC", 6.0)
            mkt_crit = max(_f("HEALTH_WD_MKT_CRIT_SEC", 15.0), mkt_warn + 3.0)
            top8_warn = _f("HEALTH_WD_TOP8_WARN_SEC", 6.0)
            top8_crit = max(_f("HEALTH_WD_TOP8_CRIT_SEC", 15.0), top8_warn + 3.0)
            radar_warn = _f("HEALTH_WD_RADAR_WARN_SEC", 12.0)
            radar_crit = max(_f("HEALTH_WD_RADAR_CRIT_SEC", 25.0), radar_warn + 8.0)
            api_warn = _f("HEALTH_WD_API_WARN_SEC", 4.0)
            api_crit = max(_f("HEALTH_WD_API_CRIT_SEC", 12.0), api_warn + 3.0)
            try:
                if bool(_env_bool("TERMUX_MODE", False)) and not (bool(_env_bool("HEALTH_WD_TOP8_ALLOW_STRICT", False)) and bool(_env_bool("HEALTH_WD_TOP8_ALLOW_STRICT_CONFIRM", False))):
                    top8_warn = max(float(top8_warn), float(_env_float("TERMUX_TOP8_WARN_MIN_SEC", 20.0) or 20.0))
                    top8_crit = max(float(top8_crit), float(_env_float("TERMUX_TOP8_CRIT_MIN_SEC", 45.0) or 45.0))
            except Exception:
                pass
            try:
                if bool(_env_bool("TERMUX_MODE", False)) and not (bool(_env_bool("HEALTH_WD_ALLOW_STRICT", False)) and bool(_env_bool("HEALTH_WD_ALLOW_STRICT_CONFIRM", False))):
                    mkt_warn = max(float(mkt_warn), float(_env_float("TERMUX_MKT_WARN_MIN_SEC", 10.0) or 10.0))
                    mkt_crit = max(float(mkt_crit), float(_env_float("TERMUX_MKT_CRIT_MIN_SEC", 40.0) or 40.0), float(mkt_warn) + 3.0)
                    radar_warn = max(float(radar_warn), float(_env_float("TERMUX_RADAR_WARN_MIN_SEC", 30.0) or 30.0))
                    radar_crit = max(float(radar_crit), float(_env_float("TERMUX_RADAR_CRIT_MIN_SEC", 120.0) or 120.0), float(radar_warn) + 8.0)
                    api_warn = max(float(api_warn), float(_env_float("TERMUX_API_WARN_MIN_SEC", 6.0) or 6.0))
                    api_crit = max(float(api_crit), float(_env_float("TERMUX_API_CRIT_MIN_SEC", 25.0) or 25.0), float(api_warn) + 3.0)
                    top8_warn = max(float(top8_warn), float(_env_float("TERMUX_TOP8_WARN_MIN_SEC", 90.0) or 90.0))
                    top8_crit = max(float(top8_crit), float(_env_float("TERMUX_TOP8_CRIT_MIN_SEC", 300.0) or 300.0), float(top8_warn) + 10.0)
            except Exception:
                pass
            try:
                setattr(self, "_hw_thresholds", {
                    "mkt_warn": float(mkt_warn), "mkt_crit": float(mkt_crit),
                    "top8_warn": float(top8_warn), "top8_crit": float(top8_crit),
                    "radar_warn": float(radar_warn), "radar_crit": float(radar_crit),
                    "api_warn": float(api_warn), "api_crit": float(api_crit),
                })
            except Exception:
                pass
            try:
                na_burst_max = int(max(0, min(10, int(_env_int("HEALTH_NA_BURST_MAX", 2) or 2))))
            except Exception:
                na_burst_max = 2
            try:
                na_burst_win = float(max(5.0, min(300.0, float(_env_float("HEALTH_NA_BURST_WINDOW_SEC", 30.0) or 30.0))))
            except Exception:
                na_burst_win = 30.0
            try:
                burst_pen = float(max(1.0, min(120.0, float(_env_float("HEALTH_NA_BURST_PENALTY", 18.0) or 18.0))))
            except Exception:
                burst_pen = 18.0
            recovery_cooldown = _f("HEALTH_RECOVERY_COOLDOWN_SEC", 45.0)
            recover_hold = _f("HEALTH_WD_RECOVER_HOLD_SEC", 6.0)
            try:
                good_need = int(_env_int("HEALTH_WD_RECOVER_GOOD_SAMPLES", 0) or 0)
            except Exception:
                good_need = 0
            if good_need <= 0:
                try:
                    good_need = int(max(3, int(round(float(recover_hold) / max(0.5, float(interval))))))
                except Exception:
                    good_need = 3
            good_need = int(max(2, min(12, int(good_need))))
            ema_win = float(max(3.0, min(120.0, _f("HEALTH_WD_EMA_WINDOW_SEC", 18.0))))
            try:
                n = max(2, int(round(float(ema_win) / float(interval))))
            except Exception:
                n = 10
            alpha = float(clamp(2.0 / float(n + 1), 0.05, 0.60))
            def _ema(prev: Optional[float], x: float) -> float:
                try:
                    x = float(x)
                except Exception:
                    x = float("inf")
                if prev is None or (not isinstance(prev, (int, float))) or (not math.isfinite(float(prev))):
                    return float(x)
                try:
                    return float(prev) + float(alpha) * (float(x) - float(prev))
                except Exception:
                    return float(x)
            def _age_from_mixed_ts(ts: float, now_epoch: float, now_mono: float) -> float:
                try:
                    ts = float(ts or 0.0)
                except Exception:
                    return float("inf")
                if ts <= 0.0 or (not math.isfinite(ts)):
                    return float("inf")
                cand: List[float] = []
                def _push(age: float) -> None:
                    try:
                        a = float(age)
                        if math.isfinite(a) and a >= 0.0:
                            cand.append(a)
                    except Exception:
                        pass
                def _near(x: float, ref: float, max_skew: float) -> bool:
                    try:
                        return math.isfinite(x) and math.isfinite(ref) and abs(float(x) - float(ref)) <= float(max_skew)
                    except Exception:
                        return False
                if ts > 1e11:
                    ts_s = ts / 1000.0
                    if _near(ts_s, now_epoch, 86400.0 * 60.0):
                        _push(max(0.0, float(now_epoch) - float(ts_s)))
                    if _near(ts_s, now_mono, 86400.0 * 60.0):
                        _push(max(0.0, float(now_mono) - float(ts_s)))
                if ts > 1e9:
                    if _near(ts, now_epoch, 86400.0 * 60.0):
                        _push(max(0.0, float(now_epoch) - float(ts)))
                    ts_s = ts / 1000.0  # interpret as monotonic-ms
                    if _near(ts_s, now_mono, 86400.0 * 60.0):
                        _push(max(0.0, float(now_mono) - float(ts_s)))
                if ts <= 1e9:
                    if _near(ts, now_mono, 86400.0 * 60.0):
                        _push(max(0.0, float(now_mono) - float(ts)))
                    if _near(ts, now_epoch, 86400.0 * 60.0):
                        _push(max(0.0, float(now_epoch) - float(ts)))
                if cand:
                    return float(min(cand))
                try:
                    if ts > 1e11:
                        return max(0.0, float(now_epoch) - float(ts / 1000.0))
                    if ts > 1e9:
                        return max(0.0, float(now_epoch) - float(ts))
                    return max(0.0, float(now_mono) - float(ts))
                except Exception:
                    return float("inf")
            def _age_from_ts(ts: float, now: float) -> float:
                return _age_from_mixed_ts(ts, float(now), float(time.monotonic()))
            def _age_guess(ts: float, now_epoch: float, now_mono: float) -> float:
                return _age_from_mixed_ts(ts, float(now_epoch), float(now_mono))
            def _age_from_mono(ts_mono: float, mono_now: float) -> float:
                return _age_from_mixed_ts(ts_mono, float(time.time()), float(mono_now))
            def _public_api_age(now: float) -> float:
                ts_api = None
                try:
                    pub = getattr(self, "public", None)
                    if pub is not None:
                        for k in ("_last_ok_ts", "last_ok_ts", "_ok_ts", "ok_ts", "_last_ts", "last_ts", "_ts", "ts"):
                            try:
                                if hasattr(pub, k):
                                    ts_api = getattr(pub, k)
                                    if ts_api:
                                        break
                            except Exception:
                                continue
                except Exception:
                    ts_api = None
                if ts_api is None:
                    try:
                        ts_api = getattr(self, "_last_public_update_ts", None)
                    except Exception:
                        ts_api = None
                try:
                    return _age_from_mixed_ts(float(ts_api or 0.0), float(now), float(time.monotonic()))
                except Exception:
                    return float("inf")
            state = str(getattr(self, "_hw_state", "INIT") or "INIT").upper()
            if state == "LIVE":
                state = "OK"
            if state not in ("INIT", "OK", "DEGRADED", "CRITICAL", "HALTED"):
                state = "INIT"
            since_ts = float(getattr(self, "_hw_since_ts", 0.0) or 0.0)
            if since_ts <= 0.0:
                since_ts = float(_rt_now(self))
            na_win: Dict[str, deque] = getattr(self, "_hw_na_win", None)
            if not isinstance(na_win, dict):
                na_win = {}
            for k in ("mkt", "top8", "radar", "api"):
                if not isinstance(na_win.get(k), deque):
                    na_win[k] = __import__("collections").deque(maxlen=256)
            ema_mkt = None
            ema_top8 = None
            ema_radar = None
            ema_api = None
            last_crit_ts = float(getattr(self, "_hw_last_crit_ts", 0.0) or 0.0)
            good_streak = int(getattr(self, "_hw_good_streak", 0) or 0)
            scl = StateChangeLogger(getattr(self, "_log", logging.getLogger(__name__)))
            def _burst_count(key: str, now: float) -> int:
                dq = na_win.get(key)
                if not isinstance(dq, deque):
                    return 0
                for _omega_guard in range(150000):
                    dq.popleft()
                return int(len(dq))
            for _omega_guard in range(150000):
                now = float(_rt_now(self))
                mono_now = float(time.monotonic())
                try:
                    mkt_age_raw = _age_from_mixed_ts(
                        float(getattr(self, "_market_snapshot_mono_ts", 0.0) or 0.0),
                        float(now),
                        float(mono_now),
                    )
                except Exception:
                    mkt_age_raw = float("inf")
                if not math.isfinite(float(mkt_age_raw)):
                    try:
                        mkt_age_raw = _age_from_mixed_ts(
                            float(getattr(self, "_market_snapshot_local_ts", 0.0) or 0.0),
                            float(now),
                            float(mono_now),
                        )
                    except Exception:
                        mkt_age_raw = float("inf")
                top8_age_raw = float("inf")
                try:
                    ts_ok_mono = float(getattr(self, "_top8_ok_mono_ts", 0.0) or 0.0)
                    if ts_ok_mono > 0.0:
                        top8_age_raw = min(top8_age_raw, _age_from_mixed_ts(ts_ok_mono, float(now), float(mono_now)))
                except Exception:
                    pass
                try:
                    ts_ok = float(getattr(self, "_top8_ok_ts", 0.0) or 0.0)
                    if ts_ok > 0.0:
                        top8_age_raw = min(top8_age_raw, _age_from_mixed_ts(ts_ok, float(now), float(mono_now)))
                except Exception:
                    pass
                if not math.isfinite(float(top8_age_raw)):
                    try:
                        top8_age_raw = _age_from_mixed_ts(
                            float(getattr(self, "_top8_last_ts", 0.0) or 0.0),
                            float(now),
                            float(mono_now),
                        )
                    except Exception:
                        top8_age_raw = float("inf")
                radar_age_raw = float("inf")
                try:
                    scan_ts = float(getattr(self, "last_market_scan", 0.0) or 0.0)
                    if scan_ts <= 0.0:
                        scan_ts = float(getattr(self, "_focus_last_scan_ts", 0.0) or 0.0)
                    if scan_ts > 0.0:
                        radar_age_raw = min(radar_age_raw, _age_from_mixed_ts(scan_ts, float(now), float(mono_now)))
                except Exception:
                    pass
                try:
                    ok_ts = float(getattr(self, "_radar_ok_ts", 0.0) or 0.0)
                    if ok_ts > 0.0:
                        radar_age_raw = min(radar_age_raw, _age_from_mixed_ts(ok_ts, float(now), float(mono_now)))
                except Exception:
                    pass
                api_age_raw = float("inf")
                try:
                    pub = getattr(self, "public", None)
                    if pub is not None and hasattr(pub, "get_last_update_age"):
                        aa = pub.get_last_update_age()
                        try:
                            aa = float(aa)
                        except Exception:
                            aa = float("inf")
                        if math.isfinite(float(aa)):
                            if float(aa) > 1e9:
                                api_age_raw = _age_from_mixed_ts(float(aa), float(now), float(mono_now))
                            else:
                                if float(aa) > 1e6:  # ms -> sec
                                    aa = float(aa) / 1000.0
                                api_age_raw = max(0.0, float(aa))
                except Exception:
                    pass
                try:
                    if (not isinstance(api_age_raw, (int, float))) or (not math.isfinite(float(api_age_raw))):
                        api_age_raw = float("inf")
                except Exception:
                    api_age_raw = float("inf")
                if api_age_raw == float("inf"):
                    api_age_raw = _public_api_age(float(now))
                ema_mkt = _ema(ema_mkt, float(mkt_age_raw))
                ema_top8 = _ema(ema_top8, float(top8_age_raw))
                ema_radar = _ema(ema_radar, float(radar_age_raw))
                ema_api = _ema(ema_api, float(api_age_raw))
                try:
                    need_fast = int(_env_int("HEALTH_WD_FAST_RECOVER_GOOD_SAMPLES", 3) or 3)
                except Exception:
                    need_fast = 3
                try:
                    if math.isfinite(float(api_age_raw)) and float(api_age_raw) < float(api_warn):
                        g = int(getattr(self, "_hw_api_good_raw", 0) or 0) + 1
                        setattr(self, "_hw_api_good_raw", int(g))
                    else:
                        setattr(self, "_hw_api_good_raw", 0)
                except Exception:
                    pass
                try:
                    if int(getattr(self, "_hw_api_good_raw", 0) or 0) >= int(need_fast):
                        ema_api = float(api_age_raw)
                except Exception:
                    pass
                try:
                    if math.isfinite(float(radar_age_raw)) and float(radar_age_raw) < float(radar_warn):
                        g2 = int(getattr(self, "_hw_radar_good_raw", 0) or 0) + 1
                        setattr(self, "_hw_radar_good_raw", int(g2))
                    else:
                        setattr(self, "_hw_radar_good_raw", 0)
                except Exception:
                    pass
                try:
                    if int(getattr(self, "_hw_radar_good_raw", 0) or 0) >= int(need_fast):
                        ema_radar = float(radar_age_raw)
                except Exception:
                    pass
                def _is_na(age: float) -> bool:
                    """Missing semantics for subsystem ages.

                    """
                    try:
                        a = float(age)
                        return (not math.isfinite(a)) or (a < 0.0) or (a > 1e6)
                    except Exception:
                        return True
                def _age_ok(x):
                    try:
                        v = float(x)
                        if math.isfinite(v) and v >= 0.0:
                            return v
                    except Exception:
                        pass
                    return float("inf")
                subs_raw = {
                    "mkt": (float(_age_ok(mkt_age_raw)), float(mkt_warn), float(mkt_crit)),
                    "top8": (float(_age_ok(top8_age_raw)), float(top8_warn), float(top8_crit)),
                    "radar": (float(_age_ok(radar_age_raw)), float(radar_warn), float(radar_crit)),
                    "api": (float(_age_ok(api_age_raw)), float(api_warn), float(api_crit)),
                }
                subs_ema = {
                    "mkt": (float(_age_ok(ema_mkt)), float(mkt_warn), float(mkt_crit)),
                    "top8": (float(_age_ok(ema_top8)), float(top8_warn), float(top8_crit)),
                    "radar": (float(_age_ok(ema_radar)), float(radar_warn), float(radar_crit)),
                    "api": (float(_age_ok(ema_api)), float(api_warn), float(api_crit)),
                }
                api_pen_until = 0.0
                api_soft_na = False
                try:
                    api_pen_until = float(getattr(self, "_hw_api_burst_pen_until", 0.0) or 0.0)
                except Exception:
                    api_pen_until = 0.0
                def _compute_levels(_subs, *, update_burst: bool):
                    nonlocal api_pen_until, api_soft_na
                    _lv = {}
                    for k, (age, warn, crit) in _subs.items():
                        if _is_na(age):
                            if update_burst:
                                try:
                                    na_win[k].append(now)
                                except Exception:
                                    pass
                            b = _burst_count(k, now)
                            if k == "api" and b <= int(na_burst_max):
                                if update_burst:
                                    api_soft_na = True
                                    try:
                                        api_pen_until = max(float(api_pen_until or 0.0), float(now) + float(burst_pen))
                                        setattr(self, "_hw_api_burst_pen_until", float(api_pen_until))
                                    except Exception:
                                        pass
                                _lv[k] = "OK"
                            else:
                                if b <= int(na_burst_max):
                                    _lv[k] = "DEGRADED"
                                else:
                                    _lv[k] = "CRITICAL"
                                    if k == "api" and update_burst:
                                        try:
                                            setattr(self, "_hw_api_burst_pen_until", 0.0)
                                            api_pen_until = 0.0
                                        except Exception:
                                            pass
                        else:
                            _burst_count(k, now)
                            if float(age) >= float(crit):
                                _lv[k] = "CRITICAL"
                            elif float(age) >= float(warn):
                                _lv[k] = "DEGRADED"
                            else:
                                _lv[k] = "OK"
                    return _lv
                levels_raw = _compute_levels(subs_raw, update_burst=True)
                levels_ema = _compute_levels(subs_ema, update_burst=False)
                try:
                    if api_pen_until and float(now) >= float(api_pen_until):
                        setattr(self, "_hw_api_burst_pen_until", 0.0)
                        api_pen_until = 0.0
                except Exception:
                    pass
                levels_state = levels_ema
                levels_exec = levels_raw
                subs = subs_ema
                levels = levels_state
                try:
                    top8_aux_only = bool(_env_bool("HEALTH_WD_TOP8_AUX_ONLY", True))
                except Exception:
                    top8_aux_only = True
                try:
                    if bool(_env_bool("TERMUX_MODE", False)) and not bool(_env_bool("HEALTH_WD_TOP8_FORCE_EXEC", False)):
                        top8_aux_only = True
                except Exception:
                    pass
                aux_keys = set()
                if top8_aux_only:
                    aux_keys.add("top8")
                want_state_full = "OK"
                if "CRITICAL" in levels_state.values():
                    want_state_full = "CRITICAL"
                elif "DEGRADED" in levels_state.values():
                    want_state_full = "DEGRADED"
                want_exec_full = "OK"
                if "CRITICAL" in levels_exec.values():
                    want_exec_full = "CRITICAL"
                elif "DEGRADED" in levels_exec.values():
                    want_exec_full = "DEGRADED"
                want_state = "OK"
                for _k, _lvl in levels_state.items():
                    if _k in aux_keys:
                        continue
                    if _lvl == "CRITICAL":
                        want_state = "CRITICAL"
                        break
                if want_state != "CRITICAL":
                    for _k, _lvl in levels_state.items():
                        if _k in aux_keys:
                            continue
                        if _lvl == "DEGRADED":
                            want_state = "DEGRADED"
                            break
                want_exec = "OK"
                for _k, _lvl in levels_exec.items():
                    if _k in aux_keys:
                        continue
                    if _lvl == "CRITICAL":
                        want_exec = "CRITICAL"
                        break
                if want_exec != "CRITICAL":
                    for _k, _lvl in levels_exec.items():
                        if _k in aux_keys:
                            continue
                        if _lvl == "DEGRADED":
                            want_exec = "DEGRADED"
                            break
                want_full = want_state_full
                want = want_state
                exec_block = {"ts": float(now), "want_exec": str(want_exec), "cause": "", "level": "", "age_s": None, "warn": None, "crit": None}
                try:
                    sev = {"OK": 0, "DEGRADED": 1, "CRITICAL": 2}
                    best = None
                    best_sev = -1
                    best_age = -1.0
                    for kk, lvl in (levels_exec or {}).items():
                        if kk in aux_keys:
                            continue
                        s = int(sev.get(str(lvl), -1))
                        if s < 0:
                            continue
                        age, warn, crit = subs_raw.get(kk, (float("inf"), 0.0, 0.0))
                        a = float(age) if math.isfinite(float(age)) else float("inf")
                        if s > best_sev or (s == best_sev and a > best_age):
                            best = kk
                            best_sev = s
                            best_age = a
                    if best and best_sev > 0:
                        age, warn, crit = subs_raw.get(best, (None, None, None))
                        exec_block.update({
                            "cause": str(best),
                            "level": str(levels_exec.get(best)),
                            "age_s": (None if age is None or (not math.isfinite(float(age))) else float(age)),
                            "warn": (None if warn is None else float(warn)),
                            "crit": (None if crit is None else float(crit)),
                        })
                except Exception:
                    pass
                exec_nocrit = True
                try:
                    for _k, _lvl in levels_exec.items():
                        if _k in aux_keys:
                            continue
                        if _lvl == "CRITICAL":
                            exec_nocrit = False
                            break
                except Exception:
                    exec_nocrit = True
                try:
                    if exec_nocrit:
                        if float(getattr(self, "_hw_exec_nocrit_since", 0.0) or 0.0) <= 0.0:
                            setattr(self, "_hw_exec_nocrit_since", float(now))
                    else:
                        setattr(self, "_hw_exec_nocrit_since", 0.0)
                except Exception:
                    pass
                if state == "INIT" and want in ("OK", "DEGRADED"):
                    state = "OK"
                    since_ts = now
                if state in ("OK", "DEGRADED") and want == "CRITICAL":
                    if state != "CRITICAL":
                        state = "CRITICAL"
                        since_ts = now
                        last_crit_ts = now
                        good_streak = 0
                if state == "OK" and want == "DEGRADED":
                    state = "DEGRADED"
                    since_ts = now
                    good_streak = 0
                if state == "DEGRADED" and want == "OK":
                    if last_crit_ts > 0.0 and (now - last_crit_ts) < float(recovery_cooldown):
                        good_streak = 0
                    else:
                        good_streak += 1
                        if good_streak >= int(good_need):
                            state = "OK"
                            since_ts = now
                            good_streak = 0
                if state == "CRITICAL":
                    if want == "CRITICAL":
                        good_streak = 0
                        last_crit_ts = now
                    else:
                        if (now - last_crit_ts) < float(recovery_cooldown):
                            good_streak = 0
                        else:
                            good_streak += 1
                            if good_streak >= int(good_need):
                                state = "DEGRADED" if want == "DEGRADED" else "OK"
                                since_ts = now
                                good_streak = 0
                try:
                    force_sec = float(_env_float("HEALTH_WD_FORCE_RECOVER_NONCRIT_SEC", 12.0) or 12.0)
                except Exception:
                    force_sec = 12.0
                try:
                    nocrit_since = float(getattr(self, "_hw_exec_nocrit_since", 0.0) or 0.0)
                except Exception:
                    nocrit_since = 0.0
                try:
                    if state == "CRITICAL" and want in ("OK", "DEGRADED") and nocrit_since > 0.0 and (now - nocrit_since) >= float(force_sec):
                        state = ("DEGRADED" if want == "DEGRADED" else "OK")
                        since_ts = now
                        last_crit_ts = 0.0
                        good_streak = 0
                except Exception:
                    pass
                try:
                    if state == "CRITICAL" and bool(_env_bool("HEALTH_WD_HALT_ON_CRIT", False)):
                        state = "HALTED"
                        since_ts = now
                except Exception:
                    pass
                score = 100.0
                for k, (age, warn, crit) in subs_ema.items():
                    try:
                        if k in aux_keys and (not bool(_env_bool("HEALTH_WD_SCORE_INCLUDE_AUX", False))):
                            continue
                    except Exception:
                        pass
                    if levels_state.get(k) == "OK":
                        continue
                    if levels_state.get(k) == "DEGRADED":
                        score -= 12.0
                    else:
                        score -= 25.0
                    try:
                        if math.isfinite(age) and float(age) > float(warn):
                            score -= min(10.0, float(age) - float(warn)) * 0.5
                    except Exception:
                        pass
                try:
                    if api_pen_until and float(now) < float(api_pen_until):
                        soft_pts = float(max(3.0, min(15.0, float(burst_pen) * 0.5)))
                        score -= float(soft_pts)
                except Exception:
                    pass
                score = float(max(0.0, min(100.0, score)))
                prev = str(getattr(self, "_hw_state", "INIT") or "INIT").upper()
                if state != prev:
                    try:
                        msg = f"event=HEALTH_WD_STATE from={prev} to={state} score={score:.1f} mkt={fmt_age_s(ema_mkt)} top8={fmt_age_s(ema_top8)} radar={fmt_age_s(ema_radar)} api={fmt_age_s(ema_api)}"
                        scl.log("HEALTH_WD_STATE", (prev, state), "warning" if state in ("DEGRADED", "CRITICAL") else "info", msg)
                    except Exception:
                        pass
                try:
                    r = getattr(self, "risk", None)
                    if r is not None and hasattr(r, "set_safe"):
                        safe_tag = "HALTED" if state == "HALTED" else str(want_exec or "OK")
                        reason_line = f"HEALTH_SYS_{safe_tag} score={float(score):.1f} mkt={fmt_age_s(mkt_age_raw)} top8={fmt_age_s(top8_age_raw)} radar={fmt_age_s(radar_age_raw)} api={fmt_age_s(api_age_raw)}"
                        try:
                            safe_on_degraded = bool(_env_bool("HEALTH_WD_SAFE_ON_DEGRADED", False))
                        except Exception:
                            safe_on_degraded = False
                        if safe_tag == "OK":
                            try:
                                if bool(getattr(r, "safe_mode", False)) and str(getattr(r, "safe_reason", "") or "").startswith("HEALTH_SYS_"):
                                    r.set_safe(False, reason="HEALTH_SYS_RECOVER")
                            except Exception:
                                pass
                        elif safe_tag == "DEGRADED" and not safe_on_degraded:
                            try:
                                if bool(getattr(r, "safe_mode", False)) and str(getattr(r, "safe_reason", "") or "").startswith("HEALTH_SYS_"):
                                    r.set_safe(False, reason="HEALTH_SYS_DEGRADED_NO_SAFE")
                            except Exception:
                                pass
                        else:
                            try:
                                r.set_safe(True, reason=reason_line)
                            except Exception:
                                pass
                except Exception:
                    pass
                try:
                    setattr(self, "_engine_halted", bool(state == "HALTED"))
                except Exception:
                    pass
                reasons = {
                    "state": state,
                    "levels": dict(levels_raw), "levels_ema": dict(levels_ema),
                    "want_full": str(locals().get("want_full", "") or ""),
                    "aux_keys": sorted(list(locals().get("aux_keys", set()) or set())),
                    "mkt_ema_s": float(ema_mkt or 0.0),
                    "top8_ema_s": float(ema_top8 or 0.0),
                    "radar_ema_s": float(ema_radar or 0.0),
                    "api_ema_s": float(ema_api or 0.0),
                    "api_burst_pen_until": float(api_pen_until or 0.0),
                    "api_burst_pen_active": bool(api_pen_until and float(now) < float(api_pen_until)),
                    "api_soft_na": bool(api_soft_na),
                    "mkt_burst": int(_burst_count("mkt", now)),
                    "top8_burst": int(_burst_count("top8", now)),
                    "radar_burst": int(_burst_count("radar", now)),
                    "api_burst": int(_burst_count("api", now)),
                }
                try:
                    setattr(self, "_hw_state", str(state))
                    try:
                        setattr(self, "_hw_want_exec", str(want_exec))
                        setattr(self, "_hw_want_full", str(want_state_full))
                        setattr(self, "_hw_want_state", str(want_state))
                        setattr(self, "_hw_want_exec_full", str(want_exec_full))
                        setattr(self, "_hw_levels", dict(levels_raw))
                        setattr(self, "_hw_levels_ema", dict(levels_ema))
                        setattr(self, "_hw_exec_block", dict(exec_block))
                        try:
                            setattr(self, "_hw_ages_raw", {str(k): float(v[0]) for k, v in (subs_raw or {}).items() if isinstance(v, (tuple, list)) and v})
                            setattr(self, "_hw_ages_ema", {str(k): float(v[0]) for k, v in (subs_ema or {}).items() if isinstance(v, (tuple, list)) and v})
                        except Exception:
                            pass
                        setattr(self, "_hw_thr", {
                            "mkt": {"warn": float(mkt_warn), "crit": float(mkt_crit)},
                            "top8": {"warn": float(top8_warn), "crit": float(top8_crit)},
                            "radar": {"warn": float(radar_warn), "crit": float(radar_crit)},
                            "api": {"warn": float(api_warn), "crit": float(api_crit)},
                        })
                        try:
                            setattr(self, "_hw_thresholds", {
                                "mkt_warn": float(mkt_warn), "mkt_crit": float(mkt_crit),
                                "top8_warn": float(top8_warn), "top8_crit": float(top8_crit),
                                "radar_warn": float(radar_warn), "radar_crit": float(radar_crit),
                                "api_warn": float(api_warn), "api_crit": float(api_crit),
                            })
                        except Exception:
                            pass
                    except Exception:
                        pass
                    setattr(self, "_hw_since_ts", float(since_ts))
                    setattr(self, "_hw_score", float(score))
                    setattr(self, "_hw_reasons", dict(reasons))
                    setattr(self, "_hw_last_ts", float(now))
                    setattr(self, "_hw_na_win", na_win)
                    setattr(self, "_hw_last_crit_ts", float(last_crit_ts))
                    setattr(self, "_hw_good_streak", int(good_streak))
                except Exception:
                    pass
                try:
                    st = getattr(self, "_mkt_store", None)
                    if st is not None and hasattr(st, "set_subsys"):
                        st.set_subsys(
                            "health",
                            last_update_ts=float(now),
                            state=str(state),
                            score=float(score),
                            levels=dict(levels_raw), levels_ema=dict(levels_ema),
                            mkt_age=(float(mkt_age_raw) if (mkt_age_raw is not None and math.isfinite(float(mkt_age_raw))) else float("inf")),
                            top8_age=(float(top8_age_raw) if (top8_age_raw is not None and math.isfinite(float(top8_age_raw))) else float("inf")),
                            radar_age=(float(radar_age_raw) if (radar_age_raw is not None and math.isfinite(float(radar_age_raw))) else float("inf")),
                            api_age=(float(api_age_raw) if (api_age_raw is not None and math.isfinite(float(api_age_raw))) else float("inf")),
                            mkt_age_ema=(float(ema_mkt) if (ema_mkt is not None and math.isfinite(float(ema_mkt))) else float("inf")),
                            top8_age_ema=(float(ema_top8) if (ema_top8 is not None and math.isfinite(float(ema_top8))) else float("inf")),
                            radar_age_ema=(float(ema_radar) if (ema_radar is not None and math.isfinite(float(ema_radar))) else float("inf")),
                            api_age_ema=(float(ema_api) if (ema_api is not None and math.isfinite(float(ema_api))) else float("inf")),
                        )
                except Exception:
                    pass
                try:
                    tick_sec = float(_env_float("HEALTH_WD_TICK_LOG_SEC", 12.0) or 12.0)
                except Exception:
                    tick_sec = 12.0
                tick_sec = float(max(3.0, min(120.0, tick_sec)))
                try:
                    last_tick = float(getattr(self, "_hw_last_tick_log_ts", 0.0) or 0.0)
                except Exception:
                    last_tick = 0.0
                do_tick = False
                try:
                    r0 = getattr(self, "risk", None)
                    safe_on = bool(getattr(r0, "safe_mode", False)) if r0 is not None else False
                except Exception:
                    safe_on = False
                if state in ("DEGRADED", "CRITICAL", "HALTED") or safe_on:
                    if (last_tick <= 0.0) or ((now - last_tick) >= tick_sec):
                        do_tick = True
                if do_tick:
                    try:
                        setattr(self, "_hw_last_tick_log_ts", float(now))
                    except Exception:
                        pass
                    try:
                        log = getattr(self, "_log", logging.getLogger(__name__))
                        msg = f"HEALTH_SYS_{state} score={float(score):.1f} mkt={fmt_age_s(ema_mkt)} top8={fmt_age_s(ema_top8)} radar={fmt_age_s(ema_radar)} api={fmt_age_s(ema_api)}"
                        if state in ("DEGRADED", "CRITICAL"):
                            log.warning(msg)
                        elif state == "HALTED":
                            log.critical(msg)
                        else:
                            log.info(msg)
                    except Exception:
                        pass
                await _sleep_or_stop(stop_ev, interval)
        internal_tasks = self._ensure_internal_services_started(stop_ev)
        watch_tasks: List[asyncio.Task] = []
        hb_syms: List[str] = []
        try:
            watch_symbols, hb_syms = await _build_watch_symbols()
        except Exception:
            watch_symbols, hb_syms = (["BTCIRT", "USDTIRT", "ETHIRT", "PAXGIRT"], ["BTCIRT", "USDTIRT"])
        try:
            top8_stale = float(_env_float("TOP8_STALE_AFTER_SEC", 60.0) or 60.0)
        except Exception:
            top8_stale = 60.0
        try:
            top8_poll = float(_env_float("TOP8_POLL_INTERVAL_SEC", 2.0) or 2.0)
        except Exception:
            top8_poll = 2.0
        try:
            top8_to = float(_env_float("TOP8_HTTP_TIMEOUT_SEC", 12.0) or 12.0)
        except Exception:
            top8_to = 12.0
        try:
            top8_grace = float(_env_float("TOP8_GRACE_SEC", 20.0) or 20.0)
        except Exception:
            top8_grace = 20.0
        try:
            if not bool(getattr(self, "_cold_boot_recovered", False)):
                setattr(self, "_cold_boot_recovered", True)
                wallets0 = list((getattr(self, "wallets", {}) or {}).values())
                for w in wallets0:
                    if stop_ev.is_set() or bool(getattr(self, "_global_exit_fired", False)):
                        break
                    try:
                        _wdu = float(getattr(w, "_balance_disabled_until", 0.0) or 0.0)
                        _now = time.time()
                        if _wdu > _now:
                            try:
                                self._log.warning(
                                    "event=WALLET_BALANCE_COOLDOWN wallet=%s phase=cold_boot retry_in=%.1f fail_count=%s",
                                    getattr(w, "name", "?"),
                                    float(_wdu - _now),
                                    int(getattr(w, "_balance_fail_count", 0) or 0),
                                )
                            except Exception:
                                pass
                        else:
                            await self._refresh_balance_if_needed(w)
                            try:
                                setattr(w, "_balance_fail_count", 0)
                                setattr(w, "_balance_disabled_until", 0.0)
                            except Exception:
                                pass
                    except Exception as e:
                        try:
                            _fc = int(getattr(w, "_balance_fail_count", 0) or 0) + 1
                            setattr(w, "_balance_fail_count", _fc)
                            setattr(w, "_balance_disabled_until", time.time() + 120.0)
                        except Exception:
                            _fc = int(getattr(w, "_balance_fail_count", 0) or 0)
                        try:
                            self._log.warning(
                                "event=WALLET_ISOLATED wallet=%s phase=cold_boot_balance reason=%s fail_count=%s cooldown_sec=120",
                                getattr(w, "name", "?"),
                                str(e),
                                _fc,
                            )
                        except Exception:
                            pass
                    try:
                        await self._refresh_orders_if_needed(w)
                    except Exception:
                        pass
                    try:
                        snap_assets = (getattr(w, "assets_total_snapshot", None) or getattr(w, "assets_snapshot", None) or {})
                        quote0 = str(getattr(getattr(self, "cfg", None), "quote", "IRT") or "IRT").upper().strip() or "IRT"
                        if isinstance(snap_assets, dict):
                            posd = getattr(w, "positions", None)
                            if posd is None or not isinstance(posd, dict):
                                try:
                                    w.positions = {}
                                except Exception:
                                    posd = None
                                else:
                                    posd = w.positions
                            for a, amt in list(snap_assets.items()):
                                a0 = str(a or "").upper().strip()
                                if not a0 or a0 in {"IRT", "IRR", "TMN", "TOMAN", quote0}:
                                    continue
                                try:
                                    q = float(amt or 0.0)
                                except Exception:
                                    continue
                                if (not math.isfinite(q)) or q <= 0.0:
                                    continue
                                try:
                                    sym0 = _canon_pair(a0, quote0)
                                except Exception:
                                    sym0 = a0 + quote0
                                if not sym0:
                                    continue
                                if posd is None:
                                    continue
                                if sym0 in posd:
                                    continue
                                try:
                                    posd[sym0] = Position(symbol=sym0, qty=float(q), entry_px=0.0, entry_ts=0.0)
                                except Exception:
                                    pass
                    except Exception:
                        pass
                try:
                    self._save_state_if_needed(force=True)
                except Exception:
                    pass
        except Exception as e:
            if isinstance(e, TradingHalt): raise
        try:
            watcher = Top8WatcherService(
                self,
                watch_symbols,
                stale_after_sec=float(max(6.0, min(180.0, top8_stale))),
                poll_interval_sec=float(max(0.6, min(20.0, top8_poll))),
                timeout_sec=float(max(2.0, min(25.0, top8_to))),
                grace_sec=float(max(5.0, min(180.0, top8_grace))),
                logger=self._log,
            )
            watch_tasks = watcher.start(stop_ev)
        except Exception:
            watch_tasks = []
        tasks: List[asyncio.Task] = [
            asyncio.create_task(_exec_loop(), name="rtp_exec_loop"),
            asyncio.create_task(_cleanup_loop(), name="rtp_cleanup_loop"),
            asyncio.create_task(_dashboard_loop(), name="rtp_dashboard_loop"),
            asyncio.create_task(_market_heartbeat_loop(hb_syms), name="rtp_market_heartbeat"),
            asyncio.create_task(_health_watchdog_loop(), name="rtp_health_watchdog"),
        ] + (watch_tasks or []) + (internal_tasks or [])
        try:
            done, pending = await asyncio.wait(set(tasks), return_when=asyncio.FIRST_EXCEPTION)
            for t in done:
                try:
                    exc = t.exception()
                except Exception:
                    exc = None
                if exc:
                    try:
                        self._log.error("event=BOT_LOOP_TASK_FAIL task=%s err=%s", getattr(t, "get_name", lambda: "?")(), exc)
                    except Exception:
                        pass
                    break
        finally:
            try:
                stop_ev.set()
            except Exception:
                pass
            for t in tasks:
                try:
                    t.cancel()
                except Exception:
                    pass
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception:
                pass
            try:
                if dash is not None and hasattr(dash, "stop"):
                    dash.stop()
            except Exception:
                pass
            try:
                WalletRuntime._flush_last_known_prices(force=True)
            except Exception:
                pass
            try:
                self._save_state_if_needed(force=True)
            except Exception:
                pass
            try:
                if bool(getattr(self, "_hw_restart_requested", False)) and bool(_env_bool("HEALTH_WD_SELF_RESTART", True)):
                    try:
                        await asyncio.sleep(float(_env_float("HEALTH_WD_SELF_RESTART_SLEEP_SEC", 2.0) or 2.0))
                    except Exception:
                        pass
                    try:
                        self._log.critical(
                            "event=HEALTH_WD_SELF_RESTART execv=1 reason=%s",
                            str(getattr(self, "_hw_restart_reason", "") or "")[:80],
                        )
                    except Exception:
                        pass
                    try:
                        os.execv(sys.executable, [sys.executable] + list(sys.argv))
                    except Exception:
                        pass
            except Exception:
                pass