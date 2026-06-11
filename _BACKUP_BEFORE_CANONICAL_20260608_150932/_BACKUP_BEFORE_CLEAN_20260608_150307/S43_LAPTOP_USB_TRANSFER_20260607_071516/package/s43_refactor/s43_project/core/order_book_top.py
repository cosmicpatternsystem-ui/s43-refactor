class OrderBookTop:
    bid: float
    ask: float
    mid: float
    spread_bps: float
    bids: List[dict] = field(default_factory=list)
    asks: List[dict] = field(default_factory=list)
    last_trade_price: Optional[float] = None