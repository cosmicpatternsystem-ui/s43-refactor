class SoftSymbolBlacklist:
    """
    Fail-safe soft blacklist fallback.

    Default behavior:
    - nothing is blacklisted
    - record methods are accepted but mostly no-op
    - snapshot/status methods return lightweight state
    """
    def __init__(self, cfg=None, logger=None, *args, **kwargs):
        self.cfg = cfg
        self.logger = logger
        self._blocked = {}
        self._reasons = {}

    def is_blocked(self, symbol=None, *args, **kwargs):
        try:
            key = str(symbol).strip().upper() if symbol is not None else ""
        except Exception:
            key = ""
        return bool(key and key in self._blocked)

    def blocked(self, symbol=None, *args, **kwargs):
        return self.is_blocked(symbol, *args, **kwargs)

    def allows(self, symbol=None, *args, **kwargs):
        return not self.is_blocked(symbol, *args, **kwargs)

    def allowed(self, symbol=None, *args, **kwargs):
        return not self.is_blocked(symbol, *args, **kwargs)

    def add(self, symbol=None, reason=None, *args, **kwargs):
        try:
            key = str(symbol).strip().upper() if symbol is not None else ""
        except Exception:
            key = ""
        if key:
            self._blocked[key] = True
            if reason is not None:
                self._reasons[key] = str(reason)
        return None

    def remove(self, symbol=None, *args, **kwargs):
        try:
            key = str(symbol).strip().upper() if symbol is not None else ""
        except Exception:
            key = ""
        if key:
            self._blocked.pop(key, None)
            self._reasons.pop(key, None)
        return None

    def discard(self, symbol=None, *args, **kwargs):
        return self.remove(symbol, *args, **kwargs)

    def clear(self, *args, **kwargs):
        self._blocked.clear()
        self._reasons.clear()
        return None

    def mark(self, symbol=None, reason=None, *args, **kwargs):
        return self.add(symbol, reason=reason, *args, **kwargs)

    def unmark(self, symbol=None, *args, **kwargs):
        return self.remove(symbol, *args, **kwargs)

    def note_failure(self, symbol=None, reason=None, *args, **kwargs):
        # fail-safe: do not auto-block unless caller explicitly uses add/mark
        return None

    def record_failure(self, symbol=None, reason=None, *args, **kwargs):
        return self.note_failure(symbol, reason=reason, *args, **kwargs)

    def note_success(self, symbol=None, *args, **kwargs):
        return None

    def record_success(self, symbol=None, *args, **kwargs):
        return None

    def get_reason(self, symbol=None, *args, **kwargs):
        try:
            key = str(symbol).strip().upper() if symbol is not None else ""
        except Exception:
            key = ""
        return self._reasons.get(key)

    def snapshot(self, *args, **kwargs):
        return {
            "count": len(self._blocked),
            "symbols": sorted(self._blocked.keys()),
            "reasons": dict(self._reasons),
        }

    def to_dict(self, *args, **kwargs):
        return self.snapshot()

    def __contains__(self, symbol):
        return self.is_blocked(symbol)

    def __len__(self):
        return len(self._blocked)

    def __bool__(self):
        return True

    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            lname = str(name)
            if lname.startswith("is_") or lname in {"blocked", "contains"}:
                return False
            if lname in {"allows", "allowed"}:
                return True
            if lname in {"snapshot", "status", "stats", "to_dict"}:
                return self.snapshot()
            return None
        return _noop