from .health_metric import HealthMetric
from .__noop_lock import _NoopLock

class SymbolHealthMonitor:
    def __init__(self, symbol: str, config: Dict[str, Any]):
        self.symbol = symbol
        self.config = config
        self.metrics = {
            "latency": HealthMetric("latency_ms"),
            "spread": HealthMetric("spread_bps"),
            "volume": HealthMetric("volume_irt"),
            "price_change": HealthMetric("price_change_bps"),
            "orderbook_depth": HealthMetric("orderbook_depth")
        }
        self.anomaly_counters = defaultdict(int)
        self.last_anomaly_time = 0.0
        self.health_score = 100.0
        self.status = "HEALTHY"
        self._lock = _NoopLock()
        self.price_history = __import__("collections").deque(maxlen=100)
        self._flash_crash_threshold = config.get("flash_crash_threshold", -0.05)
    def update(self, market_data: Dict[str, Any]):
        with self._lock:
            ts = time.time()
            if "latency_ms" in market_data:
                self.metrics["latency"].add(market_data["latency_ms"], ts)
            if "spread_bps" in market_data:
                self.metrics["spread"].add(market_data["spread_bps"], ts)
            if "volume_irt" in market_data:
                self.metrics["volume"].add(market_data["volume_irt"], ts)
            if "mid_price" in market_data:
                current_price = market_data["mid_price"]
                if self.price_history:
                    prev_price = self.price_history[-1]
                    if prev_price > 0:
                        change = (current_price - prev_price) / prev_price
                        self.metrics["price_change"].add(change * 10000, ts)
                        if change < self._flash_crash_threshold:
                            self._record_anomaly("FLASH_CRASH", {
                                "change_pct": change * 100,
                                "threshold": self._flash_crash_threshold * 100
                            })
                self.price_history.append(current_price)
            self._calculate_health_score()
    def _record_anomaly(self, anomaly_type: str, details: Dict[str, Any]):
        self.anomaly_counters[anomaly_type] += 1
        self.last_anomaly_time = time.time()
        logging.warning(
            f"Symbol health anomaly: {self.symbol} | "
            f"Type: {anomaly_type} | Details: {details}"
        )
    def _calculate_health_score(self):
        scores = []
        latency_stats = self.metrics["latency"].get_stats(60)
        if latency_stats:
            target = 100.0
            current = latency_stats.get("current", target)
            score = max(0, 100 - (current / target * 100))
            scores.append(min(100, score * 1.5))
        spread_stats = self.metrics["spread"].get_stats(60)
        if spread_stats:
            target = 50.0
            current = spread_stats.get("current", target)
            score = max(0, 100 - (current / target * 100))
            scores.append(min(100, score))
        volume_stats = self.metrics["volume"].get_stats(300)
        if volume_stats and volume_stats.get("std", 0) > 0:
            cv = volume_stats["std"] / volume_stats["mean"]
            score = max(0, 100 - (cv * 100))
            scores.append(min(100, score))
        anomaly_penalty = 0
        for anomaly_type, count in self.anomaly_counters.items():
            if time.time() - self.last_anomaly_time < 300:
                anomaly_penalty += min(30, count * 10)
        if scores:
            base_score = statistics.mean(scores)
            self.health_score = max(0, base_score - anomaly_penalty)
        else:
            self.health_score = 100 - anomaly_penalty
        if self.health_score >= 80:
            self.status = "HEALTHY"
        elif self.health_score >= 50:
            self.status = "DEGRADED"
        else:
            self.status = "UNHEALTHY"
    def should_trade(self) -> Tuple[bool, str]:
        with self._lock:
            if self.status == "UNHEALTHY":
                return False, f"Symbol {self.symbol} is UNHEALTHY (score: {self.health_score:.1f})"
            if self.anomaly_counters.get("FLASH_CRASH", 0) > 0:
                if time.time() - self.last_anomaly_time < 60:
                    return False, "Flash crash detected recently"
            latency_stats = self.metrics["latency"].get_stats(30)
            if latency_stats and latency_stats.get("current", 0) > 500:
                return False, f"High latency: {latency_stats['current']:.0f}ms"
            return True, self.status
    def get_health_report(self) -> Dict[str, Any]:
        with self._lock:
            report = {
                "symbol": self.symbol,
                "health_score": self.health_score,
                "status": self.status,
                "anomalies": dict(self.anomaly_counters),
                "last_anomaly": self.last_anomaly_time,
                "metrics": {}
            }
            for name, metric in self.metrics.items():
                report["metrics"][name] = metric.get_stats(300)
            return report