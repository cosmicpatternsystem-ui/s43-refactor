from .logger import Logger
from .decision_cortex import DecisionCortex

class _CortexNullLogger:
    def __init__(self) -> None:
        self._log = logging.getLogger("DecisionCortex")
    def info(self, *a, **k):
        try:
            self._log.info(*a, **k)
        except Exception:
            pass
    def warning(self, *a, **k):
        try:
            self._log.warning(*a, **k)
        except Exception:
            pass
    def error(self, *a, **k):
        try:
            self._log.error(*a, **k)
        except Exception:
            pass
    def exception(self, *a, **k):
        try:
            self._log.exception(*a, **k)
        except Exception:
            pass