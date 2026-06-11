from .__dzh_ban_integrity_base import _DzhBanIntegrityBase
from .trading_bot import TradingBot
from .wallet_runtime import WalletRuntime

class DzhBanIntegrity(_DzhBanIntegrityBase):
    async def update_wallet_metrics(self, bot: "TradingBot", wallet: "WalletRuntime") -> None:
        now = float(time.time())
        try:
            setattr(wallet, "last_metrics_update_ts", now)
        except Exception:
            pass
        def _num(x: Any) -> float:
            return float(_safe_float(x, default=0.0, translate_digits=True, allow_percent=False, finite=True, na_values=False, strip=True) or 0.0)
        cash_irt = 0.0
        try:
            cash_irt = _num(getattr(wallet, "cash_irt", 0.0))
        except Exception:
            cash_irt = 0.0
        try:
            avail_irt = _num(getattr(wallet, "cash_free_irt", 0.0))
            cash_av_irt = avail_irt if avail_irt > 0.0 else cash_irt
        except Exception:
            cash_av_irt = cash_irt
        holdings: Dict[str, float] = {}
        try:
            holdings = dict(getattr(wallet, "assets_total_snapshot", {}) or {})
        except Exception:
            holdings = {}
        if not holdings:
            try:
                holdings = dict(getattr(wallet, "assets_snapshot", {}) or {})
            except Exception:
                holdings = {}
        try:
            _wr = globals().get("WalletRuntime", None)
            last_known = getattr(_wr, "_LAST_KNOWN_VALID_PRICES", None) if _wr is not None else None
            if not isinstance(last_known, dict):
                if _wr is not None:
                    setattr(_wr, "_LAST_KNOWN_VALID_PRICES", {})
                    last_known = getattr(_wr, "_LAST_KNOWN_VALID_PRICES")
                else:
                    last_known = {}
        except Exception:
            last_known = {}
        symbols: List[str] = []
        for asset, amt in (holdings or {}).items():
            a = str(asset or "").upper().strip()
            if not a or a in {"IRT", "TMN"}:
                continue
            if _num(amt) <= 0.0:
                continue
            symbols.append(_canon_symbol(f"{a}IRT"))
        depth_map: Dict[str, Any] = {}
        if symbols:
            try:
                depth_map = await asyncio.wait_for(
                    bot.feed.fetch_depths(symbols, use_disk_cache_on_timeout=True),
                    timeout=float(_env_float("WALLET_DEPTHS_TIMEOUT_SEC", 3.0) or 3.0),
                )
            except Exception:
                depth_map = {}
        async def _fetch_depth_one(sym: str) -> Any:
            try:
                return await asyncio.wait_for(
                    bot.feed.fetch_depth(sym, use_disk_cache_on_timeout=True),
                    timeout=float(_env_float("WALLET_DEPTH_TIMEOUT_SEC", 1.8) or 1.8),
                )
            except Exception:
                return None
        def _snapshot_mid(sym: str) -> float:
            try:
                snap = getattr(bot, "_market_snapshot", None)
                if isinstance(snap, dict):
                    r = snap.get(_canon_symbol(sym)) or {}
                    if isinstance(r, dict):
                        for k in ("mid", "last", "close", "price"):
                            v = _num(r.get(k, 0.0))
                            if v > 0.0:
                                return v
                if isinstance(snap, list):
                    for r in snap:
                        if not isinstance(r, dict):
                            continue
                        if _canon_symbol(r.get("symbol", "")) != _canon_symbol(sym):
                            continue
                        for k in ("mid", "last", "close", "price"):
                            v = _num(r.get(k, 0.0))
                            if v > 0.0:
                                return v
            except Exception:
                pass
            return 0.0
        async def _resolve_bid(sym: str) -> float:
            s = _canon_symbol(sym)
            ob = None
            try:
                ob = (depth_map or {}).get(s)
            except Exception:
                ob = None
            try:
                if ob is not None:
                    bid = _num(getattr(ob, "bid", 0.0))
                    if bid > 0.0:
                        last_known[s] = bid
                        return bid
                    mid = _num(getattr(ob, "mid", 0.0))
                    if mid > 0.0:
                        last_known[s] = mid
                        return mid
            except Exception:
                pass
            try:
                spot = getattr(bot.feed, "_spot_cache", None)
                if isinstance(spot, dict):
                    ent = spot.get(s)
                    if ent and isinstance(ent, (tuple, list)) and len(ent) >= 2:
                        px = _num(ent[1])
                        if px > 0.0:
                            last_known[s] = px
                            return px
            except Exception:
                pass
            px = _snapshot_mid(s)
            if px > 0.0:
                last_known[s] = px
                return px
            try:
                dc = getattr(bot.feed, "_disk_cache", None)
                if isinstance(dc, dict):
                    ent = dc.get(s)
                    if ent and isinstance(ent, (tuple, list)) and len(ent) >= 2:
                        px2 = _num(ent[1])
                        if px2 > 0.0:
                            last_known[s] = px2
                            return px2
            except Exception:
                pass
            ob2 = None
            try:
                ob2 = await _fetch_depth_one(s)
            except Exception:
                ob2 = None
            try:
                if ob2 is not None:
                    bid2 = _num(getattr(ob2, "bid", 0.0))
                    if bid2 > 0.0:
                        last_known[s] = bid2
                        return bid2
                    mid2 = _num(getattr(ob2, "mid", 0.0))
                    if mid2 > 0.0:
                        last_known[s] = mid2
                        return mid2
            except Exception:
                pass
            try:
                px_last = _num(last_known.get(s, 0.0))
                if px_last > 0.0:
                    return px_last
            except Exception:
                pass
            return 0.0
        assets_value_irt = 0.0
        has_nonfiat = False
        for asset, amt in (holdings or {}).items():
            a = str(asset or "").upper().strip()
            q = _num(amt)
            if q <= 0.0:
                continue
            if a in {"IRT", "TMN"}:
                continue
            has_nonfiat = True
            sym = _canon_symbol(f"{a}IRT")
            bid = await _resolve_bid(sym)
            if bid > 0.0:
                assets_value_irt += q * bid
        prev_assets = 0.0
        prev_eq = 0.0
        try:
            prev_assets = _num(getattr(wallet, "assets_value_irt", 0.0))
            prev_eq = _num(getattr(wallet, "equity_irt", 0.0))
        except Exception:
            pass
        if has_nonfiat and assets_value_irt <= 0.0:
            if prev_assets > 0.0:
                assets_value_irt = prev_assets
            else:
                return
        eq = float(cash_av_irt + assets_value_irt)
        try:
            wallet.assets_value_irt = float(assets_value_irt)
        except Exception:
            pass
        try:
            wallet.equity_irt = float(eq if eq > 0.0 else (prev_eq if prev_eq > 0.0 else eq))
        except Exception:
            pass
    async def maybe_ai_rescue(self, bot: "TradingBot", w: "WalletRuntime", sym: str, book: Any) -> None:
        try:
            pos = (getattr(w, "positions", {}) or {}).get(sym)
            if not pos:
                return
            qty = float(getattr(pos, "qty", 0.0) or 0.0)
            if qty <= 0.0:
                return
            bid = float(getattr(book, "bid", 0.0) or 0.0)
            if bid <= 0.0:
                bid = float(getattr(book, "mid", 0.0) or 0.0)
            if bid <= 0.0:
                return
            notional = qty * bid
            await w.exec.place_limit(sym, "sell", qty, bid, float(notional))
        except Exception:
            return