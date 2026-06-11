from .order_book_top import OrderBookTop
from .__symbol_state import _SymbolState

class EdgeModelV2:
    def __init__(self):
        self.fast_period = _env_int("EDGE_FAST_PERIOD", 12)
        self.slow_period = _env_int("EDGE_SLOW_PERIOD", 48)
        self.vol_period = _env_int("EDGE_VOL_PERIOD", 48)
        self.book_levels = _env_int("EDGE_BOOK_LEVELS", 10)
        self.book_alpha = _env_float("EDGE_BOOK_ALPHA", 0.15)
        self.w_mom = _env_float("EDGE_W_MOM", 0.72)
        self.w_imb = _env_float("EDGE_W_IMB", 0.22)
        self.w_micro = _env_float("EDGE_W_MICRO", 0.16)
        self.w_spread = _env_float("EDGE_W_SPREAD", 0.38)
        self.mom_scale = _env_float("EDGE_MOM_SCALE", 1.25)
        self.imb_scale = _env_float("EDGE_IMB_SCALE", 2.40)
        self.micro_scale = _env_float("EDGE_MICRO_SCALE", 160.0)
        self.spread_ref_bps = _env_float("EDGE_SPREAD_REF_BPS", 35.0)
        self.vol_target_bps = _env_float("EDGE_VOL_TARGET_BPS", 18.0)
        self.vol_damp = _env_float("EDGE_VOL_DAMP", 0.55)
        self.use_log_returns = _env_bool("EDGE_LOG_RETURNS", True)
        self.fast_alpha = 2.0 / (self.fast_period + 1.0)
        self.slow_alpha = 2.0 / (self.slow_period + 1.0)
        self.vol_alpha = 2.0 / (self.vol_period + 1.0)
        self.spread_alpha_up = _env_float("EDGE_SPREAD_ALPHA_UP", self.book_alpha)
        self.spread_alpha_dn = _env_float("EDGE_SPREAD_ALPHA_DN", 0.35)
    @staticmethod
    def _ema(prev: float, x: float, a: float) -> float:
        return x if prev == 0.0 else (prev + a * (x - prev))
    @staticmethod
    def _lvl_qty(lvl: Any) -> float:
        if isinstance(lvl, dict):
            return float(lvl.get("amount") or lvl.get("volume") or 0.0)
        if isinstance(lvl, (list, tuple)) and len(lvl) >= 2:
            return float(lvl[1] or 0.0)
        return 0.0
    def _book_features(self, bid: float, ask: float, mid: float, bids: List[Any], asks: List[Any]) -> Tuple[float, float, float]:
        spr = spread_bps(bid, ask)
        bw = 0.0
        aw = 0.0
        for i in range(min(self.book_levels, len(bids))):
            bw += (1.0 / (i + 1.0)) * self._lvl_qty(bids[i])
        for i in range(min(self.book_levels, len(asks))):
            aw += (1.0 / (i + 1.0)) * self._lvl_qty(asks[i])
        denom = bw + aw
        imb = (bw - aw) / denom if denom > 0 else 0.0
        b0q = self._lvl_qty(bids[0]) if bids else 0.0
        a0q = self._lvl_qty(asks[0]) if asks else 0.0
        micro = mid
        if bid > 0 and ask > 0 and (b0q + a0q) > 0:
            micro = (bid * a0q + ask * b0q) / (b0q + a0q)
        micro_p = (micro - mid) / mid if mid > 0 else 0.0
        return float(imb), float(micro_p), float(spr)
    def score(self, st: _SymbolState, book: OrderBookTop) -> Tuple[float, Dict[str, float]]:
        bid, ask, mid = float(book.bid), float(book.ask), float(book.mid)
        if st.last_mid > 0:
            r = math.log(mid / st.last_mid) if self.use_log_returns else (mid - st.last_mid) / max(1e-12, st.last_mid)
            st.returns.append(float(r))
            st.ema_var = self._ema(st.ema_var, float(r * r), self.vol_alpha)
        else:
            st.ema_var = 0.0
        st.last_mid = mid
        st.ema_fast = self._ema(st.ema_fast, mid, self.fast_alpha)
        st.ema_slow = self._ema(st.ema_slow, mid, self.slow_alpha)
        imb, micro_p, spr_bps = self._book_features(bid=bid, ask=ask, mid=mid, bids=book.bids, asks=book.asks)
        st.ema_imb = self._ema(st.ema_imb, imb, self.book_alpha)
        st.ema_micro = self._ema(st.ema_micro, micro_p, self.book_alpha)
        a = self.spread_alpha_up if spr_bps >= st.ema_spread_bps else self.spread_alpha_dn
        st.ema_spread_bps = self._ema(st.ema_spread_bps, spr_bps, clamp(a, 0.01, 0.85))
        mom_bps = ((st.ema_fast - st.ema_slow) / mid) * 10_000.0 if mid > 0 else 0.0
        vol_bps = math.sqrt(max(0.0, st.ema_var)) * 10_000.0
        mom_comp = math.tanh((mom_bps / max(1e-9, self.vol_target_bps)) * self.mom_scale)
        imb_comp = math.tanh(st.ema_imb * self.imb_scale)
        micro_comp = math.tanh(st.ema_micro * self.micro_scale)
        spread_pen = clamp(st.ema_spread_bps / max(1e-9, self.spread_ref_bps), 0.0, 3.0)
        spread_comp = -math.tanh(spread_pen) * self.w_spread
        vol_ratio = vol_bps / max(1e-9, self.vol_target_bps)
        damp = 1.0 / (1.0 + self.vol_damp * max(0.0, vol_ratio - 1.0))
        raw = (self.w_mom * mom_comp) + (self.w_imb * imb_comp) + (self.w_micro * micro_comp) + spread_comp
        score = clamp(float(raw * damp), -1.0, 1.0)
        st.last_score = score
        diag = {
            "mom_bps": float(mom_bps),
            "vol_bps": float(vol_bps),
            "imb": float(st.ema_imb),
            "micro": float(st.ema_micro),
            "spr_bps": float(st.ema_spread_bps),
            "damp": float(damp),
        }
        return score, diag