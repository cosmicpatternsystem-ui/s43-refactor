class TradingMemory:
    def __init__(self, win_rate_prior: float = 0.52, avg_win: float = 0.012, avg_loss: float = 0.009):
        self.win_rate_prior = float(win_rate_prior)
        self.avg_win = float(avg_win)
        self.avg_loss = float(avg_loss)
        self.n = 0
        self.wins = 0
    def record(self, pnl_pct: float) -> None:
        self.n += 1
        if pnl_pct > 0:
            self.wins += 1
    def kelly_fraction(self) -> float:
        n = max(1, self.n)
        win_rate = (self.wins + self.win_rate_prior * 10.0) / (n + 10.0)
        b = self.avg_win / max(1e-9, self.avg_loss)
        k = win_rate - (1.0 - win_rate) / max(1e-9, b)
        return float(clamp(k, 0.0, 0.20))
    def to_dict(self) -> dict:
        return {"win_rate_prior": self.win_rate_prior, "avg_win": self.avg_win, "avg_loss": self.avg_loss, "n": self.n, "wins": self.wins}
    @staticmethod
    def from_dict(d: dict) -> "TradingMemory":
        m = TradingMemory(
            win_rate_prior=float(d.get("win_rate_prior", 0.52)),
            avg_win=float(d.get("avg_win", 0.012)),
            avg_loss=float(d.get("avg_loss", 0.009)),
        )
        m.n = int(d.get("n", 0))
        m.wins = int(d.get("wins", 0))
        return m