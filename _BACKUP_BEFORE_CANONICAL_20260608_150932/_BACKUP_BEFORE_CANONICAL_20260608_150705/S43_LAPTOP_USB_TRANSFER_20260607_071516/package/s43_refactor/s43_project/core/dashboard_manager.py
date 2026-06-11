from .trading_bot import TradingBot

class DashboardManager:
    def __init__(
        self,
        bot: "TradingBot",
        *,
        refresh_sec: float = 1.0,
        screen: bool = True,
    ) -> None:
        self.bot = bot
        self.refresh_sec = float(max(0.2, refresh_sec))
        self.screen = bool(screen)
        try:
            env_screen = os.getenv("DASH_SCREEN", "").strip()
        except Exception:
            env_screen = ""
        if env_screen:
            try:
                self.screen = bool(int(env_screen))
            except Exception:
                try:
                    self.screen = bool(env_screen.lower() in ("1","true","yes","on"))
                except Exception:
                    pass
        else:
            try:
                is_termux = bool(os.getenv("TERMUX_VERSION"))
            except Exception:
                is_termux = False
            if not is_termux:
                try:
                    pref = str(os.getenv("PREFIX") or "") + " " + str(os.getenv("HOME") or "")
                    if "com.termux" in pref:
                        is_termux = True
                except Exception:
                    pass
            if is_termux:
                self.screen = False
        self._stop: asyncio.Event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
    def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        try:
            loop = asyncio.get_running_loop()
        except Exception:
            return
        self._stop.clear()
        self._task = loop.create_task(self._run(), name="Dashboard")
    def stop(self) -> None:
        try:
            self._stop.set()
        except Exception:
            pass
        t = self._task
        if t is not None and not t.done():
            try:
                t.cancel()
            except Exception:
                pass
    async def _run(self) -> None:
        await self._run_fallback()
    async def _run_fallback(self) -> None:
        for _omega_guard in range(150000):
            parts = []
            try:
                for wname, w in getattr(self.bot, "wallets", {}).items():
                    cash_irt = float(getattr(w, "cash_irt", 0.0) or 0.0)
                    div = 10.0 if (cash_irt >= 1_000_000.0 and abs(cash_irt) % 10 == 0) else 1.0
                    cash_t = cash_irt / div
                    posn = len(getattr(w, "positions", {}) or {})
                    le = str(getattr(w, "last_event", "") or "").strip()
                    parts.append(f"{wname}: cashT={cash_t:,.0f} pos={posn} ev={le[:28]}")
            except Exception:
                pass
            line = " | ".join(parts) if parts else "..."
            try:
                print("[DASH] " + line, flush=True)
            except Exception:
                pass
            await _sleep_or_stop(self._stop, self.refresh_sec)