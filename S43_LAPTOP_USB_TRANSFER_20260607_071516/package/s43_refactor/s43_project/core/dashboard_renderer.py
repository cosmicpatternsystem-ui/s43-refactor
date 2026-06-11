from .risk_metrics import RiskMetrics

class DashboardRenderer:
    def __init__(self, refresh_interval: float = 1.0):
        self.refresh_interval = float(refresh_interval or 1.0)
        self.metrics_history: Deque[RiskMetrics] = __import__("collections").deque(maxlen=1000)
        self._stop_event = asyncio.Event()
        self._render_task: Optional[asyncio.Task] = None
        self._last_render = 0.0
        self.colors = {
            "green": "\033[92m",
            "yellow": "\033[93m",
            "red": "\033[91m",
            "blue": "\033[94m",
            "reset": "\033[0m",
            "bold": "\033[1m",
        }
    def start(self):
        if self._render_task is None or self._render_task.done():
            self._stop_event.clear()
            try:
                self._render_task = asyncio.create_task(self._render_loop(), name="DashboardRenderer")
            except RuntimeError:
                self._render_task = None
    def stop(self):
        try:
            self._stop_event.set()
        except Exception:
            pass
        try:
            if self._render_task is not None and not self._render_task.done():
                self._render_task.cancel()
        except Exception:
            pass
        self._render_task = None
    async def _render_loop(self):
        for _omega_guard in range(150000):
            try:
                await asyncio.sleep(self.refresh_interval)
                self.render_dashboard()
            except asyncio.CancelledError:
                raise
            except Exception:
                logging.exception("event=DASH_RENDER_ERR")
    def update_metrics(self, metrics: RiskMetrics):
        try:
            self.metrics_history.append(metrics)
        except Exception:
            pass
    def render_dashboard(self):
        try:
            if time.time() - self._last_render < self.refresh_interval:
                return
            self._last_render = time.time()
            if not self.metrics_history:
                return
            current = self.metrics_history[-1]
            print("\033[2J\033[H")
            print(f"{self.colors['bold']}=== Risk Dashboard ==={self.colors['reset']}")
            print(f"Total Equity: {current.total_equity:,.0f} IRT")
            print(f"Risk Score: {current.risk_score:.1f}/100")
            print(f"Max Drawdown: {current.max_drawdown:.2%}")
            risk_color = "green" if current.risk_score < 30 else "yellow" if current.risk_score < 70 else "red"
            print(f"Status: {self.colors[risk_color]}{current.status}{self.colors['reset']}")
            if current.warnings:
                print(f"\n{self.colors['red']}Warnings:{self.colors['reset']}")
                for warning in current.warnings:
                    print(f"  - {warning}")
            if current.recommendations:
                print(f"\n{self.colors['blue']}Recommendations:{self.colors['reset']}")
                for rec in current.recommendations:
                    print(f"  - {rec}")
        except Exception:
            logging.exception("event=DASH_RENDER_BODY_ERR")