"""Local audit receipt builder for CP003-A.

This module does not write files or emit data implicitly.
"""

from cp003_scaffold.contracts import AuditReceipt


class AuditReceiptEngine:
    """Pure helper for constructing local audit receipt objects."""

    def __init__(self, component: str = "cp003_a_scaffold") -> None:
        self._component = component

    def build_receipt(self, status: str, **details: object) -> AuditReceipt:
        """Build an in-memory receipt with no side effects."""
        return AuditReceipt(
            component=self._component,
            status=status,
            details=dict(details),
        )