from .orch22_market_state import Orch22MarketState
from .logger import Logger
from .__orch22_stale_clock import _Orch22StaleClock
from .exchange_client import ExchangeClient
from .__orch22_async_component import _Orch22AsyncComponent
from .bot_config import BotConfig

class Orch22MarketRadar(_Orch22AsyncComponent):
    def __init__(self, *, public: "ExchangeClient", cfg: "BotConfig", log: logging.Logger) -> None:
        self.public = public
        self.cfg = cfg
        self._log = log
        self.state = Orch22MarketState()
        self._fresh = _Orch22StaleClock()
        self._stop = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._history: Dict[str, Deque[float]] = {}
        self._history_max = 120
        self._phoenix: Dict[str, float] = {}
        self.refresh_sec = float(_env_float("ORCH22_MARKET_REFRESH_SEC", max(1.0, getattr(cfg, "top8_refresh_sec", 12.0))) or 8.0)
    def _task_name(self) -> str:
        return "orch22_market_radar"
    def _score_row(self, sym: str, row: Dict[str, Any]) -> float:
        vol = _safe_float(
            row.get("volume_24h_irt") or row.get("quoteVolume") or row.get("quote_volume")
            or row.get("vol_irt") or row.get("value") or row.get("volume") or 0.0
        )
        high = _safe_float(row.get("high") or row.get("h") or row.get("high_24h") or row.get("high24h") or 0.0)
        low = _safe_float(row.get("low") or row.get("l") or row.get("low_24h") or row.get("low24h") or 0.0)
        vola = 0.0
        if low and high and high >= low and low > 0:
            vola = max(0.0, (high - low) / low)
        return (vol * 0.6) + (vol * vola * 0.4)
    def _update_history(self, by_symbol: Dict[str, Dict[str, Any]]) -> None:
        for sym, row in (by_symbol or {}).items():
            s = _canon_symbol(sym)
            if not s:
                continue
            close = _safe_float(row.get("close") or row.get("last") or row.get("last_price") or row.get("price") or 0.0)
            if close <= 0:
                continue
            dq = self._history.get(s)
            if dq is None:
                dq = __import__("collections").deque(maxlen=self._history_max)
                self._history[s] = dq
            dq.append(float(close))
    def rsi(self, sym: str, period: int = 14) -> Optional[float]:
        s = _canon_symbol(sym)
        dq = self._history.get(s)
        if not dq or len(dq) < (period + 1):
            return None
        gains = 0.0
        losses = 0.0
        prev = dq[-(period + 1)]
        for p in list(dq)[-period:]:
            delta = float(p) - float(prev)
            if delta >= 0:
                gains += delta
            else:
                losses += -delta
            prev = p
        if losses <= 0:
            return 100.0
        rs = (gains / period) / (losses / period)
        return 100.0 - (100.0 / (1.0 + rs))
    def phoenix_top(self, n: int = 8) -> List[Tuple[str, float]]:
        items = sorted((self._phoenix or {}).items(), key=lambda kv: float(kv[1]), reverse=True)
        return items[: max(1, int(n))]
    def _compute_focus_and_top8(self, by_symbol: Dict[str, Dict[str, Any]]) -> Tuple[List[str], Dict[str, float], Dict[str, float], List[str]]:
        quote = str(getattr(self.cfg, "quote", "IRT") or "IRT").upper()
        universe: List[Tuple[str, float]] = []
        phoenix_scores: Dict[str, float] = {}
        for sym, row in (by_symbol or {}).items():
            s = _canon_symbol(sym)
            if not s or not s.endswith(quote):
                continue
            sc = self._score_row(s, row or {})
            if sc > 0:
                universe.append((s, sc))
                chg_1h = _safe_float(row.get("change_1h") or row.get("changePercent1h") or row.get("pct_1h") or 0.0)
                chg_24h = _safe_float(row.get("change") or row.get("priceChangePercent") or row.get("change_24h") or 0.0)
                phoenix_scores[s] = abs(chg_1h) if abs(chg_1h) > 0 else abs(chg_24h)
        universe.sort(key=lambda x: float(x[1]), reverse=True)
        top8 = [s for s, _sc in universe[:8]]
        anchor = _canon_symbol(f"PAXG{quote}")
        focus_map: Dict[str, float] = {anchor: 0.20} if anchor else {}
        focus_scores: Dict[str, float] = {anchor: float(universe[0][1]) if universe and anchor else 0.0} if anchor else {}
        weights = [0.18, 0.15, 0.12, 0.10, 0.08, 0.07, 0.05, 0.05]
        for s, sc in universe:
            if len(focus_map) >= 9:
                break
            if s and s not in focus_map:
                focus_map[s] = float(weights[len(focus_map) - 1]) if len(focus_map) - 1 < len(weights) else 0.05
                focus_scores[s] = float(sc)
        focus = list(focus_map.keys())
        self._phoenix = phoenix_scores
        return focus, focus_map, focus_scores, top8
    async def _run(self) -> None:
        backoff = 0.5
        for _omega_guard in range(150000):
            t0 = time.time()
            try:
                stats_map = await asyncio.wait_for(self.public.get_market_snapshot(), timeout=float(os.getenv("RADAR_SNAPSHOT_TIMEOUT_SEC", "12") or 12.0))
                by_symbol = stats_map if isinstance(stats_map, dict) else {}
                if not isinstance(by_symbol, dict):
                    by_symbol = {}
                by_symbol = { _canon_symbol(k): (v if isinstance(v, dict) else {"symbol": _canon_symbol(k), "value": v})
                              for k, v in (by_symbol or {}).items() if _canon_symbol(k) }
                self._update_history(by_symbol)
                focus, focus_map, focus_scores, top8 = self._compute_focus_and_top8(by_symbol)
                self.state = Orch22MarketState(
                    server_time=float(time.time()),
                    fetched_ts=float(t0),
                    by_symbol=by_symbol,
                    top8=top8,
                    focus=focus,
                    focus_weights=focus_map,
                    focus_scores=focus_scores,
                )
                self._fresh.touch()
                backoff = 0.5
            except asyncio.CancelledError:
                raise
            except Exception as e:
                _orch22_log(self._log, logging.WARNING, "RADAR_FAIL", err=str(e)[:200], age=round(self.age(), 3))
                backoff = min(10.0, backoff * 1.6)
            dt = time.time() - t0
            sleep_for = max(0.10, float(self.refresh_sec) - dt)
            if backoff > 0.5:
                sleep_for = max(sleep_for, backoff)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=sleep_for)
            except asyncio.TimeoutError:
                pass