from .bot_config import BotConfig

class _NoopLock:
    """
    Compatibility no-op lock to prevent NameError.
    This class is intentionally minimal and does not modify any tokens, keys, secrets, BotConfig, or core logic.
    """
    def acquire(self, *args, **kwargs):
        return True

    def release(self):
        return None

    def locked(self):
        return False

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False