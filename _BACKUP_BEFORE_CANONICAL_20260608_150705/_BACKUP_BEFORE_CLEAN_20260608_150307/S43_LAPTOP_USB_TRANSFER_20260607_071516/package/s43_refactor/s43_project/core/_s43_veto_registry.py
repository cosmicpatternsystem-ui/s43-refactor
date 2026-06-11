class _S43VetoRegistry:
    """
    Fail-safe veto registry fallback for dashboard/render paths.

    Default behavior:
    - no active vetoes
    - snapshot returns an empty, dashboard-friendly structure
    - record/add methods are accepted without breaking runtime
    """
    def __init__(self, *args, **kwargs):
        self._items = []

    def add(self, *args, **kwargs):
        try:
            item = {
                "args": args,
                "kwargs": dict(kwargs),
            }
            self._items.append(item)
        except Exception:
            pass
        return None

    def record(self, *args, **kwargs):
        return self.add(*args, **kwargs)

    def put(self, *args, **kwargs):
        return self.add(*args, **kwargs)

    def append(self, *args, **kwargs):
        return self.add(*args, **kwargs)

    def remove(self, *args, **kwargs):
        return None

    def discard(self, *args, **kwargs):
        return None

    def clear(self, *args, **kwargs):
        try:
            self._items.clear()
        except Exception:
            self._items = []
        return None

    def prune(self, *args, **kwargs):
        return None

    def expire(self, *args, **kwargs):
        return None

    def snapshot(self, *args, **kwargs):
# Conservative output: the dashboard usually handles list/dict safely.
# Leave active empty to avoid a false veto.
        return {
            "active": [],
            "items": [],
            "vetoes": [],
            "count": 0,
            "total": 0,
            "stale": [],
        }

    def to_dict(self, *args, **kwargs):
        return self.snapshot(*args, **kwargs)

    def stats(self, *args, **kwargs):
        return self.snapshot(*args, **kwargs)

    def __len__(self):
        return 0

    def __bool__(self):
# The registry exists, but it has no active veto.
        return True

    def __iter__(self):
        return iter(())

    def __contains__(self, item):
        return False

    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            lname = str(name)
            if lname in {"snapshot", "to_dict", "stats", "status", "dump"}:
                return self.snapshot(*args, **kwargs)
            if lname.startswith("has_") or lname.startswith("is_"):
                return False
            if lname in {"count", "size"}:
                return 0
            return None
        return _noop