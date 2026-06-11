from .risk_metrics import RiskMetrics

class RiskMetricsCalculator:
    def __init__(self):
        self.trade_history: List[Dict[str, Any]] = []
        self.equity_history: Deque[float] = __import__("collections").deque(maxlen=10000)
        self.max_equity = 0.0
    def calculate_metrics(
        self,
        portfolio_data: Dict[str, Any],
        trade_data: List[Dict[str, Any]],
        system_data: Dict[str, Any]
    ) -> RiskMetrics:
        metrics = RiskMetrics()
        metrics.total_equity = portfolio_data.get("total_equity", 0.0)
        metrics.total_exposure = portfolio_data.get("total_exposure", 0.0)
        metrics.cash_balance = portfolio_data.get("cash_balance", 0.0)
        metrics.open_positions = portfolio_data.get("open_positions", 0)
        metrics.largest_position = portfolio_data.get("largest_position", 0.0)
        self.equity_history.append(metrics.total_equity)
        self.max_equity = max(self.max_equity, metrics.total_equity)
        metrics.daily_pnl = portfolio_data.get("daily_pnl", 0.0)
        metrics.daily_return = portfolio_data.get("daily_return", 0.0)
        metrics.unrealized_pnl = portfolio_data.get("unrealized_pnl", 0.0)
        metrics.realized_pnl = portfolio_data.get("realized_pnl", 0.0)
        metrics.var_95 = self._calculate_var_95()
        metrics.expected_shortfall = self._calculate_expected_shortfall()
        metrics.sharpe_ratio = self._calculate_sharpe_ratio()
        metrics.max_drawdown = self._calculate_max_drawdown()
        metrics.current_drawdown = self._calculate_current_drawdown()
        if trade_data:
            self.trade_history.extend(trade_data)
        metrics.total_trades = len(self.trade_history)
        metrics.win_rate = self._calculate_win_rate()
        metrics.avg_win, metrics.avg_loss = self._calculate_avg_win_loss()
        metrics.profit_factor = self._calculate_profit_factor()
        if metrics.total_equity > 0:
            metrics.concentration_ratio = metrics.largest_position / metrics.total_equity
        metrics.system_health = system_data.get("system_health", 0.0)
        metrics.latency_ms = system_data.get("latency_ms", 0.0)
        metrics.error_rate = system_data.get("error_rate", 0.0)
        return metrics
    def _calculate_var_95(self) -> float:
        if len(self.equity_history) < 20:
            return 0.0
        returns = []
        for i in range(1, len(self.equity_history)):
            if self.equity_history[i-1] > 0:
                ret = (self.equity_history[i] - self.equity_history[i-1]) / self.equity_history[i-1]
                returns.append(ret)
        if not returns:
            return 0.0
        sorted_returns = sorted(returns)
        index = int(0.05 * len(sorted_returns))
        var = sorted_returns[max(0, index)]
        return abs(var) * 100
    def _calculate_expected_shortfall(self) -> float:
        if len(self.equity_history) < 20:
            return 0.0
        returns = []
        for i in range(1, len(self.equity_history)):
            if self.equity_history[i-1] > 0:
                ret = (self.equity_history[i] - self.equity_history[i-1]) / self.equity_history[i-1]
                returns.append(ret)
        if not returns:
            return 0.0
        sorted_returns = sorted(returns)
        cutoff_index = int(0.05 * len(sorted_returns))
        tail_returns = sorted_returns[:max(1, cutoff_index)]
        if tail_returns:
            es = statistics.mean(tail_returns)
            return abs(es) * 100
        return 0.0
    def _calculate_sharpe_ratio(self) -> float:
        if len(self.equity_history) < 20:
            return 0.0
        returns = []
        for i in range(1, len(self.equity_history)):
            if self.equity_history[i-1] > 0:
                ret = (self.equity_history[i] - self.equity_history[i-1]) / self.equity_history[i-1]
                returns.append(ret)
        if len(returns) < 2:
            return 0.0
        mean_return = statistics.mean(returns)
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0
        if std_return == 0:
            return 0.0
        sharpe = (mean_return / std_return) * math.sqrt(252)
        return sharpe
    def _calculate_max_drawdown(self) -> float:
        if len(self.equity_history) < 2:
            return 0.0
        peak = self.equity_history[0]
        max_dd = 0.0
        for equity in self.equity_history:
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak if peak > 0 else 0
            max_dd = max(max_dd, dd)
        return max_dd * 100
    def _calculate_current_drawdown(self) -> float:
        if len(self.equity_history) < 1 or self.max_equity == 0:
            return 0.0
        current_equity = self.equity_history[-1] if self.equity_history else 0
        drawdown = (self.max_equity - current_equity) / self.max_equity
        return drawdown * 100
    def _calculate_win_rate(self) -> float:
        if not self.trade_history:
            return 0.0
        wins = sum(1 for trade in self.trade_history if trade.get("pnl", 0) > 0)
        return wins / len(self.trade_history)
    def _calculate_avg_win_loss(self) -> Tuple[float, float]:
        if not self.trade_history:
            return 0.0, 0.0
        wins = [t.get("pnl_pct", 0) for t in self.trade_history if t.get("pnl", 0) > 0]
        losses = [t.get("pnl_pct", 0) for t in self.trade_history if t.get("pnl", 0) < 0]
        avg_win = statistics.mean(wins) if wins else 0.0
        avg_loss = abs(statistics.mean(losses)) if losses else 0.0
        return avg_win * 100, avg_loss * 100
    def _calculate_profit_factor(self) -> float:
        if not self.trade_history:
            return 0.0
        gross_profits = sum(t.get("pnl", 0) for t in self.trade_history if t.get("pnl", 0) > 0)
        gross_losses = abs(sum(t.get("pnl", 0) for t in self.trade_history if t.get("pnl", 0) < 0))
        if gross_losses == 0:
            return float("inf") if gross_profits > 0 else 0.0
        return gross_profits / gross_losses