from .phoenix_decision import PhoenixDecision
from .order_book_top import OrderBookTop
from .logger import Logger
from .bot_config import BotConfig
from .sanity_status import SanityStatus
from .wallet_runtime import WalletRuntime

class SanityHaltController:
    def __init__(self, cfg: BotConfig, logger: logging.Logger):
        self.cfg = cfg
        self._log = logger
        self._st: Dict[Tuple[str, str], SanityStatus] = {}
    @staticmethod
    def _lvl_amt(x: Any) -> float:
        if isinstance(x, dict):
            for k in ("amount", "qty", "volume", "size", "q"):
                if k in x:
                    try:
                        return float(x.get(k) or 0.0)
                    except Exception:
                        return 0.0
        if isinstance(x, (list, tuple)) and len(x) >= 2:
            try:
                return float(x[1] or 0.0)
            except TradingHalt:
                raise
            except Exception:
                return 0.0
        return 0.0
    def _key(self, wallet: WalletRuntime, sym: str) -> Tuple[str, str]:
        return (str(getattr(wallet, "name", "W?")), _canon_symbol(sym))
    def evaluate(self, wallet: WalletRuntime, sym: str, book: OrderBookTop, spot: Optional[float], depth_latency_ms: Optional[float], pho: Optional[PhoenixDecision]) -> Tuple[bool, str]:
        if not bool(self.cfg.sanity_enabled):
            return False, ""
        now = time.time()
        key = self._key(wallet, sym)
        st = self._st.get(key)
        if st is None:
            st = SanityStatus()
            self._st[key] = st
        mid = float(getattr(book, "mid", 0.0) or 0.0)
        spr_bps = float(getattr(book, "spread_bps", 0.0) or 0.0)
        spot_px = float(spot or 0.0) if (spot is not None) else 0.0
        if mid > 0.0:
            if st.ema_mid <= 0.0:
                st.ema_mid = mid
            else:
                st.ema_mid = (0.80 * st.ema_mid) + (0.20 * mid)
        liq = 0.0
        liq_valid = True
        try:
            bids = getattr(book, "bids", None) or []
            asks = getattr(book, "asks", None) or []
            liq_valid = bool(bids) or bool(asks)
            top_n = 5
            liq_b = sum(self._lvl_amt(b) for b in (bids[:top_n] if isinstance(bids, list) else []))
            liq_a = sum(self._lvl_amt(a) for a in (asks[:top_n] if isinstance(asks, list) else []))
            liq = float(max(0.0, liq_b + liq_a))
        except Exception:
            liq_valid = False
            liq = 0.0
        if liq_valid:
            st.liq_hist.append(liq)
            if liq > 0.0:
                if st.ema_liq <= 0.0:
                    st.ema_liq = liq
                else:
                    st.ema_liq = (0.85 * st.ema_liq) + (0.15 * liq)
        depth_spot_dev = 0.0
        if (spot_px > 0.0) and (mid > 0.0):
            depth_spot_dev = abs(mid - spot_px) / spot_px
        dev_pct = 0.0
        if st.ema_mid > 0.0 and mid > 0.0:
            dev_pct = abs(mid - st.ema_mid) / st.ema_mid
        liq_drop = 1.0
        if liq_valid and st.ema_liq > 0.0:
            liq_drop = liq / st.ema_liq
        liq_cv = 0.0
        try:
            vals = [float(x) for x in st.liq_hist if float(x) > 0.0]
            if len(vals) >= 6:
                mu = sum(vals) / float(len(vals))
                if mu > 0.0:
                    var = sum((v - mu) ** 2 for v in vals) / float(len(vals))
                    liq_cv = math.sqrt(var) / mu
        except Exception:
            liq_cv = 0.0
        lat_ms = float(depth_latency_ms or 0.0)
        div = False
        div_code = ""
        try:
            if pho and pho.rsi is not None and pho.shadow_score is not None:
                rsi = float(pho.rsi)
                sh = float(pho.shadow_score)
                rsi_thr = float(self.cfg.sanity_divergence_rsi_thr)
                sh_thr = float(self.cfg.sanity_divergence_shadow_thr)
                if rsi >= rsi_thr and sh <= -abs(sh_thr):
                    div = True; div_code = "RSI_UP_SHADOW_DOWN"
                elif rsi <= (100.0 - rsi_thr) and sh >= abs(sh_thr):
                    div = True; div_code = "RSI_DOWN_SHADOW_UP"
        except Exception:
            div = False
            div_code = ""
        reasons = []
        if (spot_px > 0.0) and (depth_spot_dev > float(self.cfg.sanity_depth_spot_thr)):
            allow_spot_dev = True
            try:
                max_lat = float(getattr(self.cfg, "sanity_spot_dev_max_lat_ms", 1800.0) or 1800.0)
                if float(lat_ms or 0.0) > max_lat:
                    allow_spot_dev = False
            except Exception:
                pass
            try:
                min_liq = float(getattr(self.cfg, "sanity_spot_dev_min_liq", 0.01) or 0.01)
                if (not bool(liq_valid)) or float(liq or 0.0) <= min_liq:
                    allow_spot_dev = False
            except Exception:
                pass
            if allow_spot_dev:
                reasons.append(f"DEPTH_SPOT_DEV {depth_spot_dev:.4f}")
        dev_thr = float(self.cfg.sanity_max_dev_pct)
        try:
            if pho and bool(getattr(pho, "ready", False)):
                comp = abs(float(getattr(pho, "composite", 0.0) or 0.0))
                conf = float(getattr(pho, "confidence", 0.0) or 0.0)
                if comp >= 0.35 and conf >= 0.35:
                    dev_thr *= 1.8
        except Exception:
            pass
        try:
            if (spr_bps > 0.0) and (spr_bps <= float(self.cfg.sanity_spread_bps_thr) * 0.85) and (liq_drop >= 0.90):
                dev_thr *= 1.3
        except Exception:
            pass
        dev_thr = float(min(0.12, max(0.005, dev_thr)))
        if dev_pct > dev_thr:
            reasons.append(f"MID_DEV {dev_pct:.4f} thr={dev_thr:.4f}")
        if (lat_ms > 0.0) and (lat_ms > float(self.cfg.sanity_latency_ms)):
            reasons.append(f"LATENCY {lat_ms:.0f}ms")
        if liq_valid and (st.ema_liq > 0.0) and (liq_drop < float(self.cfg.sanity_liq_drop_ratio)):
            reasons.append(f"LIQ_DROP {liq_drop:.2f}")
        if liq_valid and (liq_cv > float(self.cfg.sanity_liq_cv_thr)) and (spr_bps > float(self.cfg.sanity_spread_bps_thr)):
            reasons.append(f"SPOOFISH cv={liq_cv:.2f} spr={spr_bps:.1f}bps")
        if div:
            reasons.append(f"DIVERGENCE {div_code}")
        triggered = bool(reasons)
        mid_dev_only = (len(reasons) == 1) and str(reasons[0]).startswith("MID_DEV")
        if mid_dev_only:
            st.active = True
            st.soft = True
            st.reason = str(reasons[0])[:220]
            st.since_ts = now if st.since_ts <= 0.0 else st.since_ts
            try:
                soft_hold = float(getattr(self.cfg, "sanity_soft_mid_hold_sec", 6.0) or 6.0)
            except Exception:
                soft_hold = 6.0
            soft_hold = float(max(2.0, min(float(self.cfg.sanity_hold_sec), soft_hold)))
            st.until_ts = max(float(st.until_ts), now + soft_hold)
            st.ok_streak = 0
            try:
                wallet.sanity_halt = False
                wallet.sanity_reason = ""
                wallet.sanity_until_ts = 0.0
            except Exception:
                pass
            try:
                self._log.info(
                    "event=SANITY_SOFT_BLOCK wallet=%s sym=%s reason=%s mid=%.0f ema=%.0f dev=%.4f",
                    getattr(wallet, "name", "?"),
                    _canon_symbol(sym),
                    st.reason,
                    mid,
                    float(st.ema_mid or 0.0),
                    float(dev_pct or 0.0),
                )
            except Exception:
                pass
            return True, st.reason
        severe = False
        try:
            sev_mult = float(getattr(self.cfg, "sanity_severe_mult", 2.0) or 2.0)
            sev_mult = max(1.0, sev_mult)
        except Exception:
            sev_mult = 2.0
        if triggered and (not bool(st.active)):
            try:
                if (spot_px > 0.0) and (depth_spot_dev > float(self.cfg.sanity_depth_spot_thr) * sev_mult):
                    severe = True
            except Exception:
                pass
            try:
                if dev_pct > float(self.cfg.sanity_max_dev_pct) * sev_mult:
                    severe = True
            except Exception:
                pass
            try:
                if (lat_ms > 0.0) and (lat_ms > float(self.cfg.sanity_latency_ms) * sev_mult):
                    severe = True
            except Exception:
                pass
            try:
                liq_sev_thr = max(0.05, float(self.cfg.sanity_liq_drop_ratio) * 0.5)
                if (st.ema_liq > 0.0) and (liq_drop < liq_sev_thr):
                    severe = True
            except Exception:
                pass
            try:
                if spr_bps > float(self.cfg.sanity_spread_bps_thr) * sev_mult:
                    severe = True
            except Exception:
                pass
        if triggered:
            if (not bool(st.active)) and (not severe):
                hits_req = 2
                win = 2.0
                try:
                    hits_req = max(1, int(getattr(self.cfg, "sanity_debounce_hits", 2) or 2))
                except Exception:
                    hits_req = 2
                try:
                    win = float(getattr(self.cfg, "sanity_debounce_window_sec", 2.0) or 2.0)
                    win = max(0.2, win)
                except Exception:
                    win = 2.0
                try:
                    if (float(st.debounce_window_start_ts) <= 0.0) or ((now - float(st.debounce_window_start_ts)) > win):
                        st.debounce_window_start_ts = now
                        st.debounce_hits = 0
                    st.debounce_hits = int(st.debounce_hits) + 1
                except Exception:
                    st.debounce_window_start_ts = now
                    st.debounce_hits = 1
                if int(st.debounce_hits) < int(hits_req):
                    pend_reason = ("PENDING(%d/%d) " % (int(st.debounce_hits), int(hits_req))) + (" | ".join(reasons)[:200])
                    try:
                        wallet.sanity_halt = True
                        wallet.sanity_reason = pend_reason[:220]
                        wallet.sanity_until_ts = now + min(win, 1.0)
                    except Exception:
                        pass
                    try:
                        if int(st.debounce_hits) == 1:
                            self._log.info("event=SANITY_PENDING wallet=%s sym=%s reason=%s", getattr(wallet, "name", "?"), _canon_symbol(sym), pend_reason[:180])
                    except Exception:
                        pass
                    return True, pend_reason[:220]
            try:
                st.debounce_hits = 0
                st.debounce_window_start_ts = 0.0
            except Exception:
                pass
            st.active = True
            st.soft = False
            st.reason = " | ".join(reasons)[:220]
            st.since_ts = now if st.since_ts <= 0.0 else st.since_ts
            st.until_ts = max(float(st.until_ts), now + float(self.cfg.sanity_hold_sec))
            st.ok_streak = 0
            try:
                wallet.sanity_halt = True
                wallet.sanity_reason = st.reason
                wallet.sanity_until_ts = st.until_ts
            except Exception:
                pass
            try:
                self._log.warning("event=SANITY_HALT wallet=%s sym=%s reason=%s mid=%.0f spot=%.0f spr_bps=%.1f liq=%.2f lat_ms=%.0f",
                                  getattr(wallet, "name", "?"), _canon_symbol(sym), st.reason, mid, spot_px, spr_bps, liq, lat_ms)
            except Exception:
                pass
            return True, st.reason
        if st.active:
            if bool(getattr(st, "soft", False)):
                if now < float(st.until_ts):
                    try:
                        wallet.sanity_halt = False
                        wallet.sanity_reason = ""
                        wallet.sanity_until_ts = 0.0
                    except Exception:
                        pass
                    return True, st.reason
            else:
                if now < float(st.until_ts):
                    try:
                        wallet.sanity_halt = True
                        wallet.sanity_reason = st.reason
                        wallet.sanity_until_ts = st.until_ts
                    except Exception:
                        pass
                    return True, st.reason
            st.ok_streak += 1
            if st.ok_streak >= int(self.cfg.sanity_clear_ok):
                st.active = False
                st.soft = False
                old = st.reason
                st.reason = ""
                st.since_ts = 0.0
                st.until_ts = 0.0
                st.ok_streak = 0
                try:
                    wallet.sanity_halt = False
                    wallet.sanity_reason = ""
                    wallet.sanity_until_ts = 0.0
                except Exception:
                    pass
                try:
                    self._log.info("event=SANITY_CLEAR wallet=%s sym=%s prev=%s", getattr(wallet, "name", "?"), _canon_symbol(sym), old[:180])
                except Exception:
                    pass
                return False, ""
            else:
                try:
                    if bool(getattr(st, "soft", False)):
                        wallet.sanity_halt = False
                        wallet.sanity_reason = ""
                        wallet.sanity_until_ts = 0.0
                    else:
                        wallet.sanity_halt = True
                        wallet.sanity_reason = st.reason
                        wallet.sanity_until_ts = st.until_ts
                except Exception:
                    pass
                return True, st.reason
        try:
            wallet.sanity_halt = False
            wallet.sanity_reason = ""
            wallet.sanity_until_ts = 0.0
        except Exception:
            pass
        return False, ""