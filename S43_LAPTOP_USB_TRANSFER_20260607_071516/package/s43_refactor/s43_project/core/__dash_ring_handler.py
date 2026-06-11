class _DashRingHandler(logging.Handler):
    def __init__(self, maxlen: int = 400):
        super().__init__(level=logging.INFO)
        from collections import deque as _s43_deque