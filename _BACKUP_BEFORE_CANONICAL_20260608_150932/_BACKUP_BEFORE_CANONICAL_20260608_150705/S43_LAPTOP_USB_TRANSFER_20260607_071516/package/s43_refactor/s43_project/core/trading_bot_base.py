from .market_specs_cache import MarketSpecsCache
from .global_exit_guard import GlobalExitGuard
from .execution_engine import ExecutionEngine
from .alpha_model import AlphaModel
from .risk_manager import RiskManager
from .dzh_ban_integrity import DzhBanIntegrity
from .order_journal import OrderJournal
from .trading_policy import TradingPolicy
from .market_snapshot_store import MarketSnapshotStore
from .logger import Logger
from .sovereign_engine import SovereignEngine
from .clock_arbiter import ClockArbiter
from .trade_health_controller import TradeHealthController
from .api_http_error import ApiHttpError
from .phoenix_engine import PhoenixEngine
from .order_normalizer import OrderNormalizer
from .trade_health import TradeHealth
from .shared_async_rate_limiter import SharedAsyncRateLimiter
from .exchange_client import ExchangeClient
from .soft_symbol_blacklist import SoftSymbolBlacklist
from .signal import Signal
from .decision_cortex import DecisionCortex
from .net_health_monitor import NetHealthMonitor
from .circuit_breaker import CircuitBreaker
from .bot_config import BotConfig
from .trading_bot import TradingBot
from .sanity_halt_controller import SanityHaltController
from .position import Position
from .data_feed import DataFeed
from .tick_recorder import TickRecorder
from .api_error import ApiError
from .order_book_service import OrderBookService
from .wallet_runtime import WalletRuntime
from .advanced_analytics_engine import AdvancedAnalyticsEngine
from .async_rate_limiter import AsyncRateLimiter

