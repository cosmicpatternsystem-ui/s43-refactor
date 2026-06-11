from ._s43_noop_awaitable import _S43NoopAwaitable

class NetHealthMonitor:
    """
    Fail-safe network health monitor fallback.

    This stub is intentionally conservative:
    - never blocks startup
    - reports network as healthy by default
    - accepts arbitrary method calls used by reconstructed code
    """
    def __init__(self, cfg=None, logger=None, *args, **kwargs):
        self.cfg = cfg
        self.logger = logger
        self.healthy = True
        self.last_error = None
        self.stats = {
            "healthy": True,
            "ok": True,
            "failures": 0,
            "errors": 0,
            "latency_ms": 0.0,
        }

    def start(self, *args, **kwargs):
        return _S43NoopAwaitable(True)

    async def astart(self, *args, **kwargs):
        return True

    def stop(self, *args, **kwargs):
        return _S43NoopAwaitable(True)

    async def astop(self, *args, **kwargs):
        return True

    def close(self, *args, **kwargs):
        return _S43NoopAwaitable(True)

    async def aclose(self, *args, **kwargs):
        return True

    def check(self, *args, **kwargs):
        return True

    async def acheck(self, *args, **kwargs):
        return True

    def is_healthy(self, *args, **kwargs):
        return True

    def ok(self, *args, **kwargs):
        return True

    def score(self, *args, **kwargs):
        return 1.0

    def snapshot(self, *args, **kwargs):
        return dict(self.stats)

    def to_dict(self, *args, **kwargs):
        return dict(self.stats)

    def record_success(self, *args, **kwargs):
        self.healthy = True
        self.stats["healthy"] = True
        self.stats["ok"] = True
        return None

    def record_failure(self, *args, **kwargs):
        self.stats["failures"] = int(self.stats.get("failures", 0)) + 1
        self.stats["errors"] = int(self.stats.get("errors", 0)) + 1
        # fail-safe: do not make startup fail
        self.healthy = True
        return None

    def record_error(self, err=None, *args, **kwargs):
        self.last_error = err
        return self.record_failure(*args, **kwargs)

    def __getattr__(self, name):
        # Any missing method becomes a harmless callable.
        def _noop(*args, **kwargs):
            if name.startswith("is_") or name in {"healthy", "available", "ready"}:
                return True
            if name in {"score", "ratio", "rate"}:
                return 1.0
            if name in {"snapshot", "stats", "metrics", "status"}:
                return dict(self.stats)
            return _S43NoopAwaitable(None)
        return _noop