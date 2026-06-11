from .order_book_top import OrderBookTop
from .logger import Logger
from .bot_config import BotConfig

class OrderBookAnalyzer:
    def __init__(self, cfg: BotConfig, logger: logging.Logger):
        self.cfg = cfg
        self._log = logger
        self.granularity = float(getattr(cfg, "oba_cluster_granularity", 50.0) or 50.0)
    @staticmethod
    def _cluster_orders(orders: List[dict], granularity: float) -> Dict[float, float]:
        clusters: Dict[float, float] = {}
        g = float(granularity) if granularity > 0 else 1.0
        for o in orders or []:
            try:
                if isinstance(o, dict):
                    price = float(o.get("price") or o.get("p") or 0.0)
                    amount = float(o.get("amount") or o.get("quantity") or o.get("q") or 0.0)
                elif isinstance(o, (list, tuple)) and len(o) >= 2:
                    price = float(o[0])
                    amount = float(o[1])
                else:
                    continue
                if price <= 0 or amount <= 0:
                    continue
                p = round(price / g) * g
                clusters[p] = clusters.get(p, 0.0) + amount
            except Exception:
                continue
        return clusters
    def _detect_walls(self, bid_clusters: Dict[float, float], ask_clusters: Dict[float, float]) -> Dict[str, List[Dict[str, Any]]]:
        thr_irt = float(getattr(self.cfg, "oba_wall_threshold_irt", 50_000_000.0) or 50_000_000.0)
        walls = {"bid": [], "ask": []}
        for side, clusters in (("bid", bid_clusters), ("ask", ask_clusters)):
            for price, amount in clusters.items():
                v = float(price) * float(amount)
                if v >= thr_irt:
                    walls[side].append({"price": price, "amount": amount, "volume_irt": v, "strength": v / max(1e-9, thr_irt)})
        return walls
    def analyze(self, book: OrderBookTop) -> Dict[str, Any]:
        if not book or not getattr(book, "bids", None) or not getattr(book, "asks", None):
            return {}
        bid_clusters = self._cluster_orders(book.bids, self.granularity)
        ask_clusters = self._cluster_orders(book.asks, self.granularity)
        bid_vol = float(sum(bid_clusters.values()))
        ask_vol = float(sum(ask_clusters.values()))
        total = bid_vol + ask_vol + 1e-9
        imbalance = (bid_vol - ask_vol) / total
        score = float(clamp(imbalance * 2.0, -1.0, 1.0))
        interpretation = "BULLISH" if score > 0.2 else ("BEARISH" if score < -0.2 else "NEUTRAL")
        return {
            "order_book_ratio": bid_vol / (ask_vol + 1e-9),
            "imbalance": imbalance,
            "score": score,
            "walls": self._detect_walls(bid_clusters, ask_clusters),
            "bid_volume": bid_vol,
            "ask_volume": ask_vol,
            "interpretation": interpretation,
        }