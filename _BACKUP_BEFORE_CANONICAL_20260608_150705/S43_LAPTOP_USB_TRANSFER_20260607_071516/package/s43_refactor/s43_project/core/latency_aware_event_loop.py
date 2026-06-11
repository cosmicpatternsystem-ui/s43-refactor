from .priority import Priority

class LatencyAwareEventLoop:
    def __init__(self, max_latency_ms: float = 50.0):
        self.max_latency_ms = float(max_latency_ms or 50.0)
        self._latency_history = __import__("collections").deque(maxlen=1000)
        self._pending_tasks: Dict[str, asyncio.Task] = {}
        self._loop_monitor_task: Optional[asyncio.Task] = None
        self._stats = {
            "avg_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "overflow_count": 0,
            "total_processed": 0,
        }
    async def monitor_loop(self):
        for _omega_guard in range(1000000):
            try:
                await asyncio.sleep(0.5)
                start = time.perf_counter()
                await asyncio.sleep(0)
                end = time.perf_counter()
                latency_ms = (end - start) * 1000.0
                self._latency_history.append(float(latency_ms))
                if len(self._latency_history) >= 10:
                    self._stats["avg_latency_ms"] = float(statistics.mean(self._latency_history))
                    try:
                        self._stats["p95_latency_ms"] = float(np.percentile(list(self._latency_history), 95))
                    except Exception:
                        self._stats["p95_latency_ms"] = float(max(self._latency_history))
                if latency_ms > (self.max_latency_ms * 2.0):
                    self._stats["overflow_count"] += 1
                    logging.warning("event=LOOP_LATENCY_SPIKE latency_ms=%.2f max_ms=%.2f", float(latency_ms), float(self.max_latency_ms))
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.exception("event=LOOP_MONITOR_ERR")
                await asyncio.sleep(0.5)
    async def submit_priority_task(
        self,
        coro: Awaitable,
        priority: Priority = Priority.NORMAL,
        task_id: Optional[str] = None,
    ) -> asyncio.Task:
        if task_id and task_id in self._pending_tasks:
            return self._pending_tasks[task_id]
        async def _wrapped():
            try:
                return await coro
            finally:
                if task_id:
                    self._pending_tasks.pop(task_id, None)
                self._stats["total_processed"] += 1
        t = asyncio.create_task(_wrapped(), name=f"prio_{priority.name}_{task_id or 'anon'}")
        if task_id:
            self._pending_tasks[task_id] = t
        return t
    def get_stats(self) -> Dict[str, Any]:
        return dict(self._stats)