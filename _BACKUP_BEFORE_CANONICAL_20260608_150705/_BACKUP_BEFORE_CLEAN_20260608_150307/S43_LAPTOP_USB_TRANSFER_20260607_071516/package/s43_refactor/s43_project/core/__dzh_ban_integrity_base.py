from .phoenix_decision import PhoenixDecision
from .dzh_ban_integrity import DzhBanIntegrity
from .logger import Logger
from .signal import Signal
from .bot_config import BotConfig
from .wallet_runtime import WalletRuntime

class _DzhBanIntegrityBase:
    def __init__(self, cfg: "BotConfig", logger: logging.Logger):
        self.cfg = cfg
        self._log = logger
        self._alpha_hist: Dict[str, deque] = {}
        self._last_tune_ts: Dict[str, float] = {}
        self._last_metrics_ts: Dict[str, float] = {}
    def _net_alpha(self, wallet: str) -> float:
        dq = self._alpha_hist.get(wallet)
        if not dq:
            return 0.0
        try:
            return float(sum(dq)) / float(len(dq))
        except Exception:
            return 0.0
    def observe_alpha(self, wallet: "WalletRuntime", sig: "Signal") -> None:
        if not bool(getattr(wallet.cfg, "dzh_net_alpha", True)):
            return
        try:
            span = int(getattr(wallet.cfg, "dzh_net_alpha_span", 50) or 50)
            dq = self._alpha_hist.get(wallet.name)
            if dq is None:
                dq = __import__("collections").deque(maxlen=max(10, span))
                self._alpha_hist[wallet.name] = dq
            dq.append(float(getattr(sig, "score", 0.0) or 0.0))
        except Exception:
            pass
    def evaluate_entry(
        self,
        wallet: "WalletRuntime",
        sym: str,
        book: "OrderBook",
        sig: "Signal",
        pho: "PhoenixDecision",
        top8_row: Optional[dict],
        mids: Optional[List[float]] = None,
    ) -> Tuple[bool, str]:
        if not bool(getattr(wallet.cfg, "autonomous_ai", False)):
            return False, "AUTONOMOUS_AI_OFF"
        try:
            gate_mode = str(getattr(wallet.cfg, "phoenix_gate_mode", "soft") or "soft").strip().lower()
        except Exception:
            gate_mode = "soft"
        try:
            st0 = str(getattr(pho, "state", "FLAT") or "FLAT").upper()
        except Exception:
            st0 = "FLAT"
        if st0 == "FLAT":
            try:
                ready = bool(getattr(pho, "ready", False))
            except Exception:
                ready = False
            if gate_mode in ("hard", "strict", "1", "true", "on"):
                return False, ("PHOENIX_FLAT" if ready else "PHOENIX_WARMUP")
            if gate_mode in ("soft", "adaptive"):
                try:
                    raz_conf = float(getattr(sig, "confidence", 0.0) or 0.0)
                    raz_score = float(getattr(sig, "score", 0.0) or 0.0)
                    raz_conf = float(raz_conf) if math.isfinite(float(raz_conf)) else 0.0
                    raz_score = float(raz_score) if math.isfinite(float(raz_score)) else 0.0
                    fb_conf = float(getattr(wallet.cfg, "phoenix_fallback_raz_conf", 0.60) or 0.60)
                    fb_score = float(getattr(wallet.cfg, "phoenix_fallback_raz_score", 0.22) or 0.22)
                    if (raz_conf < fb_conf) or (raz_score < fb_score):
                        return False, ("PHOENIX_FLAT" if ready else "PHOENIX_WARMUP")
                except Exception:
                    return False, ("PHOENIX_FLAT" if ready else "PHOENIX_WARMUP")
        if bool(getattr(wallet.cfg, "dzh_safety_entry", True)):
            try:
                spr = float(getattr(book, "spread_bps", 0.0) or 0.0)
                max_bps = float(getattr(wallet.cfg, "dzh_spread_max_bps", 35.0) or 35.0)
                try:
                    hard_bps = float(getattr(wallet.cfg, "dzh_spread_hard_bps", 0.0) or 0.0)
                except Exception:
                    hard_bps = 0.0
                if hard_bps <= 0.0:
                    hard_bps = max(250.0, max_bps * 7.0)
                if spr >= float(hard_bps):
                    return False, f"SPREAD_HARD>{spr:.1f}bps"
                if spr > float(max_bps) and spr > 0.0:
                    mult = float(max(0.15, min(1.0, float(max_bps) / float(spr))))
                    try:
                        setattr(sig, "dzh_entry_mult", mult)
                        setattr(sig, "dzh_reason", f"SPREAD_SOFT>{spr:.1f}bps")
                    except Exception:
                        pass
            except Exception:
                return False, "SPREAD_CHECK_ERR"
            try:
                if isinstance(top8_row, dict) and top8_row.get("liq_irt") is not None:
                    liq = float(top8_row.get("liq_irt") or 0.0)
                    min_liq = float(getattr(wallet.cfg, "dzh_liquidity_min_irt", 0.0) or 0.0)
                    if min_liq > 0.0 and liq < min_liq:
                        qccy = "IRT"
                        try:
                            _b, qccy = _split_pair(sym)
                            qccy = str(qccy or "").upper().strip() or "IRT"
                        except Exception:
                            qccy = "IRT"
                        tag = "LIQ_USDT_LOW" if qccy == "USDT" else "LIQ_IRT_LOW"
                        return False, f"{tag} liq_irt={liq:,.0f} min_irt={min_liq:,.0f}"
            except Exception:
                return False, "LIQ_CHECK_ERR"
            try:
                act = str(getattr(sig, "action", "") or "").upper().strip()
                ref = float(getattr(sig, "price", 0.0) or 0.0)
                if ref <= 0.0:
                    ref = float(getattr(book, "mid", 0.0) or 0.0)
                mid = float(getattr(book, "mid", 0.0) or 0.0)
                live = 0.0
                if act.startswith("S"):
                    live = float(getattr(book, "bid", 0.0) or 0.0)
                else:
                    live = float(getattr(book, "ask", 0.0) or 0.0)
                if ref > 0.0 and live > 0.0:
                    if act.startswith("S"):
                        gap_bps = max(0.0, (1.0 - (live / ref))) * 10000.0
                    else:
                        gap_bps = max(0.0, ((live / ref) - 1.0)) * 10000.0
                    base_thr = float(getattr(wallet.cfg, "slippage_bps", 0.0) or 0.0)
                    safety = float(getattr(wallet.cfg, "order_safety_bps", 0.0) or 0.0)
                    extra = float(getattr(wallet.cfg, "dzh_price_gap_extra_bps", 5.0) or 5.0)
                    thr = float(getattr(wallet.cfg, "dzh_price_gap_slippage_bps", 0.0) or 0.0)
                    if thr <= 0.0:
                        thr = max(8.0, base_thr + safety + extra)
                    if gap_bps > thr:
                        return False, f"PRICE_GAP_SLIPPAGE gap={gap_bps:.1f}bps thr={thr:.1f} ref={ref:.0f} live={live:.0f} mid={mid:.0f}"
            except Exception:
                return False, "PRICE_GAP_CHECK_ERR"
            try:
                if mids and len(mids) >= 8:
                    mean = float(sum(mids[-8:])) / float(len(mids[-8:]))
                    if mean > 0 and float(getattr(book, "mid", 0.0) or 0.0) > 0:
                        bps = ((float(book.mid) / mean) - 1.0) * 10000.0
                        if bps > float(getattr(wallet.cfg, "dzh_fake_breakout_bps", 0.0) or 0.0):
                            return False, f"FAKE_BRK>{bps:.1f}bps"
            except Exception:
                pass
        if bool(getattr(wallet.cfg, "dzh_veto_htf", True)):
            try:
                if mids and len(mids) >= 20:
                    x0 = float(mids[-20])
                    x1 = float(mids[-1])
                    slope = (x1 / x0) - 1.0 if x0 > 0 else 0.0
                    thr = float(getattr(wallet.cfg, "dzh_htf_reject_thr", 0.42) or 0.42)
                    if float(getattr(pho, "confidence", 0.0) or 0.0) < thr and slope < 0:
                        return False, f"HTF_REJECT slope={slope*100:.2f}%"
            except Exception:
                return False, "HTF_CHECK_ERR"
        return True, "OK"
    def tune_wallet(self, wallet: "WalletRuntime") -> None:
        if not (bool(getattr(wallet.cfg, "dzh_auto_tune", True)) or bool(getattr(wallet.cfg, "dzh_dyn_tune", True))):
            return
        now = time.time()
        last = float(self._last_tune_ts.get(wallet.name, 0.0) or 0.0)
        if (now - last) < 3.0:
            return
        self._last_tune_ts[wallet.name] = now
        base = float(getattr(wallet.cfg, "max_notional_frac", 0.0) or 0.0)
        if base <= 0:
            base = 0.10
        scale = 1.0
        if bool(getattr(wallet.cfg, "dzh_auto_tune", True)):
            a = self._net_alpha(wallet.name)
            a = max(-1.0, min(1.0, float(a)))
            u = 0.5 * (a + 1.0)
            lo = float(getattr(wallet.cfg, "dzh_risk_scale_min", 0.35) or 0.35)
            hi = float(getattr(wallet.cfg, "dzh_risk_scale_max", 1.0) or 1.0)
            scale = lo + (hi - lo) * u
        if bool(getattr(wallet.cfg, "dzh_dyn_tune", True)):
            try:
                vol = abs(float(getattr(wallet, "pnl_unrealized_irt", 0.0) or 0.0))
                damp = 1.0 / (1.0 + (vol / 50_000_000.0))
                scale *= max(0.25, min(1.0, damp))
            except Exception:
                pass
        wallet.dyn_max_notional_frac = float(clamp(base * scale, 0.01, 0.50))