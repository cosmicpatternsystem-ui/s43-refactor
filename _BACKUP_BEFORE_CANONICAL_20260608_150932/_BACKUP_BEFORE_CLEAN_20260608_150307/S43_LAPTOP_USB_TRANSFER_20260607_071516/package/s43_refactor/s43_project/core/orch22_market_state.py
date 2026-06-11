class Orch22MarketState:
    server_time: float = 0.0
    fetched_ts: float = 0.0
    by_symbol: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    top8: List[str] = field(default_factory=list)
    focus: List[str] = field(default_factory=list)
    focus_weights: Dict[str, float] = field(default_factory=dict)
    focus_scores: Dict[str, float] = field(default_factory=dict)