from .priority import Priority

class PrioritySemaphore:
    """
    Fail-safe async semaphore compatible with basic PrioritySemaphore usage.
    Priority values are accepted but ignored in this recovery implementation.
    """
    def __init__(self, value=1, *args, **kwargs):
        try:
            value = int(value)
        except Exception:
            value = 1
        if value < 1:
            value = 1
        self._sem = __import__("asyncio").Semaphore(value)

    async def acquire(self, priority=0, *args, **kwargs):
        await self._sem.acquire()
        return True

    def release(self):
        return self._sem.release()

    def locked(self):
        try:
            return self._sem.locked()
        except Exception:
            return False

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.release()
        return False