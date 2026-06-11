from .phoenix_decision import PhoenixDecision
from .order_book_top import OrderBookTop
from .logger import Logger
from .signal import Signal
from .bot_config import BotConfig

class PhoenixEngine:
    @dataclass
    class _State:
        mids: deque
        prev: Optional[float] = None
        rsi_count: int = 0
        sum_gain: float = 0.0
        sum_loss: float = 0.0
        avg_gain: float = 0.0
        avg_loss: float = 0.0
        last_decision: Optional[PhoenixDecision] = None
        last_update_ts: float = 0.0
    def __init__(self, cfg: BotConfig, logger: logging.Logger):
        self.cfg = cfg
        self._log = logger
        self._st: Dict[str, PhoenixEngine._State] = {}
        self._maxlen = int(max(64, (int(cfg.phoenix_shadow_window) * 4)))
        self._state_path = os.getenv("PHOENIX_STATE_PATH", "phoenix_state.json")
        self._last_save_ts = 0.0
        self._load_persisted_states()
    def _resolve_sym(self, sym: str) -> str:
        """Resolve base asset symbols to the best available market pair.

        """
        try:
            raw = str(sym or "").strip()
        except Exception:
            raw = ""
        s = _canon_symbol(raw)
        if not s:
            return ""
        for q in ("IRT", "IRR", "USDT", "USD", "USDC", "BTC", "ETH", "TMN"):
            try:
                if s.endswith(q) and len(s) > len(q):
                    return s
            except Exception:
                continue
        try:
            smap = getattr(self, "_symbol_map", None)
            if isinstance(smap, dict):
                mapped = smap.get(s) or smap.get(s.upper()) or smap.get(s.lower())
                if mapped:
                    return _canon_symbol(str(mapped))
        except Exception:
            pass
        try:
            dq = str(getattr(self.cfg, "quote", "IRT") or "IRT").upper()
        except Exception:
            dq = "IRT"
        try:
            return _canon_pair(s, dq)
        except Exception:
            return s
    def _state(self, sym: str) -> "PhoenixEngine._State":
        sym = self._resolve_sym(sym)
        st = self._st.get(sym)
        if st is None:
            st = PhoenixEngine._State(mids=__import__("collections").deque(maxlen=self._maxlen))
            self._st[sym] = st
        return st
    def get_last_decision(self, sym: str) -> Optional[PhoenixDecision]:
        try:
            st = self._state(sym)
            return st.last_decision
        except Exception:
            return None
    def _state_to_dict(self, st: "PhoenixEngine._State") -> dict:
        try:
            return {
                "mids": list(getattr(st, "mids", []) or []),
                "prev": getattr(st, "prev", None),
                "rsi_count": int(getattr(st, "rsi_count", 0) or 0),
                "sum_gain": float(getattr(st, "sum_gain", 0.0) or 0.0),
                "sum_loss": float(getattr(st, "sum_loss", 0.0) or 0.0),
                "avg_gain": float(getattr(st, "avg_gain", 0.0) or 0.0),
                "avg_loss": float(getattr(st, "avg_loss", 0.0) or 0.0),
                "last_decision": (st.last_decision.to_dict() if getattr(st, "last_decision", None) is not None else None),
                "last_update_ts": float(getattr(st, "last_update_ts", 0.0) or 0.0),
            }
        except Exception:
            return {}
    def _dict_to_state(self, data: dict) -> "PhoenixEngine._State":
        st = PhoenixEngine._State(mids=__import__("collections").deque(maxlen=self._maxlen))
        if not isinstance(data, dict):
            return st
        try:
            mids = data.get("mids") or []
            if isinstance(mids, list):
                st.mids.extend([float(x) for x in mids[-self._maxlen:] if x is not None])
        except Exception:
            pass
        try:
            st.prev = (float(data.get("prev")) if data.get("prev") is not None else None)
        except Exception:
            st.prev = None
        try:
            st.rsi_count = int(data.get("rsi_count") or 0)
            st.sum_gain = float(data.get("sum_gain") or 0.0)
            st.sum_loss = float(data.get("sum_loss") or 0.0)
            st.avg_gain = float(data.get("avg_gain") or 0.0)
            st.avg_loss = float(data.get("avg_loss") or 0.0)
            st.last_update_ts = float(data.get("last_update_ts") or 0.0)
        except Exception:
            pass
        try:
            ld = data.get("last_decision")
            if isinstance(ld, dict):
                st.last_decision = PhoenixDecision.from_dict(ld)
        except Exception:
            st.last_decision = None
        return st
    def _load_persisted_states(self) -> None:
        path = str(getattr(self, "_state_path", "") or "")
        if not path:
            return
        try:
            if not os.path.exists(path):
                return
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return
            for sym, st_data in data.items():
                try:
                    cs = _canon_symbol(str(sym))
                    self._st[cs] = self._dict_to_state(st_data)
                except Exception:
                    continue
        except Exception:
            return
    def save(self) -> None:
        path = str(getattr(self, "_state_path", "") or "")
        if not path:
            return
        try:
            payload = {sym: self._state_to_dict(st) for sym, st in (getattr(self, "_st", {}) or {}).items()}
            tmp = f"{path}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            try:
                os.replace(tmp, path)
            except Exception:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(payload, f)
        except Exception:
            return
    def _update_rsi(self, st: "PhoenixEngine._State", price: float) -> Optional[float]:
        period = int(max(2, int(self.cfg.phoenix_rsi_period)))
        if st.prev is None:
            st.prev = float(price)
            return None
        delta = float(price) - float(st.prev)
        st.prev = float(price)
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)
        if st.rsi_count < period:
            st.sum_gain += gain
            st.sum_loss += loss
            st.rsi_count += 1
            if st.rsi_count == period:
                st.avg_gain = st.sum_gain / float(period)
                st.avg_loss = st.sum_loss / float(period)
            return None
        st.avg_gain = (st.avg_gain * float(period - 1) + gain) / float(period)
        st.avg_loss = (st.avg_loss * float(period - 1) + loss) / float(period)
        if st.avg_loss <= 1e-12:
            if st.avg_gain <= 1e-12:
                return 50.0
            return 100.0
        rs = st.avg_gain / st.avg_loss
        return 100.0 - (100.0 / (1.0 + rs))
    def _shadow(self, mids: List[float]) -> Tuple[Optional[float], str]:
        n = int(max(8, int(self.cfg.phoenix_shadow_window)))
        if len(mids) < n:
            return None, "WARMUP"
        w = mids[-n:]
        cur = float(w[-1])
        hi = max(w); lo = min(w)
        rng = float(hi - lo)
        if rng <= 0.0:
            return None, "RANGE0"
        k = max(3, n // 5)
        idx_hi = max(range(n), key=lambda i: w[i])
        idx_lo = min(range(n), key=lambda i: w[i])
        hi_rej = 0.0
        lo_rej = 0.0
        rej_thr = 0.15
        if idx_hi >= (n - k):
            hi_rej = max(0.0, (hi - cur) / rng)
            if hi_rej < rej_thr:
                hi_rej = 0.0
        if idx_lo >= (n - k):
            lo_rej = max(0.0, (cur - lo) / rng)
            if lo_rej < rej_thr:
                lo_rej = 0.0
        pos = (2.0 * cur - hi - lo) / rng
        pos = clamp(pos, -1.0, 1.0)
        score = clamp((lo_rej - hi_rej) + 0.20 * pos, -1.0, 1.0)
        return float(score), "OK"
    def update(self, sym: str, sig: Optional[Signal], book: Optional[OrderBookTop], spot: Optional[float], depth_latency_ms: Optional[float] = None, book_ts: Optional[float] = None, spot_ts: Optional[float] = None) -> PhoenixDecision:
        sym = self._resolve_sym(sym)
        st = self._state(sym)
        mid = 0.0
        try:
            if book is not None:
                mid = float(getattr(book, "mid", 0.0) or 0.0)
        except Exception:
            mid = 0.0
        try:
            if book is not None and bool(getattr(book, "_stale", False)):
                mid = 0.0
        except Exception:
            pass
        sp = 0.0
        try:
            sp = float(spot or 0.0)
        except Exception:
            sp = 0.0
        synth_spot = False
        try:
            if book is not None:
                _src_tag = str(getattr(book, "_source", "") or "").upper()
                if _src_tag.startswith("SPOT") or _src_tag in ("SPOT_READY", "SPOT_FALLBACK"):
                    synth_spot = True
        except Exception:
            synth_spot = False
        if synth_spot:
            if sp <= 0.0 and mid > 0.0:
                sp = float(mid)
            mid = 0.0
        px = 0.0
        source = "none"
        if mid > 0.0:
            px = mid
            source = "depth"
        elif sp > 0.0:
            px = sp
            source = "spot"
        if px <= 0.0:
            stale = PhoenixDecision(
                state="FLAT",
                confidence=0.0,
                composite=0.0,
                rsi=50.0,
                shadow_score=0.0,
                shadow_label="NO_DATA",
                ready=False,
                reason="NO_PRICE",
            )
            st.last_decision = stale
            return stale
        now_ts = time.time()
        ts_px = None
        try:
            if source == "depth":
                ts_px = _parse_ts_sec(book_ts) or _parse_ts_sec(getattr(book, "ts", None)) or _parse_ts_sec(getattr(book, "timestamp", None))
            elif source == "spot":
                ts_px = _parse_ts_sec(spot_ts) or _parse_ts_sec(book_ts) or (_parse_ts_sec(getattr(book, "ts", None)) if book is not None else None) or (_parse_ts_sec(getattr(book, "timestamp", None)) if book is not None else None)
        except Exception:
            ts_px = None
        try:
            stale_after = float(os.getenv("HEALTH_MKT_MAX_AGE_SEC", "90") or 90.0)
        except Exception:
            stale_after = 90.0
        stale_after = float(max(1.0, stale_after))
        age_px = None
        try:
            if ts_px is not None:
                age_px = max(0.0, float(now_ts) - float(ts_px))
        except Exception:
            age_px = None
        allow_spot_ready = bool(_env_bool("PHOENIX_ALLOW_SPOT_READY", bool(getattr(self.cfg, "phoenix_allow_spot_ready", False))))
        depth_required_only = bool(source == "spot" and (not allow_spot_ready))
        if depth_required_only:
            dec = PhoenixDecision(
                state="FLAT",
                confidence=float(getattr(sig, "confidence", 0.0) or 0.0) if sig is not None else 0.0,
                composite=float(getattr(sig, "score", 0.0) or 0.0) if sig is not None else 0.0,
                rsi=50.0,
                shadow_score=0.0,
                shadow_label="DEPTH_REQUIRED",
                ready=False,
                reason="NO_DEPTH_PRICE",
            )
            st.last_decision = dec
            return dec
        if ts_px is None:
            dec = PhoenixDecision(
                state="FLAT",
                confidence=float(getattr(sig, "confidence", 0.0) or 0.0) if sig is not None else 0.0,
                composite=float(getattr(sig, "score", 0.0) or 0.0) if sig is not None else 0.0,
                rsi=50.0,
                shadow_score=0.0,
                shadow_label="NO_TS",
                ready=False,
                reason="NO_TS",
            )
            st.last_decision = dec
            return dec
        if age_px is not None and age_px > stale_after:
            dec = PhoenixDecision(
                state="FLAT",
                confidence=float(getattr(sig, "confidence", 0.0) or 0.0) if sig is not None else 0.0,
                composite=float(getattr(sig, "score", 0.0) or 0.0) if sig is not None else 0.0,
                rsi=50.0,
                shadow_score=0.0,
                shadow_label="STALE_PRICE",
                ready=False,
                reason="NO_FRESH_PRICE",
            )
            st.last_decision = dec
            return dec
        try:
            st.last_update_ts = float(ts_px)
        except Exception:
            pass
        try:
            st.mids.append(float(px))
        except Exception:
            pass
        rsi_raw = None
        try:
            rsi_raw = self._update_rsi(st, float(px))
        except Exception:
            rsi_raw = None
        rsi_ready = bool(rsi_raw is not None)
        try:
            rsi = float(rsi_raw) if rsi_raw is not None else 50.0
        except Exception:
            rsi = 50.0
        shadow_score, shadow_label = self._shadow(list(st.mids))
        if depth_required_only:
            shadow_label = "DEPTH_REQUIRED"
        ready_shadow = bool(str(shadow_label or "") == "OK")
        hard_ready = bool(rsi_ready and ready_shadow and (source == "depth"))
        soft_ready = bool(rsi_ready and ready_shadow and (source in ("depth", "spot")))
        ready = bool(soft_ready if allow_spot_ready else hard_ready)
        if depth_required_only:
            ready = False
        sig_score = 0.0
        sig_conf = 0.0
        if sig is not None:
            try:
                sig_score = float(getattr(sig, "score", 0.0) or 0.0)
            except Exception:
                sig_score = 0.0
            try:
                sig_conf = float(getattr(sig, "confidence", 0.0) or 0.0)
            except Exception:
                sig_conf = 0.0
        sig_score = clamp(sig_score, -1.0, 1.0)
        sig_conf = clamp(sig_conf, 0.0, 1.0)
        rsi_norm = 0.0 if rsi is None else clamp((50.0 - float(rsi)) / 50.0, -1.0, 1.0)
        sh_norm = clamp(float(shadow_score or 0.0), -1.0, 1.0)
        w_sig = float(self.cfg.phoenix_w_sig)
        w_rsi = float(self.cfg.phoenix_w_rsi)
        w_sh = float(self.cfg.phoenix_w_shadow)
        ws = max(1e-9, abs(w_sig) + abs(w_rsi) + abs(w_sh))
        w_sig, w_rsi, w_sh = w_sig / ws, w_rsi / ws, w_sh / ws
        composite = (w_sig * sig_score) + (w_rsi * rsi_norm) + (w_sh * sh_norm)
        composite = clamp(float(composite), -1.0, 1.0)
        entry_thr = float(max(1e-6, abs(float(self.cfg.phoenix_entry_thr))))
        # Previous decision state (for deterministic anti-flip behavior)
        prev_dec = st.last_decision
        prev_state = "FLAT"
        try:
            prev_state = str(getattr(prev_dec, "state", "FLAT") or "FLAT").upper().strip()
        except Exception:
            prev_state = "FLAT"
        # Enforce confidence gating for entries (uses Termux adaptive min_conf when enabled)
        min_conf = abs(float(getattr(self.cfg, "phoenix_min_conf", entry_thr) or entry_thr))
        try:
            entry_thr, min_conf, _sm, _resc, _tag = _termux_adaptive_phoenix_gate(self.cfg)
            entry_thr = float(max(1e-6, float(entry_thr)))
            min_conf = float(min_conf)
        except Exception:
            pass
        try:
            min_conf = clamp(float(min_conf), 0.0, 1.0)
        except Exception:
            min_conf = 0.0
        state = "FLAT"
        if ready:
            if composite >= entry_thr:
                state = "LONG"
            elif composite <= -entry_thr:
                state = "SHORT"
            else:
                state = "FLAT"
        mag = abs(composite) / max(1e-9, entry_thr)
        mag = max(0.0, mag)
        comp_conf = 1.0 - math.exp(-mag)
        base_conf = clamp(0.40 * sig_conf + 0.60 * comp_conf, 0.0, 1.0)
        if ready:
            dq = (0.85 if source == "spot" else 1.0)
        elif ready_shadow:
            dq = 0.55
        elif len(getattr(st, "mids", []) or []) >= 2:
            dq = 0.25
        else:
            dq = 0.10 if px > 0.0 else 0.0
        if source == "spot" and not ready:
            dq = min(dq, 0.35)
        confidence = clamp(base_conf * dq, 0.0, 1.0)
        # Entry gating: require confidence >= min_conf for LONG/SHORT.
        if ready and state != "FLAT" and float(confidence) < float(min_conf):
            state = "FLAT"
        # Anti-flip: never jump LONG<->SHORT in a single Phoenix tick.
        if prev_state == "LONG" and state == "SHORT":
            state = "FLAT"
        elif prev_state == "SHORT" and state == "LONG":
            state = "FLAT"
        if ready:
            reason = ("PHOENIX_OK_SPOT" if source == "spot" else "PHOENIX_OK")
        else:
            reason = f'PHOENIX_{str(shadow_label or "WARMUP")}_{source.upper()}'
        prev_dec = st.last_decision
        dec = PhoenixDecision(
            state=state,
            confidence=float(confidence),
            composite=float(composite),
            rsi=float(rsi),
            shadow_score=(float(shadow_score) if shadow_score is not None else 0.0),
            shadow_label=str(shadow_label),
            ready=bool(ready),
            reason=str(reason),
        )
        st.last_decision = dec
        try:
            now = float(time.time())
            last_map = getattr(self, "_phoenix_last_evt_ts", None)
            if not isinstance(last_map, dict):
                last_map = {}
                setattr(self, "_phoenix_last_evt_ts", last_map)
            prev_state = str(getattr(prev_dec, "state", "") or "").upper().strip() if prev_dec is not None else ""
            cur_state = str(getattr(dec, "state", "") or "").upper().strip()
            last_ts = float(last_map.get(sym, 0.0) or 0.0)
            if (cur_state != prev_state) or ((now - last_ts) >= float(_env_float("PHOENIX_EVENT_MIN_GAP_SEC", 30.0) or 30.0)):
                last_map[sym] = now
                self._log.info(
                    "event=PHOENIX sym=%s state=%s ready=%s comp=%.3f conf=%.3f rsi=%.1f shadow=%.3f(%s) src=%s reason=%s",
                    sym,
                    cur_state,
                    bool(getattr(dec, "ready", False)),
                    float(getattr(dec, "composite", 0.0) or 0.0),
                    float(getattr(dec, "confidence", 0.0) or 0.0),
                    float(getattr(dec, "rsi", 0.0) or 0.0),
                    float(getattr(dec, "shadow_score", 0.0) or 0.0),
                    str(getattr(dec, "shadow_label", "") or ""),
                    str(source or ""),
                    str(getattr(dec, "reason", "") or ""),
                )
        except Exception:
            pass
        try:
            now = float(time.time())
            if (now - float(getattr(self, "_last_save_ts", 0.0) or 0.0)) >= 60.0:
                self._last_save_ts = now
                self.save()
        except Exception:
            pass
        return dec