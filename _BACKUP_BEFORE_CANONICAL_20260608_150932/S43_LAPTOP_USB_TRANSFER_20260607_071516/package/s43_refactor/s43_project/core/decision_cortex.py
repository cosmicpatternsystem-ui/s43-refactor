from .order_book_top import OrderBookTop
from .logger import Logger
from .__cortex_null_logger import _CortexNullLogger
from .signal import Signal
from .bot_config import BotConfig

class DecisionCortex:
    def __init__(self, cfg: BotConfig, logger: logging.Logger):
        self.cfg = cfg
        self._log = logger or _CortexNullLogger()
        self._parisa_mod = None
        self._legacy = None
        self._sym_state: Dict[str, dict] = {}
        self._load_err: Optional[str] = None
    def _ensure_parisa(self) -> None:
        if self._legacy is not None or self._load_err is not None:
            return
        try:
            mod = _load_parisa_module()
            class _ShimBot:
                _news_headlines: List[str] = []
                cognitive_core: Any = None
                _dollar_defense: bool = False
            shim = _ShimBot()
            legacy_cls = getattr(mod, "LegacyIntelligenceManager", None)
            if legacy_cls is None:
                raise RuntimeError("LegacyIntelligenceManager not found in embedded Parisa module")
            self._legacy = legacy_cls(shim)
            self._parisa_mod = mod
            self._log.info("event=CORTEX_PARISA_READY status=OK")
        except Exception as e:
            self._load_err = str(e)
            self._log.warning("event=CORTEX_PARISA_DISABLED err=%s", e)
    def parisa_delta(self, symbol: str, book: OrderBookTop, depth_data: Any = None) -> Tuple[float, List[Tuple[str, str]]]:
        if not bool(self.cfg.collective_intelligence):
            return 0.0, []
        self._ensure_parisa()
        if self._legacy is None:
            return 0.0, []
        sym = _canon_symbol(symbol)
        st = self._sym_state.setdefault(sym, {})
        try:
            delta, contrib = self._legacy.evaluate(sym, st, float(book.bid), float(book.ask), float(book.mid), depth_data)
            try:
                delta = float(delta)
            except Exception:
                delta = 0.0
            if not isinstance(contrib, list):
                contrib = []
            return delta, contrib
        except Exception:
            return 0.0, []
    def entry_multiplier(self, symbol: str, raz_signal: Signal, book: OrderBookTop, depth_data: Any = None) -> Tuple[float, Dict[str, Any]]:
        meta: Dict[str, Any] = {"enabled": bool(self.cfg.collective_intelligence)}
        if not bool(self.cfg.collective_intelligence):
            return 1.0, meta
        if str(raz_signal.action).upper() != "BUY":
            return 1.0, meta
        if float(getattr(raz_signal, "confidence", 0.0) or 0.0) < float(self.cfg.collective_min_raz_conf):
            meta["raz_conf"] = float(getattr(raz_signal, "confidence", 0.0) or 0.0)
            return 1.0, meta
        delta, contrib = self.parisa_delta(symbol, book, depth_data=depth_data)
        meta["parisa_delta"] = float(delta)
        meta["parisa_vote_thr"] = float(self.cfg.parisa_vote_thr)
        veto_thr = float(getattr(self.cfg, "parisa_veto_thr", -0.35) or -0.35)
        meta["parisa_veto_thr"] = float(veto_thr)
        if float(delta) <= float(veto_thr):
            meta["veto"] = True
            try:
                meta["parisa_contrib"] = (contrib or [])[:4]
            except Exception:
                meta["parisa_contrib"] = []
            return 1.0, meta
        if float(delta) >= float(self.cfg.parisa_vote_thr):
            meta["boost"] = True
            meta["multiplier"] = float(self.cfg.collective_multiplier)
            try:
                meta["parisa_contrib"] = (contrib or [])[:4]
            except Exception:
                meta["parisa_contrib"] = []
            return float(self.cfg.collective_multiplier), meta
        meta["boost"] = False
        try:
            meta["parisa_contrib"] = (contrib or [])[:4]
        except Exception:
            meta["parisa_contrib"] = []
        return 1.0, meta