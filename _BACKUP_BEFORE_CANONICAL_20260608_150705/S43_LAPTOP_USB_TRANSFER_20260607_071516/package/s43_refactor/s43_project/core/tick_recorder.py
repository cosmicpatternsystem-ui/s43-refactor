from .logger import Logger

class TickRecorder:
    def __init__(self, db_path: str, timeout_sec: float = 30.0, logger: Optional[logging.Logger] = None):
        self.db_path = str(db_path or "raz_ticks.sqlite")
        self.timeout_sec = float(timeout_sec or 30.0)
        self._logger = logger or logging.getLogger("TickRecorder")
        self._max_q = int(_env_int("RECORDER_QUEUE_MAX", 20000))
        self._q: "asyncio.Queue[Tuple[str, tuple]]" = asyncio.Queue(maxsize=self._max_q)
        self.dropped_ticks = 0
        self._last_drop_log = 0.0
        self.disabled = False
        self._proc: Optional[asyncio.subprocess.Process] = None
        self._writer_task: Optional[asyncio.Task] = None
        self._starter_task: Optional[asyncio.Task] = None
        self._closing = False
    def _start_if_needed(self) -> None:
        if self.disabled or self._closing:
            return
        t = self._writer_task
        if t is not None and not t.done():
            return
        if self._starter_task is not None and not self._starter_task.done():
            return
        try:
            self._starter_task = asyncio.create_task(self._ensure_writer(), name="tickrec_start")
        except RuntimeError:
            return
    async def _ensure_writer(self) -> None:
        if self.disabled or self._closing:
            return
        try:
            if self._proc is not None and self._proc.returncode is None:
                if self._writer_task is None or self._writer_task.done():
                    self._writer_task = asyncio.create_task(self._writer_loop(), name="tickrec_writer")
                return
        except Exception:
            self._proc = None
        _ensure_dir(self.db_path)
        script = _this_script_path()
        try:
            self._proc = await asyncio.create_subprocess_exec(
                sys.executable,
                "-u",
                script,
                "recorder-child",
                "--db",
                self.db_path,
                "--recorder-timeout-sec",
                str(self.timeout_sec),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except Exception as e:
            self._proc = None
            self.disabled = True
            self._logger.exception("event=TICKREC_START_FAIL db=%s err=%s", self.db_path, str(e)[:200])
            return
        self._writer_task = asyncio.create_task(self._writer_loop(), name="tickrec_writer")
    async def _writer_loop(self) -> None:
        backoff = 0.25
        for _omega_guard in range(150000):
            try:
                if self._proc is None or self._proc.returncode is not None or self._proc.stdin is None:
                    await self._ensure_writer()
                    await asyncio.sleep(backoff)
                    backoff = min(5.0, backoff * 2.0)
                    continue
                kind, row = await self._q.get()
                try:
                    payload = json.dumps({"k": kind, "r": row}, separators=(",", ":")) + "\n"
                    self._proc.stdin.write(payload.encode("utf-8", "strict"))
                    await asyncio.wait_for(self._proc.stdin.drain(), timeout=2.5)
                finally:
                    self._q.task_done()
                backoff = 0.25
            except asyncio.CancelledError:
                raise
            except Exception:
                try:
                    self._logger.exception("event=TICKREC_WRITE_FAIL db=%s", self.db_path)
                except Exception:
                    pass
                try:
                    if self._proc and self._proc.stdin:
                        self._proc.stdin.close()
                except Exception:
                    pass
                try:
                    if self._proc:
                        self._proc.kill()
                except Exception:
                    pass
                self._proc = None
                await asyncio.sleep(backoff)
                backoff = min(5.0, backoff * 2.0)
    def _put_nowait(self, kind: str, row: tuple) -> None:
        if self.disabled or self._closing:
            return
        self._start_if_needed()
        try:
            self._q.put_nowait((kind, row))
        except asyncio.QueueFull:
            self.dropped_ticks += 1
            now = time.time()
            if (now - self._last_drop_log) > 5.0:
                self._last_drop_log = now
                try:
                    self._logger.warning("event=TICKREC_DROP qmax=%s dropped=%s", str(self._max_q), str(self.dropped_ticks))
                except Exception:
                    pass
    async def record_tick(
        self,
        ts: float,
        wallet: str,
        symbol: str,
        bid: float,
        ask: float,
        mid: float,
        spr_bps: float,
        score: float,
        equity: Optional[float] = None,
        quote_free: Optional[float] = None,
        asset_free: Optional[float] = None,
    ) -> None:
        row = (
            float(ts or 0.0),
            str(wallet or ""),
            str(symbol or ""),
            float(bid or 0.0),
            float(ask or 0.0),
            float(mid or 0.0),
            float(spr_bps or 0.0),
            float(score or 0.0),
            float(equity) if equity is not None else None,
            float(quote_free) if quote_free is not None else None,
            float(asset_free) if asset_free is not None else None,
        )
        self._put_nowait("tick", row)
    def record_order(
        self,
        ts: float,
        wallet: str,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        notional: float,
        ok: bool = True,
        order_id: Optional[str] = None,
        raw: Optional[dict] = None,
    ) -> None:
        row = (
            float(ts or 0.0),
            str(wallet or ""),
            str(symbol or ""),
            str(side or ""),
            float(qty or 0.0),
            float(price or 0.0),
            float(notional or 0.0),
            int(1 if ok else 0),
            str(order_id or ""),
            json.dumps(raw or {}, ensure_ascii=False)[:2000],
        )
        self._put_nowait("order", row)
    async def aclose(self) -> None:
        self._closing = True
        try:
            if self._writer_task is not None:
                self._writer_task.cancel()
        except Exception:
            pass
        try:
            if self._proc and self._proc.stdin:
                self._proc.stdin.close()
        except Exception:
            pass
        try:
            if self._proc:
                await asyncio.wait_for(self._proc.wait(), timeout=2.0)
        except Exception:
            try:
                if self._proc:
                    self._proc.kill()
            except Exception:
                pass
        self._proc = None