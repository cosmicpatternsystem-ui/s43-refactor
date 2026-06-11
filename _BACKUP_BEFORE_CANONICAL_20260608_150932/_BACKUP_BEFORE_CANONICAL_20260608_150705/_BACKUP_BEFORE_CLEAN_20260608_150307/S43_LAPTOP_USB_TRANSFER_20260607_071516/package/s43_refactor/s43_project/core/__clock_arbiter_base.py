from .clock_arbiter import ClockArbiter

class _ClockArbiterBase:
    def __init__(self, ema_alpha: float = 0.12):
        self._alpha = float(ema_alpha)
        self._offset_ema: Optional[float] = None
        try:
            self._mono0 = float(time.monotonic())
        except Exception:
            self._mono0 = 0.0
        try:
            self._wall0 = float(time.time())
        except Exception:
            self._wall0 = 0.0
        self._last_resync_wall = float(self._wall0)
        self._last_resync_mono = float(self._mono0)
    def now(self) -> float:
        try:
            m = float(time.monotonic())
            if self._mono0 <= 0.0:
                self._mono0 = m
                self._wall0 = float(time.time())
            return float(self._wall0) + max(0.0, m - float(self._mono0))
        except Exception:
            return float(time.time())
    def resync(self, jump_threshold_s: float = 0.75) -> float:
        try:
            wall = float(time.time())
            mono_wall = float(self.now())
            diff = float(wall - mono_wall)
            if abs(diff) >= float(jump_threshold_s):
                self._wall0 = float(self._wall0) + diff
                if self._offset_ema is not None and math.isfinite(self._offset_ema):
                    self._offset_ema = float(self._offset_ema) - diff
                self._last_resync_wall = wall
                try:
                    self._last_resync_mono = float(time.monotonic())
                except Exception:
                    pass
            return diff
        except Exception:
            return 0.0
    @staticmethod
    def _epoch_to_seconds(ts: Any) -> float:
        return float(_epoch_to_sec(ts))
    @staticmethod
    def _normalize_server_time(st: float) -> float:
        return float(_ClockArbiterBase._epoch_to_seconds(st))
    def observe(self, local_now_s: float, server_time: float) -> None:
        try:
            st = self._normalize_server_time(float(server_time))
            ln = float(local_now_s)
            if st <= 0.0 or ln <= 0.0:
                return
            off = st - ln
            if self._offset_ema is None or not math.isfinite(self._offset_ema):
                self._offset_ema = off
            else:
                a = self._alpha
                self._offset_ema = (1.0 - a) * float(self._offset_ema) + a * off
        except Exception:
            return
    def skew_s(self, local_now_s: float, server_time: Optional[float]) -> float:
        try:
            if server_time is None:
                return float("inf")
            st = self._normalize_server_time(float(server_time))
            if self._offset_ema is None or not math.isfinite(self._offset_ema):
                return abs(float(local_now_s) - st)
            return abs((float(local_now_s) + float(self._offset_ema)) - st)
        except Exception:
            return float("inf")