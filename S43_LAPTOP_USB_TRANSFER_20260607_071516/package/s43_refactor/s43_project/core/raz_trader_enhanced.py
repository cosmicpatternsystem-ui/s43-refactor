from .latency_aware_event_loop import LatencyAwareEventLoop
from .global_health_monitor import GlobalHealthMonitor
from .risk_metrics import RiskMetrics
from .filtered_signal import FilteredSignal
from .dashboard_renderer import DashboardRenderer
from .hybrid_signal_filter import HybridSignalFilter
from .signal import Signal
from .dynamic_position_sizer import DynamicPositionSizer
from .adaptive_retry_handler import AdaptiveRetryHandler
from .risk_metrics_calculator import RiskMetricsCalculator
from .position import Position
from .resilient_api_client import ResilientAPIClient
from .async_rate_limiter import AsyncRateLimiter

class RazTraderEnhanced:
    def __init__(self, original_config: Dict[str, Any]):
        self.original_config = original_config
        self.latency_loop = LatencyAwareEventLoop(
            max_latency_ms=original_config.get("max_latency_ms", 50.0)
        )
        self.health_monitor = GlobalHealthMonitor(
            config=original_config.get("health_monitor", {})
        )
        self.position_sizer = DynamicPositionSizer(
            config=original_config.get("position_sizing", {})
        )
        self.signal_filter = HybridSignalFilter(
            config=original_config.get("signal_filtering", {})
        )
        self.retry_handler = AdaptiveRetryHandler()
        self.rate_limiter = AsyncRateLimiter(
            requests_per_minute=original_config.get("requests_per_minute", 100),
            burst_size=original_config.get("burst_size", 5)
        )
        self.api_client = ResilientAPIClient(
            base_url=original_config.get("base_url", "https://api.arzplus.net/api/v1"),
            rate_limiter=self.rate_limiter,
            retry_handler=self.retry_handler
        )
        self.metrics_calculator = RiskMetricsCalculator()
        self.dashboard = DashboardRenderer(
            refresh_interval=original_config.get("dashboard_refresh", 1.0)
        )
        self.is_running = False
        self._main_task: Optional[asyncio.Task] = None
    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.latency_loop._loop_monitor_task = asyncio.create_task(
            self.latency_loop.monitor_loop()
        )
        self.dashboard.start()
        self._main_task = asyncio.create_task(
            self._enhanced_trading_loop()
        )
        logging.info("Enhanced RazTrader started with 6-layer improvements")
    async def stop(self):
        self.is_running = False
        if self.latency_loop._loop_monitor_task:
            self.latency_loop._loop_monitor_task.cancel()
        if self._main_task:
            self._main_task.cancel()
        self.dashboard.stop()
        await self.api_client.close()
        logging.info("Enhanced RazTrader stopped")
    async def _enhanced_trading_loop(self):
        for _omega_guard in range(150000):
            try:
                start_time = time.time()
                health_report = self.health_monitor.check_system_health()
                if health_report.get("system_status") == "CRITICAL":
                    logging.critical("System health critical, pausing trading")
                    await asyncio.sleep(5)
                    continue
                symbols = self._get_trading_symbols()
                priority_symbols = self._prioritize_symbols(symbols, health_report)
                for symbol in priority_symbols:
                    await self._process_symbol_enhanced(symbol)
                await self._update_dashboard()
                loop_duration = time.time() - start_time
                target_interval = self.original_config.get("loop_interval_sec", 2.0)
                if loop_duration < target_interval:
                    await asyncio.sleep(target_interval - loop_duration)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Enhanced trading loop error: {e}")
                await asyncio.sleep(1)
    def _get_trading_symbols(self) -> List[str]:
        return self.original_config.get("symbols", ["BTCIRT", "ETHIRT", "USDTIRT"])
    def _prioritize_symbols(
        self,
        symbols: List[str],
        health_report: Dict[str, Any]
    ) -> List[str]:
        prioritized = []
        for symbol in symbols:
            symbol_report = health_report.get("symbol_reports", {}).get(symbol, {})
            health_score = symbol_report.get("health_score", 0)
            if health_score >= 70:
                prioritized.append(symbol)
        prioritized.sort(
            key=lambda s: health_report.get("symbol_reports", {}).get(s, {}).get("health_score", 0),
            reverse=True
        )
        return prioritized
    async def _process_symbol_enhanced(self, symbol: str):
        try:
            market_data = await self._get_market_data(symbol)
            self.health_monitor.update_symbol_health(symbol, market_data)
            can_trade, reason = self.health_monitor.get_or_create_symbol_monitor(
                symbol
            ).should_trade()
            if not can_trade:
                logging.debug(f"Skipping {symbol}: {reason}")
                return
            raw_signal = await self._get_raw_signal(symbol, market_data)
            volatility_metrics = self.position_sizer.update_volatility_metrics(
                symbol,
                market_data.get("prices", []),
                market_data.get("highs", []),
                market_data.get("lows", [])
            )
            filtered_signal = self.signal_filter.filter_signal(
                raw_signal,
                market_data,
                volatility_metrics
            )
            if not filtered_signal.should_execute():
                return
            portfolio_data = await self._get_portfolio_data()
            position_size = self.position_sizer.calculate_position_size(
                symbol=symbol,
                capital=portfolio_data.get("capital", 0),
                volatility_metrics=volatility_metrics,
                signal_strength=filtered_signal.filtered_score,
                current_exposure=portfolio_data.get("exposure", 0),
                market_regime=filtered_signal.market_regime
            )
            filtered_signal.position_size_pct = position_size["position_pct"]
            priority = filtered_signal.get_execution_priority()
            await self.latency_loop.submit_priority_task(
                self._execute_trade(filtered_signal, position_size),
                priority=priority,
                task_id=f"trade_{symbol}_{time.time()}"
            )
        except Exception as e:
            logging.error(f"Error processing symbol {symbol}: {e}")
    async def _get_market_data(self, symbol: str) -> Dict[str, Any]:
        try:
            depth_data = await self.api_client.request(
                "GET",
                f"/market/depth/{symbol}"
            )
            trades_data = await self.api_client.request(
                "GET",
                f"/market/trades/{symbol}"
            )
            prices = [float(t["price"]) for t in trades_data.get("trades", [])[-100:]]
            return {
                "symbol": symbol,
                "bid": float(depth_data.get("bids", [{}])[0].get("price", 0)),
                "ask": float(depth_data.get("asks", [{}])[0].get("price", 0)),
                "mid": (float(depth_data.get("bids", [{}])[0].get("price", 0)) +
                       float(depth_data.get("asks", [{}])[0].get("price", 0))) / 2,
                "volume": sum(float(t.get("amount", 0)) for t in trades_data.get("trades", [])[-100:]),
                "prices": prices,
                "ema_fast": self._calculate_ema(prices, 9) if len(prices) >= 9 else None,
                "ema_medium": self._calculate_ema(prices, 21) if len(prices) >= 21 else None,
                "ema_slow": self._calculate_ema(prices, 50) if len(prices) >= 50 else None,
                "rsi": self._calculate_rsi(prices) if len(prices) >= 14 else None
            }
        except Exception as e:
            logging.error(f"Failed to get market data for {symbol}: {e}")
            return {}
    async def _get_raw_signal(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a deterministic raw signal from the *existing* market_data fields.

        NOTE: This bot previously returned a hard-coded BUY, which would cause perpetual buying.
        We keep this lightweight and architecture-neutral: only EMA/RSI/price that are already computed.
        """
        try:
            prices = market_data.get("prices") or []
        except Exception:
            prices = []
        try:
            px = float(market_data.get("mid") or market_data.get("price") or (prices[-1] if prices else 0.0) or 0.0)
        except Exception:
            px = 0.0
        ema_fast = market_data.get("ema_fast")
        ema_medium = market_data.get("ema_medium")
        ema_slow = market_data.get("ema_slow")
        rsi = market_data.get("rsi")
        # Not enough data -> HOLD (avoid noisy early trades)
        if px <= 0.0 or None in (ema_fast, ema_medium, ema_slow, rsi):
            return {
                "action": "HOLD",
                "symbol": symbol,
                "score": 0.0,
                "confidence": 0.0,
            }
        try:
            ema_fast_f = float(ema_fast)
            ema_medium_f = float(ema_medium)
            ema_slow_f = float(ema_slow)
            rsi_f = float(rsi)
        except Exception:
            return {
                "action": "HOLD",
                "symbol": symbol,
                "score": 0.0,
                "confidence": 0.0,
            }
        # Trend/momentum from EMAs (already computed upstream)
        try:
            mom = (ema_fast_f - ema_slow_f) / max(1e-12, float(px))
        except Exception:
            mom = 0.0
        mom_score = float(math.tanh(float(mom) * 6.0))  # [-1, 1]
        # RSI bias as a mean-reversion brake: overbought reduces BUY, oversold reduces SELL
        rsi_bias = float(clamp((50.0 - float(rsi_f)) / 50.0, -1.0, 1.0))  # + => oversold
        comp = float(clamp(0.70 * mom_score + 0.30 * rsi_bias, -1.0, 1.0))
        # Directional alignment gates (avoid conflicting signals)
        uptrend = (float(px) > ema_fast_f > ema_medium_f > ema_slow_f)
        downtrend = (float(px) < ema_fast_f < ema_medium_f < ema_slow_f)
        action = "HOLD"
        thr = 0.35
        if comp >= thr and (uptrend or float(px) > ema_medium_f):
            action = "BUY"
        elif comp <= -thr and (downtrend or float(px) < ema_medium_f):
            action = "SELL"
        # Confidence: magnitude + alignment bonus; HOLD is capped
        base_conf = float(clamp(abs(comp), 0.0, 1.0))
        if action == "BUY" and uptrend:
            base_conf = float(clamp(base_conf + 0.15, 0.0, 1.0))
        elif action == "SELL" and downtrend:
            base_conf = float(clamp(base_conf + 0.15, 0.0, 1.0))
        if action == "HOLD":
            base_conf = float(min(base_conf, 0.45))
        return {
            "action": action,
            "symbol": symbol,
            "score": float(comp),
            "confidence": float(base_conf),
        }
    async def _get_portfolio_data(self) -> Dict[str, Any]:
        try:
            _wdu = float(getattr(self, "_balance_disabled_until", 0.0) or 0.0)
        except Exception:
            _wdu = 0.0
        if _wdu > time.time():
            try:
                print(f"ISOCHK_COOLDOWN phase=portfolio_data until={int(_wdu)} fail_count={int(getattr(self, '_balance_fail_count', 0) or 0)}", flush=True)
            except Exception:
                pass
            return {
                "capital": 0.0,
                "exposure": 0.0,
                "positions": []
            }
        try:
            balance_data = await self.api_client.request(
                "GET",
                "/wallet/balance/"
            )
            try:
                setattr(self, "_balance_fail_count", 0)
                setattr(self, "_balance_disabled_until", 0.0)
            except Exception:
                pass
            cash = float(balance_data.get("IRT", {}).get("available", 0))
            return {
                "capital": cash,
                "exposure": 0.0,
                "positions": []
            }
        except Exception as e:
            try:
                _fc = int(getattr(self, "_balance_fail_count", 0) or 0) + 1
                setattr(self, "_balance_fail_count", _fc)
                setattr(self, "_balance_disabled_until", time.time() + 120.0)
                print(f"ISOCHK phase=portfolio_data err={type(e).__name__}:{e} fail_count={_fc}", flush=True)
            except Exception:
                pass
            try:
                logging.warning(
                    "ISOCHK_GLOBAL phase=portfolio_data err=%s",
                    f"{type(e).__name__}: {e}",
                )
            except Exception:
                pass
            return {
                "capital": 0.0,
                "exposure": 0.0,
                "positions": []
            }
    async def _execute_trade(
        self,
        signal: FilteredSignal,
        position_size: Dict[str, Any]
    ):
        try:
            order_data = {
                "symbol": signal.symbol,
                "side": signal.action,
                "amount": position_size["position_size"],
                "price": 0,
                "client_order_id": f"enhanced_{int(time.time() * 1000)}"
            }
            result = await self.api_client.request(
                "POST",
                "/market/orders/",
                json=order_data
            )
            logging.info(
                f"Executed {signal.action} order for {signal.symbol}: "
                f"Size={position_size['position_size']:.2f}, "
                f"Confidence={signal.filtered_confidence:.2f}"
            )
        except Exception as e:
            logging.error(f"Failed to execute trade for {signal.symbol}: {e}")
    async def _update_dashboard(self):
        portfolio_data = await self._get_portfolio_data()
        system_stats = self.latency_loop.get_stats()
        metrics = self.metrics_calculator.calculate_metrics(
            portfolio_data=portfolio_data,
            trade_data=[],
            system_data={
                "system_health": self.health_monitor.check_system_health().get("system_health_score", 100),
                "latency_ms": system_stats.get("avg_latency_ms", 0),
                "error_rate": 0.0
            }
        )
        self.dashboard.update_metrics(metrics)
    def _calculate_ema(self, prices: List[float], period: int) -> float:
        if len(prices) < period:
            return prices[-1] if prices else 0
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        return ema
    def _calculate_rsi(self, prices: List[float]) -> float:
        if len(prices) < 15:
            return 50.0
        gains = []
        losses = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        avg_gain = statistics.mean(gains[-14:]) if gains else 0
        avg_loss = statistics.mean(losses[-14:]) if losses else 0
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi