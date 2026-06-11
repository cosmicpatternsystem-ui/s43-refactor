from .health_metric import HealthMetric
from .__noop_lock import _NoopLock
from .symbol_health_monitor import SymbolHealthMonitor

class GlobalHealthMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.symbol_monitors: Dict[str, SymbolHealthMonitor] = {}
        self.system_metrics = HealthMetric("system_health")
        self.circuit_breakers: Dict[str, bool] = {}
        self._lock = _NoopLock()
        self._cb_reset_tasks: Dict[str, asyncio.Task] = {}
        self._last_system_check = 0.0
        self.thresholds = {
            "system_health_min": config.get("system_health_min", 70.0),
            "unhealthy_symbols_max": config.get("unhealthy_symbols_max", 2),
            "degraded_symbols_max": config.get("degraded_symbols_max", 4)
        }
    def get_or_create_symbol_monitor(self, symbol: str) -> SymbolHealthMonitor:
        with self._lock:
            if symbol not in self.symbol_monitors:
                self.symbol_monitors[symbol] = SymbolHealthMonitor(
                    symbol, self.config
                )
            return self.symbol_monitors[symbol]
    def update_symbol_health(self, symbol: str, market_data: Dict[str, Any]):
        monitor = self.get_or_create_symbol_monitor(symbol)
        monitor.update(market_data)
    def check_system_health(self) -> Dict[str, Any]:
        with self._lock:
            now = time.time()
            if now - self._last_system_check < 5.0:
                return self._last_system_report or {}
            self._last_system_check = now
            symbol_reports = {}
            unhealthy_count = 0
            degraded_count = 0
            avg_health_score = 0.0
            for symbol, monitor in self.symbol_monitors.items():
                report = monitor.get_health_report()
                symbol_reports[symbol] = report
                if monitor.status == "UNHEALTHY":
                    unhealthy_count += 1
                elif monitor.status == "DEGRADED":
                    degraded_count += 1
                avg_health_score += monitor.health_score
            if self.symbol_monitors:
                avg_health_score /= len(self.symbol_monitors)
            self.system_metrics.add(avg_health_score, now)
            system_status = "HEALTHY"
            if unhealthy_count > self.thresholds["unhealthy_symbols_max"]:
                system_status = "CRITICAL"
            elif degraded_count > self.thresholds["degraded_symbols_max"]:
                system_status = "DEGRADED"
            elif avg_health_score < self.thresholds["system_health_min"]:
                system_status = "DEGRADED"
            if system_status == "CRITICAL":
                self._activate_circuit_breaker("SYSTEM_HEALTH")
            report = {
                "timestamp": now,
                "system_status": system_status,
                "system_health_score": avg_health_score,
                "unhealthy_symbols": unhealthy_count,
                "degraded_symbols": degraded_count,
                "symbol_reports": symbol_reports,
                "circuit_breakers": dict(self.circuit_breakers)
            }
            self._last_system_report = report
            return report
    def _activate_circuit_breaker(self, breaker_id: str):
        self.circuit_breakers[breaker_id] = True
        try:
            reset_delay = float(self.config.get("circuit_breaker_reset_sec", 60) or 60.0)
        except Exception:
            reset_delay = 60.0
        async def _reset():
            try:
                await asyncio.sleep(reset_delay)
                with self._lock:
                    if self.circuit_breakers.get(breaker_id):
                        self.circuit_breakers[breaker_id] = False
                logging.info("event=CIRCUIT_RESET id=%s delay_s=%.1f", str(breaker_id), float(reset_delay))
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.exception("event=CIRCUIT_RESET_ERR id=%s", str(breaker_id))
        try:
            t = self._cb_reset_tasks.get(breaker_id)
            if t is None or t.done():
                self._cb_reset_tasks[breaker_id] = asyncio.create_task(_reset(), name=f"cb_reset_{breaker_id}")
        except Exception:
            logging.exception("event=CIRCUIT_SCHED_ERR id=%s", str(breaker_id))
        logging.critical("event=CIRCUIT_ACTIVE id=%s", str(breaker_id))
    def is_circuit_breaker_active(self, breaker_id: str) -> bool:
        return self.circuit_breakers.get(breaker_id, False)