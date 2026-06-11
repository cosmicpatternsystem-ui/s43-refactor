class OrderJournal:
    """
    Fail-safe stub for missing OrderJournal.
    Keeps in-memory records and tolerates unknown method calls.
    """
    def __init__(self, cfg=None, logger=None, *args, **kwargs):
        self.cfg = cfg
        self.logger = logger
        self.records = []
        self.orders = self.records

    def add(self, item=None, *args, **kwargs):
        if item is None:
            item = {}
        self.records.append(item)
        return item

    def append(self, item=None, *args, **kwargs):
        return self.add(item, *args, **kwargs)

    def record(self, item=None, *args, **kwargs):
        return self.add(item, *args, **kwargs)

    def extend(self, items):
        try:
            self.records.extend(list(items))
        except Exception:
            pass
        return None

    def clear(self):
        self.records.clear()

    def save(self, *args, **kwargs):
        return None

    def flush(self, *args, **kwargs):
        return None

    def close(self, *args, **kwargs):
        return None

    def __len__(self):
        return len(self.records)

    def __iter__(self):
        return iter(self.records)

    def __bool__(self):
        return True

    def __getattr__(self, name):
        # tolerate missing methods like log/write/mark/update/etc.
        def _noop(*args, **kwargs):
            return None
        return _noop