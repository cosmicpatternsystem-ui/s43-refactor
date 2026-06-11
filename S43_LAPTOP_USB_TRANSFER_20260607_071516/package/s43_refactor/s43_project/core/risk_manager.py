from .order_book_top import OrderBookTop
from .logger import Logger
from .risk_decision import RiskDecision
from .trading_memory import TradingMemory
from .__noop_lock import _NoopLock
from .bot_config import BotConfig
from .risk_escalation_layer import RiskEscalationLayer
from .position import Position

class RiskManager:
    def __init__(self, cfg: BotConfig, logger: logging.Logger):
        self.cfg = cfg
        self._logger = logger
        self.safe_mode = False
        self.safe_reason = ""
        self.safe_since_ts = 0.0
        self._last_safe_log: Dict[str, float] = {}
        self.memory = TradingMemory()
        self.daily_loss_irt = 0.0
        self._day_key = time.strftime("%Y-%m-%d")
        self.consecutive_losses: Dict[str, int] = {}
        self.blocked_until: Dict[str, float] = {}
        self._risk_journal_path = getattr(cfg, "risk_journal_path", "")
        self._risk_journal_last_write = 0.0
        _lrj = getattr(self, "_load_risk_journal", None)
        if callable(_lrj):
            _lrj()
        else:
            try:
                self._logger.warning("event=RISK_JOURNAL_LOAD ok=0 reason=missing_method action=skip")
            except Exception:
                pass
        self.escalation = RiskEscalationLayer()
        self._runtime_risk: Dict[str, RiskDecision] = {}
        self._runtime_risk_ts: Dict[str, float] = {}
        self._runtime_lock = _NoopLock()
        self._wallet_cash_total_irt: Dict[str, float] = {}
        self._wallet_cash_free_irt: Dict[str, float] = {}
        self._wallet_balance_ok: Dict[str, bool] = {}
        self._wallet_balance_ts: Dict[str, float] = {}
    def _roll_day(self) -> None:
        day = time.strftime("%Y-%m-%d")
        if day != self._day_key:
            self._day_key = day
            self.daily_loss_irt = 0.0
            self.consecutive_losses.clear()
            self.blocked_until.clear()
            self.safe_mode = False
            self.safe_reason = ""
            self.safe_since_ts = 0.0
            self._logger.info("New trading day: counters reset.")
            self._save_risk_journal(force=True)
    def update_wallet_balance_snapshot(
        self,
        wallet: str,
        cash_free_irt: float,
        cash_total_irt: float,
        ok: bool,
        *,
        ts: Optional[float] = None,
    ) -> None:
        try:
            w = str(wallet or "").strip()
        except Exception:
            w = ""
        if not w:
            return
        try:
            t = float(time.time() if ts is None else ts)
        except Exception:
            t = float(time.time())
        try:
            cf = float(cash_free_irt or 0.0)
        except Exception:
            cf = 0.0
        try:
            ct = float(cash_total_irt or 0.0)
        except Exception:
            ct = 0.0
        if (not math.isfinite(cf)) or cf < 0.0:
            cf = 0.0
        if (not math.isfinite(ct)) or ct < 0.0:
            ct = 0.0
        if ct <= 0.0:
            ct = cf
        try:
            with self._runtime_lock:
                self._wallet_cash_free_irt[w] = float(cf)
                self._wallet_cash_total_irt[w] = float(ct)
                self._wallet_balance_ok[w] = bool(ok) and float(ct) > 0.0
                self._wallet_balance_ts[w] = float(t)
        except Exception:
            return
    def global_cash_total_irt(self, now: Optional[float] = None) -> float:
        try:
            t = float(time.time() if now is None else now)
        except Exception:
            t = float(time.time())
        try:
            ttl = float(_env_float("GLOBAL_CASH_SNAPSHOT_TTL_SEC", 120.0) or 120.0)
        except Exception:
            ttl = 120.0
        ttl = float(max(10.0, min(900.0, ttl)))
        tot = 0.0
        try:
            with self._runtime_lock:
                cash_map = dict(self._wallet_cash_total_irt or {})
                ts_map = dict(self._wallet_balance_ts or {})
        except Exception:
            cash_map = dict(getattr(self, "_wallet_cash_total_irt", {}) or {})
            ts_map = dict(getattr(self, "_wallet_balance_ts", {}) or {})
        for w, ct in (cash_map or {}).items():
            try:
                ts0 = float(ts_map.get(w, 0.0) or 0.0)
            except Exception:
                ts0 = 0.0
            if ts0 <= 0.0 or (t - ts0) > ttl:
                continue
            try:
                v = float(ct or 0.0)
            except Exception:
                v = 0.0
            if math.isfinite(v) and v > 0.0:
                tot += v
        return float(tot)
    def _safe_log_throttle(self, reason: str, interval: float = 60.0) -> None:
        """Safe mode traffic control for halt_new_trades logs.

        """
        try:
            now = float(time.time())
        except Exception:
            now = time.time()
        key = "SAFE_MODE"
        try:
            last = float((self._last_safe_log or {}).get(key, 0.0) or 0.0)
        except Exception:
            last = 0.0
        if (now - last) < float(interval):
            return
        try:
            self._last_safe_log[key] = float(now)
        except Exception:
            pass
        try:
            since = float(getattr(self, "safe_since_ts", 0.0) or 0.0)
        except Exception:
            since = 0.0
        try:
            age_s = float(now - since) if since > 0.0 else 0.0
        except Exception:
            age_s = 0.0
        try:
            if getattr(self, "_logger", None) is not None:
                self._logger.warning("event=SAFE_MODE_ON reason=%s age=%.1fs", str(reason)[:64], float(age_s))
        except Exception:
            pass
    def halt_new_trades(self, reason: str) -> None:
        was_safe = bool(self.safe_mode)
        self.safe_mode = True
        self.safe_reason = reason
        try:
            if (not was_safe) or (float(getattr(self, "safe_since_ts", 0.0) or 0.0) <= 0.0):
                self.safe_since_ts = float(time.time())
        except Exception:
            pass
        self._safe_log_throttle(reason, interval=(0.0 if not was_safe else 60.0))
        self._save_risk_journal(force=True)
    def safe_level(self) -> str:
        if not bool(self.safe_mode):
            return "OFF"
        r = str(self.safe_reason or "")
        try:
            if r.startswith("HEALTH_SYS_"):
                if r.startswith("HEALTH_SYS_HALTED"):
                    return "HARD"
                if bool(_env_bool("TERMUX_MODE", False)):
                    def _parse_age(tag: str) -> Optional[float]:
                        try:
                            try:
                                try:
                                    import re as _re
                                except:
                                    pass
                            except:
                                pass
                            m0 = _re.search(rf"\b{tag}=([0-9\.]+)(ms|s|m|h|d)\b", r)
                            if not m0:
                                return None
                            v = float(m0.group(1))
                            u = m0.group(2)
                            if u == "ms":
                                return v / 1000.0
                            if u == "s":
                                return v
                            if u == "m":
                                return v * 60.0
                            if u == "h":
                                return v * 3600.0
                            if u == "d":
                                return v * 86400.0
                            return None
                        except Exception:
                            return None
                    mkt_s = _parse_age("mkt")
                    api_s = _parse_age("api")
                    mkt_crit = float(_env_float("HEALTH_WD_MKT_CRIT_SEC", 40.0) or 40.0)
                    api_crit = float(_env_float("HEALTH_WD_API_CRIT_SEC", 25.0) or 25.0)
                    if (mkt_s is not None and float(mkt_s) >= float(mkt_crit)) or (api_s is not None and float(api_s) >= float(api_crit)):
                        return "HARD"
                    return "SOFT"
        except Exception:
            pass
        hard_prefixes = (
            "MAX_DAILY_LOSS",
            "GLOBAL_EXIT",
            "BALANCE_AUTH_FAIL",
            "HEALTH_SYS_HALTED",
            "HEALTH_SYS_CRITICAL",
            "ORDER_RECONCILE_FAIL",
            "ORDER_RECONCILE_UNKNOWN",
            "STATE_LOAD_FAIL",
            "STATE_SAVE_FAIL",
            "RISK_JOURNAL_CORRUPT",
            "RISK_JOURNAL_WRITE_FAIL",
            "RISK_STATE_CORRUPT",
            "CORRUPTED_STATE",
        )
        try:
            if any(r.startswith(p) for p in hard_prefixes):
                return "HARD"
        except Exception:
            pass
        return "SOFT"
    def hard_blocks_all_orders(self, side: Optional[str] = None, reduce_only: bool = False) -> bool:
        if reduce_only or str(side or "").lower().strip() == "sell":
            return False
        if self.safe_level() != "HARD":
            return False
        r = str(self.safe_reason or "")
        try:
            grace = float(_env_float("SNIPER_GRACE_TRADE_DATA_AGE_SEC", 60.0) or 60.0)
        except Exception:
            grace = 60.0
        try:
            if (r.startswith("HEALTH_WD_") or r.startswith("HEALTH_SYS_")) and ("mkt=" in r or "top8=" in r):
                try:
                    try:
                        import re as _re
                    except:
                        pass
                except:
                    pass
                def _age(tag: str):
                    m = _re.search(rf"{tag}([0-9]+(?:\.[0-9]+)?)s", r)
                    return float(m.group(1)) if m else None
                mkt_age = _age("mkt=")
                top8_age = _age("top8=")
                net_bad = ("net=" in r) and any(k in r for k in ("ERR", "FAIL", "TIMEOUT", "DOWN"))
                if (not net_bad) and (mkt_age is not None) and (top8_age is not None) and (mkt_age <= grace) and (top8_age <= grace):
                    return False
        except Exception:
            pass
        return r.startswith("BALANCE_AUTH_FAIL") or r.startswith("HEALTH_SYS_HALTED") or r.startswith("HEALTH_SYS_CRITICAL")
    def _rk(self, wallet: str, sym: str) -> str:
        return _wallet_sym_key(wallet, sym)
    def set_runtime_risk(self, wallet: str, sym: str, decision: RiskDecision) -> None:
        try:
            key = self._rk(wallet, sym)
            now = float(time.time())
            with self._runtime_lock:
                self._runtime_risk[key] = decision
                self._runtime_risk_ts[key] = now
        except Exception:
            pass
    def get_runtime_risk(self, wallet: str, sym: str) -> Optional[RiskDecision]:
        try:
            key = self._rk(wallet, sym)
            with self._runtime_lock:
                d = self._runtime_risk.get(key)
                ts = float(self._runtime_risk_ts.get(key, 0.0) or 0.0)
            try:
                ttl = float(_env_float("RUNTIME_RISK_TTL_SEC", 30.0))
            except Exception:
                ttl = 30.0
            ttl = float(max(5.0, min(300.0, ttl)))
            if ts and (time.time() - ts) > ttl:
                return None
            return d
        except Exception:
            return None
    def _risk_journal_obj(self) -> dict:
        return {
            "v": 1,
            "day_key": self._day_key,
            "daily_loss_irt": float(self.daily_loss_irt),
            "safe_mode": bool(self.safe_mode),
            "safe_reason": str(self.safe_reason),
            "safe_since_ts": float(getattr(self, "safe_since_ts", 0.0) or 0.0),
            "consecutive_losses": dict(self.consecutive_losses),
            "blocked_until": dict(self.blocked_until),
            "ts": float(time.time()),
        }
    def _load_risk_journal(self) -> None:
        path = self._risk_journal_path
        if not path:
            return
        try:
            if not os.path.isfile(path):
                return
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            if not isinstance(obj, dict):
                raise ValueError("risk journal not a dict")
            day_key = str(obj.get("day_key", "") or "")
            today = time.strftime("%Y-%m-%d")
            if day_key != today:
                return
            self._day_key = day_key
            self.daily_loss_irt = float(obj.get("daily_loss_irt", 0.0) or 0.0)
            self.safe_mode = bool(obj.get("safe_mode", False))
            self.safe_reason = str(obj.get("safe_reason", "") or "")
            try:
                self.safe_since_ts = float(obj.get("safe_since_ts", 0.0) or 0.0)
                if self.safe_mode and (self.safe_since_ts <= 0.0):
                    self.safe_since_ts = float(obj.get("ts", 0.0) or time.time())
            except Exception:
                pass
            cl = obj.get("consecutive_losses") or {}
            if isinstance(cl, dict):
                self.consecutive_losses = {str(k): int(v) for k, v in cl.items()}
            bu = obj.get("blocked_until") or {}
            if isinstance(bu, dict):
                self.blocked_until = {str(k): float(v) for k, v in bu.items()}
            self._logger.info(
                "event=RISK_JOURNAL_LOAD ok=1 day=%s daily_loss_irt=%.2f safe_mode=%s",
                self._day_key, self.daily_loss_irt, self.safe_mode,
            )
        except Exception as e:
            self.safe_mode = True
            self.safe_reason = f"RISK_JOURNAL_CORRUPT:{type(e).__name__}"
            try:
                if float(getattr(self, "safe_since_ts", 0.0) or 0.0) <= 0.0:
                    self.safe_since_ts = float(time.time())
            except Exception:
                pass
            self._logger.critical(
                "event=RISK_JOURNAL_LOAD ok=0 action=safe_mode path=%s err=%s",
                path, e, exc_info=True
            )
    def _save_risk_journal(self, *, force: bool = False) -> None:
        path = self._risk_journal_path
        if not path:
            return
        now = time.time()
        if (not force) and (now - self._risk_journal_last_write) < float(self.cfg.risk_journal_throttle_sec):
            return
        self._risk_journal_last_write = now
        obj = self._risk_journal_obj()
        try:
            _atomic_write_json(path, obj, fsync=bool(self.cfg.risk_journal_fsync))
        except Exception as e:
            self.safe_mode = True
            self.safe_reason = f"RISK_JOURNAL_WRITE_FAIL:{type(e).__name__}"
            try:
                if float(getattr(self, "safe_since_ts", 0.0) or 0.0) <= 0.0:
                    self.safe_since_ts = float(time.time())
            except Exception:
                pass
            self._logger.critical(
                "event=RISK_JOURNAL_SAVE ok=0 action=safe_mode path=%s err=%s",
                path, e, exc_info=True
            )
    def can_open(
        self,
        symbol: str,
        notional_irt: float,
        cash_irt: float,
        *,
        max_notional_frac: Optional[float] = None,
    ) -> bool:
        self._roll_day()
        now = time.time()
        try:
            symbol = _canon_symbol(symbol)
        except Exception:
            symbol = str(symbol or "")
        if self.safe_mode:
            return False
        notional_irt = float(notional_irt)
        cash_irt = float(cash_irt)
        if notional_irt < float(self.cfg.min_notional_irt):
            return False
        if cash_irt <= 0.0 or notional_irt > cash_irt:
            return False
        frac = (
            float(max_notional_frac)
            if max_notional_frac is not None
            else float(getattr(self.cfg, "max_notional_frac", 1.0))
        )
        frac = clamp(frac, 0.0, 1.0)
        if notional_irt > cash_irt * frac:
            return False
        until = self.blocked_until.get(symbol, 0.0)
        if until > now:
            return False
        return True
    def can_open_explain(
        self,
        symbol: str,
        notional_irt: float,
        cash_irt: float,
        *,
        max_notional_frac: Optional[float] = None,
    ) -> Tuple[bool, str, dict]:
        self._roll_day()
        now = time.time()
        try:
            sym = _canon_symbol(symbol)
        except Exception:
            sym = str(symbol or "")
        try:
            notional_irt = float(notional_irt)
        except Exception:
            notional_irt = 0.0
        try:
            cash_irt = float(cash_irt)
        except Exception:
            cash_irt = 0.0
        if self.safe_mode and self.safe_level() == "HARD":
            try:
                grace = float(_env_float("SNIPER_GRACE_TRADE_DATA_AGE_SEC", 60.0) or 60.0)
            except Exception:
                grace = 60.0
            sr = str(self.safe_reason or "")
            try:
                if (sr.startswith("HEALTH_WD_") or sr.startswith("HEALTH_SYS_")) and ("mkt=" in sr or "top8=" in sr):
                    try:
                        try:
                            import re as _re
                        except:
                            pass
                    except:
                        pass
                    def _age(tag: str):
                        m = _re.search(rf"{tag}([0-9]+(?:\.[0-9]+)?)s", sr)
                        return float(m.group(1)) if m else None
                    mkt_age = _age("mkt=")
                    top8_age = _age("top8=")
                    net_bad = ("net=" in sr) and any(k in sr for k in ("ERR", "FAIL", "TIMEOUT", "DOWN"))
                    if (not net_bad) and (mkt_age is not None) and (top8_age is not None) and (mkt_age <= grace) and (top8_age <= grace):
                        return True, "SAFE_BYPASS_DATA_AGE", {"safe_reason": sr, "grace_sec": grace}
            except Exception:
                pass
            return False, "SAFE_MODE", {"safe_reason": sr, "safe_level": self.safe_level()}
        if notional_irt < float(self.cfg.min_notional_irt):
            return False, "NOTIONAL_SMALL", {"notional": notional_irt, "min_notional": float(self.cfg.min_notional_irt)}
        if cash_irt <= 0.0:
            return False, "NO_CASH", {"cash": cash_irt}
        if notional_irt > cash_irt:
            return False, "NOTIONAL_GT_CASH", {"notional": notional_irt, "cash": cash_irt}
        frac = (
            float(max_notional_frac)
            if max_notional_frac is not None
            else float(getattr(self.cfg, "max_notional_frac", 1.0))
        )
        frac = clamp(frac, 0.0, 1.0)
        if notional_irt > cash_irt * frac:
            return False, "FRACTION_CAP", {"notional": notional_irt, "cash": cash_irt, "frac": frac}
        until = float(self.blocked_until.get(sym, 0.0) or 0.0)
        if until > now:
            return False, "SYMBOL_COOLDOWN", {"until": until, "now": now}
        return True, "OK", {}
    def size_notional(self, cash_irt: float, base_cap_irt: float, confidence: float) -> float:
        cash_f = max(0.0, float(cash_irt))
        cap = max(0.0, float(base_cap_irt))
        if cash_f <= 0.0 or cap <= 0.0:
            return 0.0
        conf = clamp(float(confidence), 0.0, 1.0)
        try:
            kf = float(self.memory.kelly_fraction())
        except Exception:
            kf = 1.0
        kf = clamp(kf, 0.25, 1.25)
        eff_frac = (0.12 + 0.58 * conf) * (0.55 + 0.45 * kf)
        eff_frac = clamp(eff_frac, 0.05, 0.85)
        out = min(cap, cash_f * eff_frac)
        min_n = float(getattr(self.cfg, "min_notional_irt", 0.0) or 0.0)
        if min_n > 0.0 and cash_f >= min_n:
            out = max(out, min(min_n, cap, cash_f))
        return float(clamp(out, 0.0, cap))
    def register_close(self, symbol: str, pnl_irt: float, pnl_pct: float, cash_irt: Optional[float] = None) -> None:
        self._roll_day()
        try:
            sym = _canon_symbol(symbol)
        except Exception:
            sym = str(symbol or "")
        if pnl_pct != 0:
            self.memory.record(pnl_pct)
        if pnl_irt < 0:
            self.daily_loss_irt += abs(pnl_irt)
            self._save_risk_journal()
            streak = self.consecutive_losses.get(sym, 0) + 1
            self.consecutive_losses[sym] = streak
            if streak >= 3:
                cooldown = float(_env_float("LOSS_COOLDOWN_SEC", 600.0))
                self.blocked_until[sym] = time.time() + cooldown
                self._logger.warning("Symbol cooldown: %s blocked for %.0fs", sym, cooldown)
            cash_ref = 0.0
            try:
                cash_ref = float(self.global_cash_total_irt())
            except Exception:
                cash_ref = 0.0
            if cash_ref <= 0.0:
                cash_ref = float(cash_irt) if cash_irt is not None else 0.0
            if cash_ref > 0 and self.daily_loss_irt >= cash_ref * self.cfg.max_daily_loss_pct:
                self.halt_new_trades("MAX_DAILY_LOSS")
        else:
            self.consecutive_losses[sym] = 0
    def should_exit(self, pos: Position, book: OrderBookTop, score: float, cfg: Optional[BotConfig] = None) -> Tuple[bool, str]:
        c = cfg if cfg is not None else self.cfg
        if pos.qty <= 0:
            return False, ""
        exit_px = float(getattr(book, "bid", 0.0) or 0.0)
        try:
            if bool(getattr(book, "_stale", False)):
                exit_px = float(getattr(book, "mid", exit_px) or exit_px)
            else:
                src0 = str(getattr(book, "_source", "") or "").lower().strip()
                if src0.startswith(("spot", "synth", "disk")):
                    exit_px = float(getattr(book, "mid", exit_px) or exit_px)
        except Exception:
            pass
        pnl_pct = (exit_px - pos.entry_px) / pos.entry_px if pos.entry_px > 0 else 0.0
        try:
            sl = abs(float(getattr(c, "stop_loss_pct", 0.0) or 0.0))
        except Exception:
            sl = abs(float(getattr(self.cfg, "stop_loss_pct", 0.0) or 0.0))
        try:
            tp = abs(float(getattr(c, "take_profit_pct", 0.0) or 0.0))
        except Exception:
            tp = abs(float(getattr(self.cfg, "take_profit_pct", 0.0) or 0.0))
        try:
            sth = abs(float(getattr(c, "sell_threshold", 0.20) or 0.20))
        except Exception:
            sth = abs(float(getattr(self.cfg, "sell_threshold", 0.20) or 0.20))
        if sl > 0.0 and pnl_pct <= -sl:
            return True, f"STOP_LOSS({pnl_pct*100:.2f}%)"
        if tp > 0.0 and pnl_pct >= tp:
            return True, f"TAKE_PROFIT({pnl_pct*100:.2f}%)"
        try:
            min_hold = float(getattr(c, "min_hold_sec", 0.0) or 0.0)
        except Exception:
            min_hold = float(getattr(self.cfg, "min_hold_sec", 0.0) or 0.0)
        if min_hold > 0.0:
            try:
                age = float(time.time() - float(getattr(pos, "entry_ts", 0.0) or 0.0))
            except Exception:
                age = 0.0
            if age >= 0.0 and age < min_hold and score <= -sth:
                return False, f"MIN_HOLD({age:.1f}s<{min_hold:.0f}s)"
        if score <= -sth:
            return True, "SIGNAL_REVERSAL"
        return False, ""
    def to_dict(self) -> dict:
        return {
            "safe_mode": self.safe_mode,
            "safe_reason": self.safe_reason,
            "daily_loss_irt": self.daily_loss_irt,
            "day_key": self._day_key,
            "consecutive_losses": self.consecutive_losses,
            "blocked_until": self.blocked_until,
            "memory": self.memory.to_dict(),
        }
    def load_dict(self, d: dict) -> None:
        try:
            self.safe_mode = bool(d.get("safe_mode", False))
            self.safe_reason = str(d.get("safe_reason", ""))
            self.daily_loss_irt = float(d.get("daily_loss_irt", 0.0))
            self._day_key = str(d.get("day_key", time.strftime("%Y-%m-%d")))
            self.consecutive_losses = {str(k): int(v) for k, v in (d.get("consecutive_losses") or {}).items()}
            self.blocked_until = {str(k): float(v) for k, v in (d.get("blocked_until") or {}).items()}
            mem = d.get("memory") or {}
            if isinstance(mem, dict):
                self.memory = TradingMemory.from_dict(mem)
        except Exception as e:
            self.safe_mode = True
            self.safe_reason = f"CORRUPTED_STATE:{type(e).__name__}"
            self._logger.critical(
                "event=RISK_STATE_CORRUPT action=safe_mode reason=%s err=%s",
                self.safe_reason, e,
                exc_info=True,
            )
            if not self.cfg.dry_run:
                raise RuntimeError("Refusing to trade: risk state load failed") from e
    def set_safe(self, on: bool, reason: str = "") -> None:
        try:
            onb = bool(on)
        except Exception:
            onb = True
        if onb:
            try:
                self.halt_new_trades(str(reason or "SAFE_MODE"))
            except Exception:
                self.safe_mode = True
                self.safe_reason = str(reason or "SAFE_MODE")
                self.safe_since_ts = float(time.time())
        else:
            try:
                min_safe = float(_env_float("SAFE_MODE_MIN_DURATION_SEC", 10.0) or 10.0)
            except Exception:
                min_safe = 10.0
            try:
                if bool(self.safe_mode) and float(self.safe_since_ts or 0.0) > 0.0 and (time.time() - float(self.safe_since_ts)) < float(min_safe):
                    return
            except Exception:
                pass
            try:
                self.safe_mode = False
                self.safe_reason = ""
                self.safe_since_ts = 0.0
            except Exception:
                pass
            try:
                self._save_risk_journal()
            except Exception:
                pass