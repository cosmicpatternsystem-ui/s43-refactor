class HealthMetric:
    name: str
    values: Deque[float] = field(default_factory=lambda: __import__("collections").deque(maxlen=1000))
    timestamps: Deque[float] = field(default_factory=lambda: __import__("collections").deque(maxlen=1000))
    def add(self, value: float, timestamp: Optional[float] = None):
        ts = timestamp or time.time()
        self.values.append(value)
        self.timestamps.append(ts)
    def get_stats(self, window_seconds: float = 300) -> Dict[str, float]:
        if not self.values:
            return {}
        cutoff = time.time() - window_seconds
        recent = [
            v for v, t in zip(self.values, self.timestamps)
            if t >= cutoff
        ]
        if not recent:
            return {}
        return {
            "mean": float(np.mean(recent)),
            "std": float(np.std(recent)),
            "min": float(np.min(recent)),
            "max": float(np.max(recent)),
            "p95": float(np.percentile(recent, 95)),
            "current": float(recent[-1]),
            "count": len(recent)
        }
    def detect_anomaly(
        self,
        current_value: float,
        sigma_threshold: float = 3.0,
        window_seconds: float = 300
    ) -> Tuple[bool, Dict[str, float]]:
        stats = self.get_stats(window_seconds)
        if not stats or stats["std"] == 0:
            return False, stats
        z_score = abs(current_value - stats["mean"]) / stats["std"]
        is_anomaly = z_score > sigma_threshold
        anomaly_info = {
            **stats,
            "z_score": z_score,
            "threshold": sigma_threshold,
            "is_anomaly": is_anomaly
        }
        return is_anomaly, anomaly_info