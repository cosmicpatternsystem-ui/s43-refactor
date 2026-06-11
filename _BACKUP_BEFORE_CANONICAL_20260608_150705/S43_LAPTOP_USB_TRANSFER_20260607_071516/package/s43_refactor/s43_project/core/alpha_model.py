from .order_book_top import OrderBookTop
from .edge_model_v2 import EdgeModelV2
from .price_history import PriceHistory
from .signal import Signal
from .__noop_lock import _NoopLock
from .bot_config import BotConfig
from .__symbol_state import _SymbolState

class AlphaModel:
    _REGIME_LOCK = _NoopLock()
    _REGIME_BY_SYMBOL: Dict[str, dict] = {}
    def __init__(self, cfg: BotConfig):
        self.cfg = cfg
        self.core = EdgeModelV2()
        self.state: Dict[str, _SymbolState] = {}
        self._hist: Dict[str, PriceHistory] = {}
        self._last_signals: Dict[str, Signal] = {}
        self._bar_sec = float(getattr(cfg, "alpha_bar_sec", 2.0) or 2.0)
        self._rsi_period = int(getattr(cfg, "alpha_rsi_period", 14) or 14)
        self._adx_period = int(getattr(cfg, "alpha_adx_period", 14) or 14)
        self._vfi_period = int(getattr(cfg, "alpha_vfi_period", 30) or 30)
        self._min_confirm_trending = int(getattr(cfg, "alpha_min_confirm_trending", 2) or 2)
        self._min_confirm_ranging = int(getattr(cfg, "alpha_min_confirm_ranging", 2) or 2)
        self._min_confirm_volatile = int(getattr(cfg, "alpha_min_confirm_volatile", 3) or 3)
        self._max_spread_bps = float(getattr(cfg, "alpha_max_spread_bps", 35.0) or 35.0)
    @classmethod
    def get_regime(cls, symbol: str) -> dict:
        sym = _canon_symbol(symbol)
        try:
            with cls._REGIME_LOCK:
                v = cls._REGIME_BY_SYMBOL.get(sym) or {}
            return v if isinstance(v, dict) else {}
        except Exception:
            return {}
    @staticmethod
    def _clamp01(x: float) -> float:
        return float(clamp(float(x), 0.0, 1.0))
    @staticmethod
    def _ema(prev: float, x: float, alpha: float) -> float:
        try:
            if prev == 0.0:
                return float(x)
            return float(prev) + float(alpha) * (float(x) - float(prev))
        except Exception:
            return float(x)
    @staticmethod
    def _estimate_volume(book: OrderBookTop) -> float:
        try:
            v = 0.0
            def _qty(lvl: Any) -> float:
                try:
                    if isinstance(lvl, dict):
                        for kk in ("amount", "qty", "quantity", "q", "vol", "volume", "size", "sz"):
                            if lvl.get(kk) is not None:
                                return float(lvl.get(kk) or 0.0)
                        return 0.0
                    if isinstance(lvl, (list, tuple)) and len(lvl) >= 2:
                        return float(lvl[1] or 0.0)
                except Exception:
                    return 0.0
                return 0.0
            for lvl in (book.bids or [])[:3]:
                v += float(_qty(lvl))
            for lvl in (book.asks or [])[:3]:
                v += float(_qty(lvl))
            return max(0.0, float(v) * 0.35)
        except Exception:
            return 0.0
    def _update_history(self, sym: str, book: OrderBookTop) -> PriceHistory:
        now = float(time.time())
        hist = self._hist.get(sym)
        if hist is None:
            hist = PriceHistory(symbol=sym)
            self._hist[sym] = hist
        bid = float(book.bid)
        ask = float(book.ask)
        mid = float(book.mid)
        vol = self._estimate_volume(book)
        spr_bps = 0.0
        try:
            if mid > 0:
                spr_bps = ((ask - bid) / mid) * 10_000.0
        except Exception:
            spr_bps = 0.0
        if not hist.timestamps or (now - float(hist.timestamps[-1])) >= self._bar_sec:
            o = float(hist.closes[-1]) if hist.closes else mid
            h = max(mid, o)
            l = min(mid, o)
            hist.opens.append(float(o))
            hist.highs.append(float(h))
            hist.lows.append(float(l))
            hist.closes.append(float(mid))
            hist.volumes.append(float(vol))
            hist.timestamps.append(float(now))
        else:
            try:
                hist.highs[-1] = float(max(float(hist.highs[-1]), mid))
                hist.lows[-1] = float(min(float(hist.lows[-1]), mid))
                hist.closes[-1] = float(mid)
                hist.volumes[-1] = float(max(0.0, float(hist.volumes[-1]) + float(vol)))
            except Exception:
                pass
        try:
            setattr(hist, "_last_spread_bps", float(spr_bps))
        except Exception:
            pass
        return hist
    def _calc_rsi_pair(self, closes: List[float]) -> Tuple[float, float]:
        p = int(max(5, self._rsi_period))
        if len(closes) < p + 6:
            return (50.0, 50.0)
        now = _calc_rsi(closes, p)
        prev = _calc_rsi(closes[:-5], p)
        return (float(now), float(prev))
    def _calc_atr_adx(self, highs: List[float], lows: List[float], closes: List[float]) -> Tuple[float, float, float, float]:
        n = int(max(8, self._adx_period))
        if len(closes) < n + 2:
            return (0.0, 0.0, 0.0, 0.0)
        tr = []
        pdm = []
        mdm = []
        for i in range(1, len(closes)):
            h = float(highs[i]); l = float(lows[i]); pc = float(closes[i-1])
            up = float(h - float(highs[i-1]))
            dn = float(float(lows[i-1]) - l)
            tr_i = max(h - l, abs(h - pc), abs(l - pc))
            tr.append(float(tr_i))
            pdm.append(float(up) if (up > dn and up > 0) else 0.0)
            mdm.append(float(dn) if (dn > up and dn > 0) else 0.0)
        def wilder_smooth(arr: List[float], period: int) -> List[float]:
            out = []
            if len(arr) < period:
                return out
            s = sum(arr[:period])
            out.append(float(s))
            for x in arr[period:]:
                s = float(s - (s / period) + float(x))
                out.append(float(s))
            return out
        tr_s = wilder_smooth(tr, n)
        pdm_s = wilder_smooth(pdm, n)
        mdm_s = wilder_smooth(mdm, n)
        if not tr_s or len(tr_s) != len(pdm_s) or len(tr_s) != len(mdm_s):
            return (0.0, 0.0, 0.0, 0.0)
        pdi = []
        mdi = []
        dx = []
        for t, p, m in zip(tr_s, pdm_s, mdm_s):
            t = float(max(1e-12, t))
            pdi_v = 100.0 * float(p) / t
            mdi_v = 100.0 * float(m) / t
            pdi.append(float(pdi_v))
            mdi.append(float(mdi_v))
            den = max(1e-12, float(pdi_v + mdi_v))
            dx.append(100.0 * abs(float(pdi_v - mdi_v)) / den)
        adx_s = wilder_smooth(dx, n)
        adx = float(adx_s[-1] / n) if adx_s else 0.0
        atr = float(tr_s[-1] / n)
        return (float(atr), float(adx), float(pdi[-1] if pdi else 0.0), float(mdi[-1] if mdi else 0.0))
    def _calc_vfi(self, highs: List[float], lows: List[float], closes: List[float], vols: List[float]) -> float:
        n = int(max(12, self._vfi_period))
        if len(closes) < n + 2 or len(vols) < n + 2:
            return 0.0
        tp = [(float(h) + float(l) + float(c)) / 3.0 for h, l, c in zip(highs, lows, closes)]
        vr = []
        for i in range(1, len(tp)):
            a = float(tp[i]); b = float(tp[i-1])
            if a > 0 and b > 0:
                vr.append(abs(math.log(a / b)))
        if not vr:
            return 0.0
        vcut = float(sorted(vr[-(n*2):])[max(0, int(0.80 * min(len(vr), n*2)) - 1)]) if vr else 0.0
        vcut = max(1e-8, float(vcut))
        vbar = sum(float(x) for x in vols[-n:]) / float(n)
        vcap = max(1e-12, float(vbar) * 2.5)
        mf = 0.0
        for i in range(-n, 0):
            chg = float(tp[i] - tp[i-1])
            if abs(chg) <= float(tp[i-1]) * vcut:
                continue
            v_i = min(float(vols[i]), vcap)
            mf += float(chg) * v_i
        den = max(1e-9, float(vbar) * float(tp[-1]))
        vfi = float(mf / den)
        return float(math.tanh(vfi * 6.0))
    def _detect_regime(self, atr: float, adx: float, mid: float) -> Tuple[str, float]:
        atr_pct = (float(atr) / max(1e-12, float(mid))) * 100.0 if mid > 0 else 0.0
        if atr_pct >= float(getattr(self.cfg, "regime_vol_atr_pct", 1.35) or 1.35):
            strength = self._clamp01((atr_pct - 1.35) / 2.0)
            return ("VOLATILE", float(strength))
        if adx >= float(getattr(self.cfg, "regime_trend_adx", 23.0) or 23.0):
            strength = self._clamp01((float(adx) - 23.0) / 22.0)
            return ("TRENDING", float(strength))
        strength = self._clamp01((23.0 - float(adx)) / 23.0)
        return ("RANGING", float(strength))
    def evaluate(self, symbol: str, book: OrderBookTop) -> Signal:
        sym = _canon_symbol(symbol)

        # CORE LOGIC FIX: do not let stale/synthetic books contaminate Alpha history.
        # Stale books can be used for exit pricing, but must not generate new Alpha signals.
        try:
            if book is None or bool(getattr(book, "_stale", False)) or (str(getattr(book, "_source", "") or "").upper().strip() == "SPOT_READY"):
                px = 0.0
                try:
                    px = float(getattr(book, "mid", 0.0) or 0.0) if book is not None else 0.0
                except Exception:
                    px = 0.0
                meta = {"stale": True}
                try:
                    if book is not None:
                        meta.update({
                            "source": str(getattr(book, "_source", "") or ""),
                            "age_sec": float(getattr(book, "age_sec", 0.0) or 0.0),
                        })
                except Exception:
                    pass
                sig = Signal(action="HOLD", symbol=sym, score=0.0, confidence=0.0,
                             price=float(px), reason="STALE_BOOK", meta=meta)
                self._last_signals[sym] = sig
                return sig
        except Exception:
            pass
        st = self.state.setdefault(sym, _SymbolState())
        score, diag = self.core.score(st, book)
        hist = self._update_history(sym, book)
        spr_bps = float(getattr(hist, "_last_spread_bps", 0.0) or 0.0)
        if spr_bps > self._max_spread_bps:
            diag2 = dict(diag or {})
            diag2["spread_bps"] = float(spr_bps)
            sig = Signal(action="HOLD", symbol=sym, score=float(score), confidence=0.0,
                         price=float(book.mid), reason="SPREAD_GUARD", meta=diag2)
            self._last_signals[sym] = sig
            try:
                with AlphaModel._REGIME_LOCK:
                    AlphaModel._REGIME_BY_SYMBOL[sym] = {"state": "VOLATILE", "strength": 0.2, "spread_bps": float(spr_bps)}
            except Exception:
                pass
            return sig
        closes = list(hist.closes)
        highs = list(hist.highs)
        lows = list(hist.lows)
        vols = list(hist.volumes)
        rsi_now, rsi_prev = self._calc_rsi_pair(closes)
        rsi_mom = float(rsi_now - rsi_prev)
        atr, adx, pdi, mdi = self._calc_atr_adx(highs, lows, closes)
        vfi = self._calc_vfi(highs, lows, closes, vols)
        regime, reg_strength = self._detect_regime(atr=atr, adx=adx, mid=float(book.mid))
        trend_dir = 0
        try:
            if pdi > mdi:
                trend_dir = +1
            elif mdi > pdi:
                trend_dir = -1
        except Exception:
            trend_dir = 0
        div_buy = False
        div_sell = False
        try:
            if len(closes) >= 8:
                p_mom = (float(closes[-1]) - float(closes[-6])) / max(1e-12, float(closes[-6]))
                div_buy = (p_mom < -0.002) and (rsi_mom > 1.5) and (rsi_now <= 55.0)
                div_sell = (p_mom > 0.002) and (rsi_mom < -1.5) and (rsi_now >= 45.0)
        except Exception:
            div_buy, div_sell = False, False
        vfi_buy = bool(vfi > 0.12)
        vfi_sell = bool(vfi < -0.12)
        c_buy = bool((adx >= 18.0) and (trend_dir > 0))
        c_sell = bool((adx >= 18.0) and (trend_dir < 0))
        if str(regime).upper() == "VOLATILE":
            min_confirm = self._min_confirm_volatile
        elif str(regime).upper() == "TRENDING":
            min_confirm = self._min_confirm_trending
        else:
            min_confirm = self._min_confirm_ranging
        buy_thr = abs(float(self.cfg.buy_threshold))
        sell_thr = abs(float(self.cfg.sell_threshold))
        action = "HOLD"
        confirm = 0
        if score >= buy_thr:
            confirm = int(div_buy) + int(vfi_buy) + int(c_buy)
            if confirm >= int(min_confirm):
                action = "BUY"
        elif score <= -sell_thr:
            confirm = int(div_sell) + int(vfi_sell) + int(c_sell)
            if confirm >= int(min_confirm):
                action = "SELL"
        base = self._clamp01(abs(float(score)))
        conf = self._clamp01(0.55 * base + 0.18 * float(confirm) + 0.10 * self._clamp01(float(adx) / 35.0))
        if action == "HOLD":
            conf = min(conf, 0.45)
        meta = dict(diag or {})
        meta.update({
            "spread_bps": float(spr_bps),
            "rsi": float(rsi_now),
            "rsi_mom": float(rsi_mom),
            "vfi": float(vfi),
            "atr": float(atr),
            "adx": float(adx),
            "pdi": float(pdi),
            "mdi": float(mdi),
            "regime": str(regime),
            "regime_strength": float(reg_strength),
            "confirm": int(confirm),
            "layers": {
                "A_rsi_div": bool(div_buy if (action == "BUY" or (action == "HOLD" and score > 0)) else (div_sell if (action == "SELL" or (action == "HOLD" and score < 0)) else (div_buy or div_sell))),
                "B_vfi": bool(vfi_buy if (action == "BUY" or (action == "HOLD" and score > 0)) else (vfi_sell if (action == "SELL" or (action == "HOLD" and score < 0)) else (vfi_buy or vfi_sell))),
                "C_adx": bool(c_buy if (action == "BUY" or (action == "HOLD" and score > 0)) else (c_sell if (action == "SELL" or (action == "HOLD" and score < 0)) else (c_buy or c_sell))),
            },
        })
        reason = "EDGE_V2+TRIPLE_CONFIRM"
        sig = Signal(action=action, symbol=sym, score=float(score), confidence=float(conf), price=float(book.mid), reason=reason, meta=meta)
        self._last_signals[sym] = sig
        try:
            with AlphaModel._REGIME_LOCK:
                AlphaModel._REGIME_BY_SYMBOL[sym] = {
                    "state": str(regime),
                    "strength": float(reg_strength),
                    "adx": float(adx),
                    "atr": float(atr),
                    "spread_bps": float(spr_bps),
                    "ts": float(time.time()),
                }
        except Exception:
            pass
        return sig