class TradingBotBase:
    def __init__(self, cfg: BotConfig, logger: Logger):
        self.cfg = cfg
        self.logger = logger
        self._log = logger.log
        self.engine_status = 'Hold'
        self.last_reason = 'Wait_X'
        self._engine_ts = float(time.time())
        try:
            st = globals().get('_V167_STATE')
            if isinstance(st, dict):
                st['BOT'] = self
        except Exception:
            pass
        if cfg.quote != "IRT":
            raise ValueError("Only IRT quote is supported in this build.")
        self._limiter = SharedAsyncRateLimiter(cfg.rate_limit_per_min)
        self._breaker = CircuitBreaker(cfg.circuit_breaker_errors, cfg.circuit_breaker_cooldown_sec, self._log)
        self.public = ExchangeClient(cfg, token="", limiter=self._limiter, logger=self._log, breaker=self._breaker)
        self.specs = MarketSpecsCache(self.public, self._log)
        self.norm = OrderNormalizer(self.specs)
        self.recorder: Optional[TickRecorder] = None
        if cfg.record_ticks:
            self.recorder = TickRecorder(cfg.record_db_path, timeout_sec=cfg.sqlite_timeout_sec, logger=self._log)
            self._log.warning("Tick recording ENABLED db=%s", cfg.record_db_path)
        self.risk = RiskManager(cfg, self._log)
        self.phoenix = PhoenixEngine(cfg, self._log)
        self.sanity = SanityHaltController(cfg, self._log)
        self.orders = OrderJournal(cfg, self._log)
        self._last_temp_pause_log_ts = 0.0
        try:
            self._secure_store = _get_secure_token_store()
        except Exception:
            self._secure_store = None
        try:
            self._token_monitor = TokenExpiryMonitor(self._secure_store, warn_days=int(_env_int("TOKEN_WARN_DAYS", 3))) if self._secure_store else None
        except Exception:
            self._token_monitor = None
        try:
            self._ai_trader = AITrader(logger=self._log) if _env_bool("AI_TRADER_ENABLE", True) else None
        except Exception:
            self._ai_trader = None
        try:
            self.perf_monitor = PerfHealthMonitor(logger=self._log) if _env_bool("PERF_MONITOR_ENABLE", True) else None
        except Exception:
            self.perf_monitor = None
        self._autonomy_last_token_refresh_ts = 0.0
        self._autonomy_last_perf_tick_ts = 0.0
        self._bot_state_path = os.getenv("BOT_STATE_PATH", "bot_state.json")
        self._bot_state_last_save_ts = 0.0
        self._bot_state_last_hash = ""
        self.wallets: Dict[str, WalletRuntime] = {}
        slots = set()
        for _s in (cfg.wallet_slots or [1]):
            try:
                slots.add(int(_s))
            except Exception:
                continue
        for _k, _v in (HARDCODED_WALLET_TOKENS or {}).items():
            try:
                if str(_v).strip():
                    slots.add(int(_k))
            except Exception:
                continue
        for slot in sorted(slots or {1}):
            token = get_arzplus_token(slot)
            wname = f"W{slot}"
            if token:
                self._log.info("event=WALLET_TOKEN_OK wallet=%s len=%d", wname, len(str(token)))
            else:
                self._log.warning("event=WALLET_TOKEN_MISSING wallet=%s", wname)
            token_expiry_ts = 0
            try:
                token_expiry_ts = int(get_arzplus_token_expiry_ts(slot) or 0)
            except Exception:
                token_expiry_ts = 0
            wallet_disabled = False
            wallet_disable_reason = ""
            now_ts = float(time.time())
            if token_expiry_ts and float(token_expiry_ts) <= now_ts:
                wallet_disabled = True
                wallet_disable_reason = "TOKEN_EXPIRED"
                token = ""
            if not token:
                wallet_disabled = True
                wallet_disable_reason = wallet_disable_reason or "TOKEN_MISSING"
            if wallet_disabled:
                try:
                    self._log.warning("event=WALLET_DISABLED wallet=%s reason=%s expiry_ts=%s", wname, wallet_disable_reason, str(token_expiry_ts))
                except Exception:
                    pass
            else:
                try:
                    self._log.info("event=WALLET_ENABLED wallet=%s expiry_ts=%s", wname, str(token_expiry_ts))
                except Exception:
                    pass
            w_symbols_env = _env_str(f"WALLET_{slot}_SYMBOLS", "")
            w_symbols = ([_canon_pair(s, cfg.quote) for s in w_symbols_env.split(",") if str(s).strip()]
                         if w_symbols_env else list(cfg.symbols or []))
            w_pri_env = _env_str(f"WALLET_{slot}_SYMBOL_PRIORITY", "")
            w_priority = ([_canon_pair(s, cfg.quote) for s in w_pri_env.split(",") if str(s).strip()]
                          if w_pri_env else list(cfg.symbol_priority or []))
            w_max_pos = _env_int(f"WALLET_{slot}_MAX_OPEN_POSITIONS", int(getattr(cfg, "max_open_positions", 0) or 0))
            w_max_frac = _env_float(f"WALLET_{slot}_MAX_NOTIONAL_FRAC", float(getattr(cfg, "max_notional_frac", 0.0) or 0.0))
            w_min_profit = _env_float(f"WALLET_{slot}_MIN_NET_PROFIT_IRT", float(getattr(cfg, "min_net_profit_irt", 0.0) or 0.0))
            w_ci = _env_bool(f"WALLET_{slot}_COLLECTIVE_INTELLIGENCE", bool(getattr(cfg, "collective_intelligence", False)))
            w_aut = _env_bool(f"WALLET_{slot}_AUTONOMOUS_AI", bool(getattr(cfg, "autonomous_ai", False)))
            w_idem_ttl = _env_float(f"WALLET_{slot}_IDEMPOTENCY_TTL_SEC", float(getattr(cfg, "idempotency_ttl_sec", 0.0) or 0.0))
            wcfg = __import__("dataclasses").replace(
                cfg,
                symbols=w_symbols,
                symbol_priority=w_priority,
                max_open_positions=w_max_pos,
                max_notional_frac=w_max_frac,
                min_net_profit_irt=w_min_profit,
                collective_intelligence=w_ci,
                autonomous_ai=w_aut,
                idempotency_ttl_sec=w_idem_ttl,
            )
            ex = ExchangeClient(wcfg, token=token or "DUMMY", limiter=self._limiter, logger=self._log, breaker=self._breaker)
            alpha = AlphaModel(wcfg)
            cortex = DecisionCortex(wcfg, self._log)
            exec_engine = ExecutionEngine(
                wcfg, ex, self.norm, self._log,
                recorder=self.recorder,
                wallet_name=wname,
                order_journal=self.orders,
            )
            try:
                exec_engine._risk = self.risk
            except Exception:
                pass
            wr = WalletRuntime(
                slot=slot,
                name=wname,
                cfg=wcfg,
                ex=ex,
                exec=exec_engine,
                alpha=alpha,
                cortex=cortex,
            )
            self.wallets[wname] = wr
            try:
                wr.token_expiry_ts = float(token_expiry_ts or 0)
                wr.wallet_disabled = bool(wallet_disabled)
                wr.wallet_disable_reason = str(wallet_disable_reason or "")
            except Exception:
                pass
        try:
            self._load_bot_state()
        except Exception:
            pass
        self.supported_symbols: Dict[str, float] = {}
        self.last_market_scan: float = 0.0
        self._focus_prev_symbols: List[str] = []
        self._focus_scores: Dict[str, float] = {}
        self._focus_last_scan_ts: float = 0.0
        self._focus_risk_weights: Dict[str, float] = {}
        self._focus_whale_active: Dict[str, bool] = {}
        self._whale_monitor = SovereignEngine.InvariantMonitor()
        self._mkt_store = MarketSnapshotStore(self._log)
        self.trade_policy = TradingPolicy(self)
        self._market_snapshot: Dict[str, dict] = {}
        self._market_server_time: float = 0.0
        self._market_snapshot_local_ts: float = 0.0
        self._market_age_s: float = 0.0
        self.feed = DataFeed(self.public, self._log, ttl_sec=cfg.depth_cache_ttl_sec, price_cache_path=cfg.price_cache_path)
        try:
            self.clock_arbiter = ClockArbiter(ema_alpha=float(getattr(cfg, "skew_ema_alpha", 0.12) or 0.12))
        except Exception:
            self.clock_arbiter = ClockArbiter()
        try:
            thr = float(getattr(cfg, "market_age_skip_sec", 4.0) or 4.0)
            self.health_mkt_thr = float(os.getenv("HEALTH_MKT_MAX_AGE_SEC", "15") or 15.0)
            health_book_thr = float(os.getenv("HEALTH_BOOK_MAX_AGE_SEC", str(thr)) or float(thr))
            try:
                health_mkt_thr = max(float(thr), float(health_mkt_thr))
            except Exception:
                health_mkt_thr = float(thr)
            try:
                health_book_thr = max(1.0, float(health_book_thr))
            except Exception:
                health_book_thr = float(thr)
            health_ctrl = TradeHealthController(
                market_thr_s=float(health_mkt_thr),
                book_thr_s=float(health_book_thr),
                skew_soft_s=float(getattr(cfg, "skew_soft_sec", 8.0) or 8.0),
                skew_degraded_s=float(getattr(cfg, "skew_degraded_sec", 20.0) or 20.0),
                skew_halt_s=float(getattr(cfg, "skew_halt_sec", 60.0) or 60.0),
            )
            self.health_ctrl = health_ctrl
        except Exception:
            self.health_ctrl = TradeHealthController()
        try:
            self.obsvc = OrderBookService(self.feed, self._log)
        except Exception:
            self.obsvc = None
        self.advanced_analytics: Optional[AdvancedAnalyticsEngine] = None
        try:
            if bool(getattr(self.cfg, "advanced_analytics_enabled", True)):
                self.advanced_analytics = AdvancedAnalyticsEngine(self.cfg, self._log, self.feed)
                self._log.info("Advanced Analytics Engine: ENABLED")
        except Exception as e:
            self._log.error("Advanced Analytics Engine init failed: %s", e)
            self.advanced_analytics = None
        self._global_exit_fired = False
        self._flash_last_check_ts = 0.0
        self.global_exit = GlobalExitGuard(cfg, self._log)
        self.net = NetHealthMonitor(cfg, self._log)
        self.soft_blacklist = SoftSymbolBlacklist(cfg, self._log)
        self._top8_snapshot: List[dict] = []
        self._top8_start_mid: Dict[str, float] = {}
        self._top8_last_ts: float = 0.0
        self.dzh = DzhBanIntegrity(cfg, self._log)
        self._last_state_save = 0.0
        self._load_state()
        self._idem: Dict[Tuple[str, str, str], float] = {}
    def _bot_state_snapshot(self) -> dict:
        st = {
            "ts": time.time(),
            "armed": (os.environ.get("ARZPLUS_LIVE_ARMED") == "YES"),
            "last_order_ts": float(_TERMUX_LAST_ORDER_TS or 0.0),
            "wallets": {},
        }
        for wn, w in (getattr(self, "wallets", {}) or {}).items():
            pos_out = {}
            for sym, p in (getattr(w, "positions", {}) or {}).items():
                try:
                    pos_out[str(sym)] = {
                        "qty": float(getattr(p, "qty", 0.0) or 0.0),
                        "entry_px": float(getattr(p, "entry_px", 0.0) or 0.0),
                        "entry_ts": float(getattr(p, "entry_ts", 0.0) or 0.0),
                    }
                except Exception:
                    continue
            st["wallets"][str(wn)] = {
                "last_engine_status": str(getattr(w, "last_engine_status", "") or ""),
                "last_engine_reason": str(getattr(w, "last_engine_reason", "") or ""),
                "positions": pos_out,
            }
        return st
    def _save_bot_state(self, *, force: bool = False) -> None:
        path = str(getattr(self, "_bot_state_path", "") or "").strip()
        if not path:
            return
        now = float(time.time())
        every = float(_env_float("BOT_STATE_SAVE_EVERY_SEC", 15.0) or 15.0)
        last = float(getattr(self, "_bot_state_last_save_ts", 0.0) or 0.0)
        if (not force) and (now - last) < every:
            return
        snap = self._bot_state_snapshot()
        try:
            h = hashlib.sha256(
                json.dumps(snap, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
            ).hexdigest()
        except Exception:
            h = ""
        prev_h = str(getattr(self, "_bot_state_last_hash", "") or "")
        if (not force) and h and (h == prev_h):
            try:
                setattr(self, "_bot_state_last_save_ts", now)
            except Exception:
                pass
            return
        _atomic_write_json(path, snap, fsync=True)
        try:
            setattr(self, "_bot_state_last_save_ts", now)
        except Exception:
            pass
        if h:
            try:
                setattr(self, "_bot_state_last_hash", h)
            except Exception:
                pass
    def _load_bot_state(self) -> None:
        path = str(getattr(self, "_bot_state_path", "") or "").strip()
        if (not path) or (not os.path.exists(path)):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return
        if not isinstance(data, dict):
            return
        try:
            lo = float(data.get("last_order_ts", 0.0) or 0.0)
            if lo > 0.0 and math.isfinite(lo):
                global _TERMUX_LAST_ORDER_TS
                _TERMUX_LAST_ORDER_TS = float(lo)
        except Exception:
            pass
        wmap = data.get("wallets", {})
        if not isinstance(wmap, dict):
            return
        for wn, ws in wmap.items():
            if not isinstance(ws, dict):
                continue
            w = (getattr(self, "wallets", {}) or {}).get(str(wn))
            if w is None:
                continue
            try:
                if not str(getattr(w, "last_engine_status", "") or ""):
                    setattr(w, "last_engine_status", str(ws.get("last_engine_status", "") or ""))
                if not str(getattr(w, "last_engine_reason", "") or ""):
                    setattr(w, "last_engine_reason", str(ws.get("last_engine_reason", "") or ""))
            except Exception:
                pass
            try:
                curp = getattr(w, "positions", {}) or {}
                if curp:
                    continue
            except Exception:
                pass
            pmap = ws.get("positions", {})
            if not isinstance(pmap, dict):
                continue
            outp = {}
            for sym, ps in pmap.items():
                if not isinstance(ps, dict):
                    continue
                try:
                    qty = float(ps.get("qty", 0.0) or 0.0)
                    if qty <= 0.0:
                        continue
                    outp[str(sym)] = Position(
                        symbol=str(sym),
                        qty=float(qty),
                        entry_px=float(ps.get("entry_px", 0.0) or 0.0),
                        entry_ts=float(ps.get("entry_ts", 0.0) or 0.0),
                    )
                except Exception:
                    continue
            try:
                setattr(w, "positions", outp)
            except Exception:
                pass
    def snapshot(self) -> dict:
        now = float(time.time())
        out: dict = {"wallets": {}}
        try:
            mem_mb = float(_rss_mb(int(os.getpid())))
        except Exception:
            mem_mb = None
        try:
            uptime = max(0.0, now - float(_BOOT_TS))
        except Exception:
            uptime = 0.0
        market_age = None
        try:
            mts_m = float(getattr(self, "_market_snapshot_mono_ts", 0.0) or 0.0)
        except Exception:
            mts_m = 0.0
        try:
            if mts_m > 0.0:
                market_age = max(0.0, float(time.monotonic()) - float(mts_m))
            else:
                ts = float(getattr(self, "_market_snapshot_local_ts", 0.0) or 0.0)
                if ts > 1e11:
                    ts = ts / 1000.0
                if ts > 0.0:
                    market_age = max(0.0, now - ts)
        except Exception:
            market_age = None
        market_skew = None
        try:
            ma = float(getattr(self, "_market_age_s", float("inf")))
            if math.isfinite(ma):
                market_skew = ma
        except Exception:
            market_skew = None
        api_age = None
        try:
            aa = float(self.public.get_last_update_age())
            if math.isfinite(aa):
                api_age = aa
        except Exception:
            api_age = None
        try:
            counts = {}
            for _n, _w in ((getattr(self, "wallets", {}) or {}).items()):
                try:
                    sigs = getattr(getattr(_w, "alpha", None), "_last_signals", {}) or {}
                    for _s, _sig in (sigs or {}).items():
                        if isinstance(_sig, Signal):
                            meta = getattr(_sig, "meta", {}) or {}
                            rg = str(meta.get("regime") or "").upper().strip()
                            if rg:
                                counts[rg] = int(counts.get(rg, 0)) + 1
                except Exception:
                    pass
            if counts:
                self._market_regime = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[0][0]
            else:
                self._market_regime = str(getattr(self, "_market_regime", "") or "")
        except Exception:
            self._market_regime = str(getattr(self, "_market_regime", "") or "")
        try:
            g = 0
            for _n, _w in ((getattr(self, "wallets", {}) or {}).items()):
                try:
                    g += int(getattr(getattr(_w, "exec", None), "ghost_order_count", 0) or 0)
                except Exception:
                    pass
            self._ghost_orders_total = int(g)
        except Exception:
            self._ghost_orders_total = int(getattr(self, "_ghost_orders_total", 0) or 0)
        try:
            safe_mode = bool(getattr(self.risk, "safe_mode", False))
            safe_reason = str(getattr(self.risk, "safe_reason", "") or "")
        except Exception:
            safe_mode, safe_reason = False, ""
        out["system"] = {
            "ts": now,
            "pid": int(os.getpid()),
            "mode": ("LIVE" if _env_bool("LIVE_TRADING", True) else "PAPER"),
            "uptime_sec": uptime,
            "cycle_count": int(getattr(self, "_cycle_count", 0) or 0),
            "last_cycle_ms": (float(getattr(self, "_last_cycle_ms", 0.0) or 0.0) if hasattr(self, "_last_cycle_ms") else None),
            "mem_rss_mb": mem_mb,
            "market_age_sec": market_age,
            "market_clock_skew_sec": market_skew,
            "api_age_sec": api_age,
            "market_confidence": float(getattr(self, "_snap_confidence", 100.0) or 0.0),
            "market_state": str(getattr(self, "_snap_state", "OK") or "OK"),
            "market_source": str(getattr(self, "_snap_source", "") or ""),
            "safe_mode": safe_mode,
            "safe_reason": safe_reason,
        }
        try:
            safe_level = str(self.risk.safe_level())
        except Exception:
            safe_level = ("HARD" if safe_mode else "OFF")
        try:
            daily_loss = float(getattr(self.risk, "daily_loss_irt", 0.0) or 0.0)
        except Exception:
            daily_loss = 0.0
        blocked_syms = 0
        try:
            bu = getattr(self.risk, "blocked_until", {}) or {}
            if isinstance(bu, dict):
                for _k, until_ts in bu.items():
                    try:
                        if float(until_ts or 0.0) > now:
                            blocked_syms += 1
                    except Exception:
                        pass
        except Exception:
            blocked_syms = 0
        out["risk"] = {
            "safe_level": safe_level,
            "daily_loss_irt": daily_loss,
            "blocked_symbols": int(blocked_syms),
        }
        try:
            syms_obj = getattr(self, "supported_symbols", {}) or {}
            if isinstance(syms_obj, dict):
                syms_list = list(syms_obj.keys())
                weights = {k: float(v) for k, v in syms_obj.items()}
            else:
                syms_list = list(syms_obj or [])
                weights = {k: float(v) for k, v in (getattr(self, "_focus_risk_weights", {}) or {}).items()}
            scan_ts = float(getattr(self, "last_market_scan", 0.0) or 0.0)
            if scan_ts <= 0.0:
                scan_ts = float(getattr(self, "_focus_last_scan_ts", 0.0) or 0.0)
            scan_ts = scan_ts / 1000.0 if scan_ts and scan_ts > 1e11 else scan_ts
            api_age2 = float("inf")
            try:
                api_age2 = float(self.public.get_last_update_age())
            except Exception:
                try:
                    ts_api = None
                    if getattr(self, "public", None) is not None:
                        for k in ("last_update_time", "last_update_ts", "_last_update_ts", "_last_public_update_ts", "last_ts", "_last_ts"):
                            if hasattr(self.public, k):
                                ts_api = getattr(self.public, k)
                                break
                    if ts_api is None:
                        ts_api = getattr(self, "_last_public_update_ts", None)
                    if ts_api is not None:
                        ts_api = float(ts_api or 0.0)
                        ts_api = ts_api / 1000.0 if ts_api and ts_api > 1e11 else ts_api
                        api_age2 = max(0.0, float(now) - ts_api)
                except Exception:
                    api_age2 = float("inf")
            scan_age = None
            try:
                if scan_ts > 0.0:
                    scan_age = max(0.0, now - scan_ts)
            except Exception:
                scan_age = None
            market_snap_age = None
            try:
                mts_m2 = float(getattr(self, "_market_snapshot_mono_ts", 0.0) or 0.0)
            except Exception:
                mts_m2 = 0.0
            try:
                if mts_m2 > 0.0:
                    market_snap_age = max(0.0, float(time.monotonic()) - float(mts_m2))
                else:
                    ts2 = float(getattr(self, "_market_snapshot_local_ts", 0.0) or 0.0)
                    if ts2 > 1e11:
                        ts2 = ts2 / 1000.0
                    if ts2 > 0.0:
                        market_snap_age = max(0.0, now - ts2)
            except Exception:
                market_snap_age = None
            mkt_skew2 = None
            try:
                ms2 = float(getattr(self, "_market_age_s", float("inf")))
                if math.isfinite(ms2):
                    mkt_skew2 = ms2
            except Exception:
                mkt_skew2 = None
            out["focus"] = {
                "symbols": syms_list,
                "scan_age_sec": scan_age,
                "market_age_sec": market_snap_age,
                "mkt_clock_skew_sec": mkt_skew2,
                "api_age_sec": (None if api_age2 == float("inf") else float(api_age2)),
                "market_confidence": float(getattr(self, "_snap_confidence", 100.0) or 0.0),
                "market_state": str(getattr(self, "_snap_state", "OK") or "OK"),
                "market_source": str(getattr(self, "_snap_source", "") or ""),
                "market_server_time": (None if not self._market_server_time else float(self._market_server_time)),
                "whale_active": {k: bool(v) for k, v in (getattr(self, "_focus_whale_active", {}) or {}).items()},
                "weights": weights,
                "hw_state": str(getattr(self, "_hw_state", "") or ""),
                "hw_score": (None if getattr(self, "_hw_score", None) is None else float(getattr(self, "_hw_score", 0.0) or 0.0)),
                "hw_since_ts": float(getattr(self, "_hw_since_ts", 0.0) or 0.0),
                "hw_thresholds": dict(getattr(self, "_hw_thresholds", {}) or {}),
                "recover": {
                    "last_reason": str(getattr(self, "_hw_last_recover_reason", "") or ""),
                    "streak": int(getattr(self, "_hw_recover_streak", 0) or 0),
                    "next_ts": float(getattr(self, "_hw_next_recover_ts", 0.0) or 0.0),
                    "last_ok_ts": float(getattr(self, "_hw_last_recover_ok_ts", 0.0) or 0.0),
                    "last_fail_ts": float(getattr(self, "_hw_last_recover_fail_ts", 0.0) or 0.0),
                },
                "stale_symbols": (
                    self._mkt_store.stale_symbols(
                        now=now,
                        stale_after_sec=float(_env_float("DASH_SYMBOL_STALE_SEC", 15.0) or 15.0),
                        limit=int(_env_int("DASH_SYMBOL_STALE_MAX", 12) or 12),
                    ) if getattr(self, "_mkt_store", None) is not None else []
                ),
            }
        except Exception:
            out["focus"] = {"symbols": [], "scan_age_sec": None, "whale_active": {}, "weights": {}}
        dead = []
        soft_bl = 0
        try:
            dead = sorted(list(getattr(self.feed, "_dead_symbols", set()) or []))
        except Exception:
            dead = []
        try:
            if hasattr(self, "soft_blacklist"):
                ss = getattr(self.soft_blacklist, "to_state", None)
                st = ss() if callable(ss) else {}
                if isinstance(st, dict):
                    items = st.get("items") or st.get("symbols") or st.get("data") or st.get("entries") or {}
                    if isinstance(items, dict):
                        soft_bl = len(items)
                    elif isinstance(items, list):
                        soft_bl = len(items)
        except Exception:
            soft_bl = 0
        out["symbols"] = {"dead_count": int(len(dead)), "soft_blacklist_count": int(soft_bl)}
        try:
            ostats = _compute_wallet_trade_stats(getattr(self, "orders", None), now_ts=now)
        except Exception:
            ostats = {}
        total_cash = total_eq = total_exp = total_upnl = 0.0
        total_pos = 0
        total_open_orders = 0
        for w, st in (self.wallets or {}).items():
            ws = (ostats.get(str(w), {}) if isinstance(ostats, dict) else {}) or {}
            cash = float(getattr(st, "cash_irt", 0.0) or 0.0)
            eq = None
            try:
                eqv = float(getattr(st, "equity_irt", 0.0) or 0.0)
                if eqv > 0.0:
                    eq = eqv
            except Exception:
                eq = None
            if eq is None:
                try:
                    eq = float(getattr(st, "cash_total_irt", cash) or cash)
                except Exception:
                    eq = cash
                try:
                    eq = float(self._estimate_equity_irt(cash, getattr(st, "positions", {}) or {}))
                except Exception:
                    pass
            exp = 0.0
            try:
                exp = float(getattr(st, "engaged_irt", 0.0) or 0.0)
            except Exception:
                exp = 0.0
            upnl = 0.0
            try:
                upnl = float(getattr(st, "pnl_unrealized_irt", 0.0) or 0.0)
            except Exception:
                upnl = 0.0
            rpnl = 0.0
            try:
                rpnl = float(getattr(st, "pnl_realized_irt", 0.0) or 0.0)
            except Exception:
                rpnl = 0.0
            tpnl = upnl + rpnl
            try:
                tpnl = float(getattr(st, "pnl_total_irt", tpnl) or tpnl)
            except Exception:
                pass
            open_orders_exch = None
            try:
                open_orders_exch = int(getattr(st, "open_orders_exch", 0) or 0)
            except Exception:
                open_orders_exch = None
            steps_open = 0
            try:
                steps_open = int(getattr(st, "steps_open", 0) or 0)
            except Exception:
                steps_open = 0
            sync_ok = None
            sync_err = ""
            sync_age = None
            try:
                sync_ok = bool(getattr(st, "last_orders_sync_ok", True))
            except Exception:
                sync_ok = None
            try:
                sync_err = str(getattr(st, "last_orders_sync_err", "") or "")
            except Exception:
                sync_err = ""
            try:
                ts = float(getattr(st, "last_orders_sync_ts", 0.0) or 0.0)
                sync_age = (now - ts) if ts > 0 else None
            except Exception:
                sync_age = None
            sanity_halt = False
            sanity_reason = ""
            sanity_until = None
            try:
                sanity_halt = bool(getattr(st, "sanity_halt", False))
                sanity_reason = str(getattr(st, "sanity_reason", "") or "")
                until_ts = float(getattr(st, "sanity_until_ts", 0.0) or 0.0)
                sanity_until = (until_ts - now) if until_ts > now else 0.0
            except Exception:
                pass
            rej = ""
            try:
                rej = str(getattr(st, "last_reject_reason", "") or "")
            except Exception:
                rej = ""
            phx_state = ""
            phx_conf = None
            try:
                phx_state = str(getattr(st, "phoenix_state", "") or "")
                phx_conf = float(getattr(st, "phoenix_conf", 0.0) or 0.0)
            except Exception:
                phx_state, phx_conf = "", None
            total_cash += cash
            total_eq += float(eq or 0.0)
            total_exp += exp
            total_upnl += upnl
            total_pos += int(len(getattr(st, "positions", {}) or {}))
            if isinstance(open_orders_exch, int):
                total_open_orders += open_orders_exch
            else:
                total_open_orders += int(ws.get("open_trades", 0) or 0)
            out["wallets"][w] = {
                "cash_irt": cash,
                "open_positions": int(len(getattr(st, "positions", {}) or {})),
                "open_trades": int(ws.get("open_trades", 0) or 0),
                "done_trades": int(ws.get("done_trades", 0) or 0),
                "canceled_trades": int(ws.get("canceled_trades", 0) or 0),
                "cancel_reasons": str(ws.get("cancel_reasons", "") or ""),
                "last_event": str(getattr(st, "last_event", "") or ""),
                "cash_total_irt": float(getattr(st, "cash_total_irt", cash) or cash),
                "equity_irt": float(eq or cash),
                "exposure_irt": exp,
                "upnl_irt": upnl,
                "rpnl_irt": rpnl,
                "tpnl_irt": tpnl,
                "open_orders_exch": open_orders_exch if isinstance(open_orders_exch, int) else int(ws.get("open_trades", 0) or 0),
                "steps_open": steps_open,
                "done_24h": int(ws.get("done_24h", 0) or 0),
                "canceled_24h": int(ws.get("canceled_24h", 0) or 0),
                "last_resolved_age_sec": ws.get("last_resolved_age_sec", None),
                "orders_sync_ok": sync_ok,
                "orders_sync_err": sync_err,
                "orders_sync_age_sec": sync_age,
                "sanity_halt": sanity_halt,
                "sanity_reason": sanity_reason,
                "sanity_until_sec": sanity_until,
                "last_reject_reason": rej,
                "phoenix_state": phx_state,
                "phoenix_conf": phx_conf,
            }
        out["totals"] = {
            "cash_irt": total_cash,
            "equity_irt": total_eq,
            "exposure_irt": total_exp,
            "upnl_irt": total_upnl,
            "open_positions": int(total_pos),
            "open_orders": int(total_open_orders),
        }
        try:
            out["events"] = list(self.logger.ring.last_important(10))
        except Exception:
            try:
                out["events"] = list(self._log.ring.last_important(10))
            except Exception:
                out["events"] = []
        try:
            p = str(os.environ.get("DASH_EXPORT_PATH", "") or "").strip()
            if p:
                last = float(getattr(self, "_dash_export_last_ts", 0.0) or 0.0)
                if (now - last) >= 2.0:
                    setattr(self, "_dash_export_last_ts", now)
                    try:
                        _ensure_dir(p)
                    except Exception:
                        pass
                    tmp = p + ".tmp"
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(out, f, ensure_ascii=False)
                    try:
                        os.replace(tmp, p)
                    except Exception:
                        try:
                            os.rename(tmp, p)
                        except Exception:
                            pass
        except Exception:
            pass
        return out
    def _state_obj(self) -> dict:
        pub = getattr(self, "public", None)
        depth_ep = getattr(pub, "_working_depth_ep", None) if pub is not None else None
        depth_map = None
        try:
            m = getattr(pub, "_working_depth_ep_map", None) if pub is not None else None
            if isinstance(m, dict):
                depth_map = {str(_canon_symbol(k)): str(v) for k, v in m.items() if k and v}
        except Exception:
            depth_map = None
        return {
            "risk": self.risk.to_dict(),
            "net": self.net.to_dict(),
            "blacklist": sorted(list(getattr(self.feed, "_dead_symbols", set()) or [])),
            "soft_blacklist": (self.soft_blacklist.to_state() if hasattr(self, "soft_blacklist") else {}),
            "depth_ep": (str(depth_ep) if depth_ep else None),
            "depth_ep_map": (depth_map if isinstance(depth_map, dict) and depth_map else {}),
            "wallets": {
                w: {
                    "cash_irt": st.cash_irt,
                    "positions": {sym: {"qty": p.qty, "entry_px": p.entry_px, "entry_ts": p.entry_ts} for sym, p in st.positions.items()},
                } for w, st in self.wallets.items()
            },
        }
    def _load_state(self) -> None:
        path = self.cfg.state_path
        try:
            setattr(self, "_state_loaded_ok", False)
        except Exception:
            pass
        if not path:
            return
        candidates: List[str] = []
        try:
            candidates.append(str(path))
        except Exception:
            candidates.append(path)
        try:
            candidates.append(str(path) + ".bak")
        except Exception:
            candidates.append(path + ".bak")
        try:
            d = os.path.dirname(os.path.abspath(path)) or "."
            base = os.path.basename(path)
            pref = base + ".tmp."
            tmps: List[str] = []
            for fn in os.listdir(d):
                try:
                    if fn.startswith(pref):
                        fp = os.path.join(d, fn)
                        if os.path.isfile(fp):
                            tmps.append(fp)
                except Exception:
                    continue
            try:
                tmps.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            except Exception:
                pass
            candidates.extend(tmps)
        except Exception:
            pass
        had_any = False
        last_err: Exception | None = None
        loaded_obj: dict | None = None
        loaded_from: str = ""
        for p in candidates:
            try:
                if not p or (not os.path.isfile(p)):
                    continue
                had_any = True
                with open(p, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                if not isinstance(obj, dict):
                    continue
                if isinstance(obj.get("risk"), dict):
                    self.risk.load_dict(obj.get("risk"))
                if isinstance(obj.get("net"), dict):
                    try:
                        self.net.load_dict(obj.get("net"))
                    except Exception:
                        pass
                try:
                    sb = obj.get("soft_blacklist") or {}
                    if hasattr(self, "soft_blacklist") and isinstance(sb, dict):
                        self.soft_blacklist.load_state(sb)
                except Exception:
                    pass
                try:
                    bl = obj.get("blacklist") or obj.get("dead_symbols") or []
                    if isinstance(bl, list) and hasattr(self, "soft_blacklist"):
                        for s in bl:
                            ss = _canon_symbol(s)
                            if ss:
                                try:
                                    self.soft_blacklist.block(ss, reason="STATE_RESTORE")
                                except Exception:
                                    pass
                except Exception:
                    pass
                pub = getattr(self, "public", None)
                if pub is not None:
                    try:
                        ep_map = obj.get("depth_ep_map") or {}
                        if isinstance(ep_map, dict):
                            clean = {str(_canon_symbol(k)): str(v) for k, v in ep_map.items() if k and v}
                            try:
                                setattr(pub, "_working_depth_ep_map", clean)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        ep = obj.get("depth_ep")
                        if isinstance(ep, str) and ep:
                            setattr(pub, "_working_depth_ep", ep)
                    except Exception:
                        pass
                wallets = obj.get("wallets")
                if isinstance(wallets, dict):
                    for wn, st_obj in wallets.items():
                        if wn not in self.wallets:
                            continue
                        st = self.wallets[wn]
                        try:
                            st.cash_irt = float(st_obj.get("cash_irt", st.cash_irt))
                        except Exception:
                            pass
                        pos = st_obj.get("positions")
                        if isinstance(pos, dict):
                            for sym, ppos in pos.items():
                                s = _canon_symbol(sym)
                                if not s:
                                    continue
                                try:
                                    qty = float(ppos.get("qty", 0.0))
                                    ep = float(ppos.get("entry_px", 0.0))
                                    ets = float(ppos.get("entry_ts", 0.0))
                                    if qty != 0.0:
                                        st.positions[s] = Position(symbol=s, qty=qty, entry_px=ep, entry_ts=ets)
                                except Exception:
                                    pass
                loaded_obj = obj
                loaded_from = str(p)
                break
            except Exception as e:
                last_err = e
                continue
        if loaded_obj is not None:
            try:
                setattr(self, "_state_loaded_ok", True)
            except Exception:
                pass
            if loaded_from and loaded_from != str(path):
                try:
                    _atomic_write_json(str(path), loaded_obj, fsync=bool(_env_bool("STATE_FSYNC", False)))
                except Exception:
                    pass
            return
        if had_any:
            try:
                self.risk.safe_mode = True
                self.risk.safe_reason = "STATE_UNREADABLE"
            except Exception:
                pass
            if not bool(getattr(self.cfg, "dry_run", False)):
                if last_err is not None:
                    raise RuntimeError("Refusing to trade: state load failed") from last_err
                raise RuntimeError("Refusing to trade: state load failed")
        return
    def _save_state_if_needed(self, force: bool = False) -> None:
        now = time.time()
        if (not force) and ((now - self._last_state_save) < self.cfg.state_save_sec):
            return
        self._last_state_save = now
        path = self.cfg.state_path
        try:
            try:
                if hasattr(self, 'soft_blacklist'):
                    self.soft_blacklist._prune(time.time())
            except Exception:
                pass
            fsync_flag = bool(_env_bool("STATE_FSYNC", False))
            try:
                if path and os.path.isfile(path):
                    bak = str(path) + ".bak"
                    tmp = f"{bak}.tmp.{os.getpid()}"
                    with open(path, "rb") as rf, open(tmp, "wb") as wf:
                        for _omega_guard in range(1000000):
                            buf = rf.read(1024 * 1024)
                            if not buf:
                                break
                            wf.write(buf)
                        wf.flush()
                        if fsync_flag:
                            try:
                                os.fsync(wf.fileno())
                            except Exception:
                                pass
                    try:
                        os.replace(tmp, bak)
                    except Exception:
                        try:
                            os.rename(tmp, bak)
                        except Exception:
                            pass
                    if fsync_flag:
                        d = os.path.dirname(os.path.abspath(bak)) or "."
                        try:
                            fd = os.open(d, os.O_RDONLY)
                        except Exception:
                            fd = None
                        if fd is not None:
                            try:
                                os.fsync(fd)
                            except Exception:
                                pass
                            finally:
                                try:
                                    os.close(fd)
                                except Exception:
                                    pass
            except Exception:
                pass
            _atomic_write_json(path, self._state_obj(), fsync=fsync_flag)
            try:
                _state_autopurge(path, max_mb=int(_env_int("STATE_AUTOPURGE_MB", 50)), keep_returns=int(_env_int("STATE_AUTOPURGE_KEEP", 1500)))
            except Exception:
                pass
        except Exception as e:
            self._log.error("event=STATE_SAVE_FAIL path=%s err=%s", path, e, exc_info=True)
            if _env_bool("LIVE_TRADING", False):
                self.risk.halt_new_trades("STATE_SAVE_FAIL")
    async def _refresh_balance_if_needed(self, w: WalletRuntime) -> float:
        now = time.time()
        def _balance_refresh_degraded(reason: str) -> float:
            try:
                w.last_balance_ok = False
            except Exception:
                pass
            try:
                w.last_balance_ts = now
            except Exception:
                pass
            try:
                w.last_balance_err = str(reason)[:300]
            except Exception:
                pass
            try:
                self._log.warning("event=BALANCE_REFRESH_DEGRADED wallet=%s reason=%s", getattr(w, "name", None), str(reason)[:300])
            except Exception:
                pass
            return float(getattr(w, "cash_irt", 0.0) or 0.0)
        if (now - w.last_balance_ts) < self.cfg.balance_refresh_sec and w.cash_irt > 0:
            return w.cash_irt
        if self.cfg.dry_run and (not _env_bool("FETCH_BALANCE_IN_DRY_RUN", True)):
            w.cash_irt = float(_env_float("DRY_RUN_CASH_IRT", 100_000_000.0))
            try:
                w.cash_total_irt = float(getattr(w, "cash_irt", 0.0) or 0.0)
            except Exception:
                pass
            try:
                self.logger.info(
                    "event=BALANCE_REFRESH_OK wallet=%s cash_irt=%.2f last_balance_ok=%s",
                    getattr(w, "name", None),
                    float(getattr(w, "cash_irt", 0.0) or 0.0),
                    True,
                )
            except Exception:
                pass
            w.last_balance_ok = True
            try:
                w.last_balance_err = ""
            except Exception:
                pass
            w.last_balance_ts = now
            return w.cash_irt
        last_cash = float(w.cash_irt or 0.0)
        try:
            get_bal = getattr(w.ex, "get_balance", None)
            if callable(get_bal):
                if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
                    print(f"REFRESHDBG CALL_GET_BAL wallet={w.name}")
                bal = await get_bal()
                if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
                    print(f"REFRESHDBG GOT_BAL wallet={w.name} type={type(bal).__name__} value={bal}")
            else:
                req = getattr(w.ex, "request", None)
                if callable(req):
                    if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
                        print(f"REFRESHDBG FALLBACK_REQ wallet={w.name} ep=/wallet/balance/")
                    try:
                        try:
                            def _s43_mask_fadb(v):
                                v = str(v or "")
                                if len(v) <= 0:
                                    return "<EMPTY>"
                                if len(v) <= 12:
                                    return v[:2] + "...len=" + str(len(v))
                                return v[:6] + "..." + v[-4:] + ":len=" + str(len(v))
                            _req_self = getattr(req, "__self__", None)
                            _tok = getattr(_req_self, "_token", "") if _req_self is not None else ""
                            _scheme = getattr(_req_self, "_auth_scheme", None) if _req_self is not None else None
                            _hp = getattr(_req_self, "_headers_private", None) or {}
                            _authv = ""
                            try:
                                _authv = _hp.get("Authorization", "") if hasattr(_hp, "get") else ""
                            except Exception:
                                _authv = ""
                            _base = ""
                            try:
                                _base = getattr(_req_self, "base_url", None) or getattr(_req_self, "_base_url", None) or ""
                            except Exception:
                                _base = ""
                            _wn = None
                            try:
                                _wn = getattr(w, "name", None)
                            except Exception:
                                _wn = None
                            _s43_debug_print(
                                f"AUTHDBG_FALLBACK_REQ_V1 wallet={_wn or 'UNKNOWN'} "
                                f"req_self_type={type(_req_self).__name__ if _req_self is not None else 'None'} "
                                f"scheme={_scheme} "
                                f"token={_s43_mask_fadb(_tok)} "
                                f"auth={_s43_mask_fadb(_authv)} "
                                f"token_len={len(str(_tok or ''))} "
                                f"auth_len={len(str(_authv or ''))} "
                                f"base={_base}",
                                flush=True,
                            )
                        except Exception as _fae:
                            _s43_debug_print(f"AUTHDBG_FALLBACK_REQ_V1_FAIL err={type(_fae).__name__}:{_fae}", flush=True)
                        # S43_TOKEN_OVERRIDE_FALLBACK_V1
                        try:
                            import os as _s43_os
                            def _s43_mask_tok_ov(v):
                                v = str(v or "")
                                if not v:
                                    return "<EMPTY>"
                                if len(v) <= 8:
                                    return v[:2] + "...len=" + str(len(v))
                                return v[:4] + "..." + v[-4:] + ":len=" + str(len(v))
                            _req_self = getattr(req, "__self__", None)
                            _wn = None
                            try:
                                _wn = str(getattr(w, "name", "") or "").strip()
                            except Exception:
                                _wn = ""
                            _env_key = "S43_" + _wn.upper() + "_TOKEN" if _wn else ""
                            _env_tok = _s43_os.environ.get(_env_key, "") if _env_key else ""
                            _old_tok = getattr(_req_self, "_token", "") if _req_self is not None else ""
                            if _req_self is not None and _env_tok:
                                _raw = str(_env_tok).strip()
                                _scheme = "Token"
                                _tok = _raw
                                if " " in _raw:
                                    _a, _b = _raw.split(None, 1)
                                    if _a.lower() in ("token", "bearer") and _b.strip():
                                        _scheme, _tok = _a, _b.strip()
                                setattr(_req_self, "_auth_scheme", _scheme)
                                setattr(_req_self, "_token", _tok)
                                _hp = getattr(_req_self, "_headers_private", None)
                                if not isinstance(_hp, dict):
                                    _hp = {}
                                    setattr(_req_self, "_headers_private", _hp)
                                _hp["Authorization"] = f"{_scheme} {_tok}"
                                _s43_debug_print(f"S43_TOKEN_OVERRIDE_FALLBACK_V1 wallet={_wn or 'UNKNOWN'} env={_env_key} old={_s43_mask_tok_ov(_old_tok)} new={_s43_mask_tok_ov(_tok)} auth_len={len(_hp.get('Authorization', ''))}", flush=True)
                            else:
                                _s43_debug_print(f"S43_TOKEN_OVERRIDE_FALLBACK_V1_NO_ENV wallet={_wn or 'UNKNOWN'} env={_env_key or 'NONE'} current={_s43_mask_tok_ov(_old_tok)}", flush=True)
                        except Exception as _s43_toe:
                            _s43_debug_print(f"S43_TOKEN_OVERRIDE_FALLBACK_V1_FAIL err={type(_s43_toe).__name__}:{_s43_toe}", flush=True)
                        bal = await req("GET", "/wallet/balance/", auth=True)
                    except Exception as _e:
                        try:
                            if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
                                print(
                                    f"REFRESHDBG FALLBACK_EXC wallet={w.name} "
                                    f"type={type(_e).__module__}.{type(_e).__name__} "
                                    f"err={_e}"
                                )
                        except Exception:
                            if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
                                print(f"REFRESHDBG FALLBACK_EXC wallet={w.name} err_log_failed")
                        raise
                    if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
                        print(f"REFRESHDBG FALLBACK_RESP wallet={w.name} type={type(bal).__name__} value={bal}")
                else:
                    raise AttributeError("has no attribute 'get_balance'")
        except asyncio.CancelledError:
            raise
        except TradingHalt: raise
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            self._log.warning(
                "event=BALANCE_REFRESH_TRANSIENT wallet=%s err=%s",
                w.name,
                f"{type(e).__name__}: {e}",
            )
            w.last_balance_ts = now
            return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: TRANSIENT: {type(e).__name__}:{e}")
        except ApiHttpError as e:
            # Precise ArzPlus 403 diagnostics (fail-closed but keep engine alive)
            msg = str(e)
            try:
                try:
                    self.logger.warning(
                        "event=BALANCE_REFRESH_ERR wallet=%s err=%s last_balance_ok=%s",
                        getattr(w, "name", None),
                        str(msg),
                        False,
                    )
                except Exception:
                    pass
                w.last_balance_err = msg
            except Exception:
                pass
            st = int(getattr(e, "http_status", 0) or 0)
            cause = str(getattr(e, "cause", "") or "")
            drift_s = getattr(e, "drift_s", None)
            try:
                if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
                    print(f"BALAUTHDBG HTTP_FAIL wallet={w.name} status={st} cause={cause} endpoint={getattr(e, 'endpoint', '')} exchange={getattr(e, 'exchange', '')} msg={msg[:120]}")
            except Exception as _e:
                if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
                    print(f"BALAUTHDBG HTTP_FAIL_LOG_ERR wallet={w.name} err={type(_e).__name__}:{_e}")
            if (not self.cfg.dry_run) and st in (401, 403):
                # Fail-closed: halt trading on auth/permission blocks.
                # Keep existing recovery logic (prefix preserved).
                if st == 403:
                    self.risk.halt_new_trades("BALANCE_AUTH_FAIL: Balance blocked by exchange – trading halted")
                else:
                    self.risk.halt_new_trades("BALANCE_AUTH_FAIL")
            try:
                self._log.warning(
                    "event=BALANCE_REFRESH_HTTP_FAIL wallet=%s exchange=%s endpoint=%s http_status=%s cause=%s drift_s=%s err=%s",
                    w.name,
                    str(getattr(e, "exchange", "") or "arzplus"),
                    str(getattr(e, "endpoint", "") or ""),
                    st,
                    cause,
                    (f"{float(drift_s):.3f}" if drift_s is not None else "-"),
                    msg[:200],
                )
            except Exception:
                pass
            w.last_balance_ts = now
            return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: HTTP_FAIL: {type(e).__name__}:{e}")
        except ApiError as e:
            msg = str(e)
            try:
                w.last_balance_err = msg
            except Exception:
                pass
            is_transient = (
                ("Transient HTTP" in msg)
                or ("HTTP 429" in msg)
                or ("HTTP 500" in msg)
                or ("HTTP 502" in msg)
                or ("HTTP 503" in msg)
                or ("HTTP 504" in msg)
            )
            if is_transient:
                self._log.warning(
                    "event=BALANCE_REFRESH_TRANSIENT wallet=%s err=%s",
                    w.name,
                    msg[:200],
                )
                w.last_balance_ts = now
                return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: TRANSIENT: {type(e).__name__}:{e}")
            if (not self.cfg.dry_run) and (("HTTP 401" in msg) or ("HTTP 403" in msg)):
                if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
                    print(f"BALAUTHDBG API_FAIL wallet={w.name} msg={msg[:200]}")
                self.risk.halt_new_trades(f"BALANCE_AUTH_FAIL: {msg[:300]}")
            self._log.warning(
                "event=BALANCE_REFRESH_API_FAIL wallet=%s err=%s",
                w.name,
                msg[:200],
            )
            w.last_balance_ts = now
            return _balance_refresh_degraded(f"BALANCE_FETCH_FAILED: API_FAIL: {type(e).__name__}:{e}")
        except Exception as e:
            try:
                msg = f"{type(e).__name__}: {e}"
                try:
                    if isinstance(e, AttributeError):
                        mm = re.search(r"has no attribute '([^']+)'", str(e))
                        if mm:
                            msg = f"AttributeError: NOATTR {mm.group(1)}"
                except Exception:
                    pass
                w.last_balance_err = msg
            except Exception:
                pass
            self._log.warning(
                "event=BALANCE_REFRESH_FAIL wallet=%s err=%s",
                w.name,
                f"{type(e).__name__}: {e}",
                exc_info=True,
            )
            w.last_balance_ts = now
            return _balance_refresh_degraded("BALANCE_FETCH_FAILED: EXC")
        cash_free_irt, cash_total_irt, assets_free, assets_total, ok = _parse_wallet_balance_response_v2(
            bal, quote=str(getattr(self.cfg, "quote", "IRT") or "IRT")
        )
        try:
            if (not ok) and _is_arzplus_client(getattr(w, "ex", None)) and isinstance(bal, (dict, list)):
                cf2, ct2, af2, at2, ok2 = _parse_arzplus_wallet_balance_fast(
                    bal, quote=str(getattr(self.cfg, "quote", "IRT") or "IRT")
                )
                if ok2:
                    cash_free_irt, cash_total_irt, assets_free, assets_total, ok = cf2, ct2, af2, at2, ok2
        except Exception as e:
            return _balance_refresh_degraded("BALANCE_FETCH_FAILED: ARZPLUS_FAST_PARSE_FAIL")
        if ok:
            w.cash_irt = float(max(0.0, cash_free_irt))
            try:
                w.cash_total_irt = float(max(0.0, cash_total_irt))
                if w.cash_total_irt <= 0.0:
                    w.cash_total_irt = float(w.cash_irt)
            except Exception:
                w.cash_total_irt = float(w.cash_irt)
            w.last_balance_ok = True
            try:
                if bool(getattr(self, 'risk', None) is not None) and bool(getattr(self.risk, 'safe_mode', False)):
                    r0 = str(getattr(self.risk, 'safe_reason', '') or '')
                    if r0.startswith('BALANCE_AUTH_FAIL'):
                        all_ok = True
                        try:
                            now2 = float(time.time())
                        except Exception:
                            now2 = time.time()
                        try:
                            _br = float(getattr(self.cfg, 'balance_refresh_sec', 8.0) or 8.0)
                        except Exception:
                            _br = 8.0
                        try:
                            fresh_sec = float(_env_float('BALANCE_AUTH_RECOVER_REQUIRE_FRESH_SEC', max(15.0, _br * 3.0)) or max(15.0, _br * 3.0))
                        except Exception:
                            fresh_sec = max(15.0, _br * 3.0)
                        fresh_sec = float(max(10.0, min(300.0, fresh_sec)))
                        try:
                            for _w2 in (getattr(self, 'wallets', {}) or {}).values():
                                try:
                                    if not bool(getattr(_w2, 'last_balance_ok', False)):
                                        all_ok = False
                                        break
                                    ts2 = float(getattr(_w2, 'last_balance_ts', 0.0) or 0.0)
                                    if ts2 <= 0.0 or (now2 - ts2) > fresh_sec:
                                        all_ok = False
                                        break
                                except Exception:
                                    all_ok = False
                                    break
                        except Exception:
                            all_ok = False
                        if all_ok:
                            self.risk.safe_mode = False
                            self.risk.safe_reason = ''
                            try:
                                self.risk.safe_since_ts = 0.0
                            except Exception:
                                pass
                            try:
                                self.risk._save_risk_journal(force=True)
                            except Exception:
                                pass
                            self._log.warning('event=SAFE_CLEARED reason=BALANCE_AUTH_FAIL wallet=%s', w.name)
            except Exception:
                pass
            try:
                w.assets_snapshot = dict(assets_free or {})
                try:
                    w.assets_total_snapshot = dict((assets_total or {}) or (assets_free or {}))
                except Exception:
                    w.assets_total_snapshot = dict(assets_free or {})
                w.last_assets_ts = now
            except Exception:
                pass
        else: return _balance_refresh_degraded("BALANCE_FETCH_FAILED: PARSE_OK_FALSE")
        try:
            if float(getattr(w, "cash_total_irt", 0.0) or 0.0) <= 0.0:
                w.cash_total_irt = float(getattr(w, "cash_irt", 0.0) or 0.0)
        except Exception:
            pass
        try:
            if not (getattr(w, "assets_total_snapshot", None) or {}):
                w.assets_total_snapshot = dict(getattr(w, "assets_snapshot", None) or {})
        except Exception:
            pass
        w.last_balance_ts = now
        return w.cash_irt
    def _idem_ok(self, wallet: str, symbol: str, side: str, *, ttl_sec: Optional[float] = None) -> bool:
        key = (wallet, _canon_symbol(symbol), str(side).lower())
        now = time.time()
        last = self._idem.get(key, 0.0)
        ttl = float(ttl_sec) if ttl_sec is not None else float(self.cfg.idempotency_ttl_sec)
        if last and (now - last) < ttl:
            return False
        self._idem[key] = now
        return True
    def _idem_forget(self, wallet: str, symbol: str, side: str) -> None:
        """Forget an idempotency key.

        Used to allow immediate retry after transient execution errors.
        """
        try:
            key = (str(wallet or ""), _canon_symbol(symbol), str(side).lower())
            self._idem.pop(key, None)
        except Exception:
            pass

    def _expected_net_profit_irt(self, notional: float, target_move_bps: float = 35.0, *, cfg: Optional[BotConfig] = None) -> float:
        c = cfg or self.cfg
        n = float(notional or 0.0)
        if n <= 0:
            return 0.0
        gross = n * (float(target_move_bps) / 10000.0)
        pen = n * ((c.fee_bps + c.slippage_bps + c.order_safety_bps) / 10000.0)
        return float(gross - pen)
    def get_risk_weight(self, symbol: str, rank: int) -> float:
        sym = _canon_symbol(symbol)
        if sym == "PAXGIRT":
            return 0.20
        rel = max(0, int(rank) - 1)
        weights = [0.18, 0.15, 0.12, 0.10, 0.08, 0.07, 0.05, 0.05]
        return float(weights[min(rel, len(weights) - 1)])
    def calculate_opportunity_score(self, data: dict) -> float:
        try:
            vol = float(data.get("volume") or 0.0)
        except Exception:
            vol = 0.0
        try:
            high = float(data.get("high") or 0.0)
            low = float(data.get("low") or 0.0)
        except Exception:
            high, low = 0.0, 0.0
        vola = 0.0
        if low and low > 0 and high and high > 0:
            vola = max(0.0, (high - low) / low)
        liq = math.sqrt(max(vol, 0.0))
        return (liq * 0.6) + (vola * liq * 0.4)