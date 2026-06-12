import time
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GovernanceEvent:
    gate: str
    status: str
    reason: str
    timestamp: float

class CapitalKillSwitch:
    """
    Minimal, auditable governance guard for Phase 11.

    Behavior:
    - tracks peak equity
    - computes drawdown from peak
    - triggers kill when drawdown >= threshold
    - may also be manually killed
    """

    def __init__(self, max_drawdown_pct=20.0, enabled=True):
        self.max_drawdown_pct = float(max_drawdown_pct)
        self.enabled = bool(enabled)
        self._killed = False
        self._peak_equity = None
        self._last_reason = None
        self._events = []

    @property
    def killed(self):
        return self._killed

    @property
    def last_reason(self):
        return self._last_reason

    @property
    def peak_equity(self):
        return self._peak_equity

    def _record(self, gate, status, reason):
        event = GovernanceEvent(
            gate=gate,
            status=status,
            reason=str(reason),
            timestamp=time.time()
        )
        self._events.append(event)
        logger.warning("[GOVERNANCE] gate=%s status=%s reason=%s", gate, status, reason)

    def kill(self, reason="manual kill"):
        self._killed = True
        self._last_reason = str(reason)
        self._record("GATE_G11_1", "TRIGGERED", reason)

    def update(self, equity):
        if not self.enabled or self._killed:
            return self._killed

        if equity is None:
            return self._killed

        equity = float(equity)

        if self._peak_equity is None or equity > self._peak_equity:
            self._peak_equity = equity
            return self._killed

        if self._peak_equity <= 0:
            return self._killed

        drawdown_pct = ((self._peak_equity - equity) / self._peak_equity) * 100.0

        if drawdown_pct >= self.max_drawdown_pct:
            self.kill(
                reason=f"equity drawdown {drawdown_pct:.2f}% >= threshold {self.max_drawdown_pct:.2f}%"
            )

        return self._killed

    def snapshot(self):
        return {
            "enabled": self.enabled,
            "killed": self._killed,
            "max_drawdown_pct": self.max_drawdown_pct,
            "peak_equity": self._peak_equity,
            "last_reason": self._last_reason,
            "event_count": len(self._events),
        }


def governance_wallet_cycle_guard(reason, logger_obj=None):
    msg = f"[GATE_G11_2] wallet cycle guard reason={reason}"
    if logger_obj is not None:
        try:
            logger_obj.warning(msg)
        except Exception:
            logger.warning(msg)
    else:
        logger.warning(msg)
    return {
        "gate": "GATE_G11_2",
        "status": "TRIGGERED",
        "reason": str(reason),
        "timestamp": time.time(),
    }