class _S43NoopAwaitable:
    """
    Small permissive object usable both as a normal return value and awaitable.
    """
    def __init__(self, value=None):
        self.value = value

    def __await__(self):
        if False:
            yield None
        return self.value

    def __bool__(self):
        return True

    def __float__(self):
        try:
            return float(self.value)
        except Exception:
            return 0.0

    def __int__(self):
        try:
            return int(self.value)
        except Exception:
            return 0

    def __repr__(self):
        return repr(self.value)