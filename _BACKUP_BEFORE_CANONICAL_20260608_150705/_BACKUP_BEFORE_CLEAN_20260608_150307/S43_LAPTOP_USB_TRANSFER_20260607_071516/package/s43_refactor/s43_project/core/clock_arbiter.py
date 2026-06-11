from .logger import Logger
from .__clock_arbiter_base import _ClockArbiterBase

class ClockArbiter(_ClockArbiterBase):
    def __init__(self, ema_alpha: float = 0.12, *args: Any, log: Optional[logging.Logger] = None, **kwargs: Any) -> None:
        try:
            if "ema_alpha" in kwargs:
                ema_alpha = float(kwargs.pop("ema_alpha") or ema_alpha)
        except Exception:
            pass
        skew_alpha_override: Optional[float] = None
        try:
            if "skew_ema_alpha" in kwargs:
                skew_alpha_override = float(kwargs.pop("skew_ema_alpha"))
        except Exception:
            skew_alpha_override = None
        try:
            kwargs.pop("log", None)
        except Exception:
            pass
        try:
            super().__init__(ema_alpha=float(ema_alpha or 0.12))
        except TypeError:
            try:
                super().__init__(float(ema_alpha or 0.12))
            except Exception:
                super().__init__()
        self._log = log
        self._skew_ema: Optional[float] = None
        base_skew_alpha = float(_env_float("SKEW_EMA_ALPHA", 0.15))
        try:
            if skew_alpha_override is not None and math.isfinite(float(skew_alpha_override)):
                self._skew_alpha = float(skew_alpha_override)
            else:
                self._skew_alpha = float(base_skew_alpha)
        except Exception:
            self._skew_alpha = float(base_skew_alpha)
    def _normalize_server_time(self, server_ts: Any) -> float:
        return float(_epoch_to_sec(server_ts))
    def skew_s(self, server_ts: Any, now: Optional[float] = None) -> float:
        try:
            now_s = float(_epoch_to_sec(time.time() if now is None else now))
            st = float(self._normalize_server_time(server_ts))
            if st <= 0.0 or now_s <= 0.0:
                return float("inf")
            raw = abs(float(now_s) - float(st))
            if self._skew_ema is None or (not math.isfinite(self._skew_ema)):
                self._skew_ema = raw
            else:
                a = max(0.0, min(1.0, float(self._skew_alpha)))
                self._skew_ema = (a * raw) + ((1.0 - a) * float(self._skew_ema))
            return float(self._skew_ema)
        except Exception:
            return float("inf")