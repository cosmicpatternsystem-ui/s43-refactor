class Orch22WalletState:
    name: str
    equity_irt: float = 0.0
    cash_irt: float = 0.0
    assets_irt: float = 0.0
    open_orders: int = 0
    last_ok: bool = False
    last_ts: float = 0.0
    last_err: str = ""
    mode: str = "Hold"
    reason: str = ""
    canceled_ok: int = 0
    canceled_fail: int = 0