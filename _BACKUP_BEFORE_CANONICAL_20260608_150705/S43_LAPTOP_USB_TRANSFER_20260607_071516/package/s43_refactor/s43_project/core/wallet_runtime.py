from .execution_engine import ExecutionEngine
from .alpha_model import AlphaModel
from .exchange_client import ExchangeClient
from .decision_cortex import DecisionCortex
from .bot_config import BotConfig
from .position import Position

class WalletRuntime:
    _LAST_KNOWN_VALID_PRICES: ClassVar[Dict[str, float]] = {}
    _LAST_KNOWN_PRICES_PATH: ClassVar[str] = ""
    _LAST_KNOWN_PRICES_LOADED: ClassVar[bool] = False
    _LAST_KNOWN_PRICES_DIRTY: ClassVar[bool] = False
    _LAST_KNOWN_PRICES_LAST_FLUSH: ClassVar[float] = 0.0
    @classmethod
    def configure_last_known_prices(cls, path: str) -> None:
        try:
            cls._LAST_KNOWN_PRICES_PATH = str(path or "").strip()
        except Exception:
            cls._LAST_KNOWN_PRICES_PATH = ""
    @classmethod
    def load_last_known_prices(cls) -> None:
        if cls._LAST_KNOWN_PRICES_LOADED:
            return
        cls._LAST_KNOWN_PRICES_LOADED = True
        p = str(getattr(cls, "_LAST_KNOWN_PRICES_PATH", "") or "").strip()
        if not p:
            return
        try:
            if not os.path.exists(p):
                return
            with open(p, "r", encoding="utf-8") as f:
                obj = json.load(f)
            if not isinstance(obj, dict):
                return
            out: Dict[str, float] = {}
            for k, v in obj.items():
                try:
                    kk = _canon_symbol(str(k or "").strip())
                    vv = float(v)
                    if kk and math.isfinite(vv) and vv > 0.0:
                        out[kk] = vv
                except Exception:
                    continue
            if out:
                cls._LAST_KNOWN_VALID_PRICES.update(out)
        except Exception:
            return
    @classmethod
    def _flush_last_known_prices(cls, force: bool = False) -> None:
        p = str(getattr(cls, "_LAST_KNOWN_PRICES_PATH", "") or "").strip()
        if not p:
            return
        try:
            now = float(time.time())
        except Exception:
            now = 0.0
        try:
            if (not force) and (not bool(getattr(cls, "_LAST_KNOWN_PRICES_DIRTY", False))):
                return
            min_iv = float(_env_float("LKP_FLUSH_MIN_INTERVAL_SEC", 10.0) or 10.0)
            last = float(getattr(cls, "_LAST_KNOWN_PRICES_LAST_FLUSH", 0.0) or 0.0)
            if (not force) and now and (now - last) < max(1.0, min_iv):
                return
        except Exception:
            pass
        try:
            d = os.path.dirname(os.path.abspath(p))
            if d:
                os.makedirs(d, exist_ok=True)
        except Exception:
            pass
        try:
            data = dict(getattr(cls, "_LAST_KNOWN_VALID_PRICES", {}) or {})
            tmp = p + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            os.replace(tmp, p)
            cls._LAST_KNOWN_PRICES_DIRTY = False
            cls._LAST_KNOWN_PRICES_LAST_FLUSH = float(time.time())
        except Exception:
            return
    @classmethod
    def set_last_known_price(cls, symbol: str, price: float) -> None:
        try:
            sym = _canon_symbol(symbol)
        except Exception:
            sym = str(symbol or "").strip()
        try:
            px = float(price)
        except Exception:
            return
        if not sym or (not math.isfinite(px)) or px <= 0.0:
            return
        try:
            cls._LAST_KNOWN_VALID_PRICES[sym] = px
            cls._LAST_KNOWN_PRICES_DIRTY = True
        except Exception:
            return
        try:
            cls._flush_last_known_prices(force=False)
        except Exception:
            pass
    slot: int
    name: str
    cfg: BotConfig
    ex: ExchangeClient
    exec: ExecutionEngine
    alpha: AlphaModel
    cortex: DecisionCortex
    positions: Dict[str, Position] = field(default_factory=dict)
    last_balance_ts: float = 0.0
    cash_irt: float = 0.0
    cash_total_irt: float = 0.0
    last_event: str = ""
    focus_symbols: List[str] = field(default_factory=list)
    equity_irt: float = 0.0
    engaged_irt: float = 0.0
    steps_open: int = 0
    open_orders_exch: int = 0
    last_orders_ts: float = 0.0
    last_orders_sync_ok: bool = True
    last_orders_sync_err: str = ""
    last_orders_sync_ts: float = 0.0
    last_reject_reason: str = ""
    last_reject_meta: Dict[str, Any] = field(default_factory=dict)
    trace: deque = field(default_factory=_obs_trace_deque)
    last_reconcile_ts: float = 0.0
    pnl_realized_irt: float = 0.0
    pnl_unrealized_irt: float = 0.0
    pnl_total_irt: float = 0.0
    dyn_max_notional_frac: float = 0.0
    sanity_halt: bool = False
    sanity_reason: str = ""
    sanity_until_ts: float = 0.0
    last_engine_status: str = ""
    last_engine_reason: str = ""
    last_engine_ts: float = 0.0
    ttl_canceled: int = 0
    ttl_cancel_failed: int = 0
    ttl_last_cancel_ts: float = 0.0
    ttl_last_cancel_err: str = ""
    phoenix_state: str = "FLAT"
    phoenix_conf: float = 0.0
    phoenix_rsi: Optional[float] = None
    phoenix_shadow: Optional[float] = None
    phoenix_composite: float = 0.0
    last_balance_ok: bool = False
    assets_snapshot: Dict[str, float] = field(default_factory=dict)
    assets_total_snapshot: Dict[str, float] = field(default_factory=dict)
    last_assets_ts: float = 0.0
    token_expiry_ts: float = 0.0
    wallet_disabled: bool = False
    wallet_disable_reason: str = ""