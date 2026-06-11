from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SafetyDecision:
    allowed: bool
    reason: str = ""
    code: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def allow(cls, reason: str = "ok", **details):
        return cls(True, reason=reason, code="OK", details=details)

    @classmethod
    def deny(cls, code: str, reason: str, **details):
        return cls(False, reason=reason, code=code, details=details)


@dataclass
class MarketSnapshot:
    symbol: str
    bid: Optional[float] = None
    ask: Optional[float] = None
    mid: Optional[float] = None
    spread_abs: Optional[float] = None
    spread_bps: Optional[float] = None
    best_bid_size: Optional[float] = None
    best_ask_size: Optional[float] = None
    last_update_ts: Optional[float] = None
    source: str = "unknown"


@dataclass
class BalanceSnapshot:
    asset: str
    free: float = 0.0
    locked: float = 0.0
    total: float = 0.0
    last_update_ts: Optional[float] = None
    source: str = "unknown"


@dataclass
class SafetyConfig:
    max_market_staleness_sec: float = 3.0
    max_spread_bps: float = 35.0
    min_top_book_size: float = 0.0
    max_balance_staleness_sec: float = 10.0
    max_balance_drift_ratio: float = 0.05
    halt_on_balance_mismatch: bool = True
    halt_on_stale_market: bool = True
    halt_on_spread_breach: bool = False
    halt_on_liquidity_breach: bool = False


class CircuitBreaker:
    def __init__(self):
        self._halted = False
        self._halt_reason = ""
        self._halt_code = ""
        self._halt_ts = None

    def halt(self, code: str, reason: str):
        self._halted = True
        self._halt_code = code
        self._halt_reason = reason
        self._halt_ts = time.time()

    def reset(self):
        self._halted = False
        self._halt_code = ""
        self._halt_reason = ""
        self._halt_ts = None

    @property
    def halted(self) -> bool:
        return self._halted

    def snapshot(self) -> Dict[str, Any]:
        return {
            "halted": self._halted,
            "code": self._halt_code,
            "reason": self._halt_reason,
            "ts": self._halt_ts,
        }


class SafetyCoordinator:
    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or SafetyConfig()
        self.circuit_breaker = CircuitBreaker()

    def check_circuit_breaker(self) -> SafetyDecision:
        if self.circuit_breaker.halted:
            snap = self.circuit_breaker.snapshot()
            return SafetyDecision.deny(
                code=snap.get("code", "HALTED"),
                reason=snap.get("reason", "circuit breaker active"),
                **snap
            )
        return SafetyDecision.allow("circuit breaker clear")

    def check_market_freshness(self, snapshot: MarketSnapshot, now_ts: Optional[float] = None) -> SafetyDecision:
        now_ts = now_ts or time.time()

        if snapshot.last_update_ts is None:
            return SafetyDecision.deny(
                code="MARKET_TS_MISSING",
                reason="market snapshot timestamp missing",
                symbol=snapshot.symbol,
                source=snapshot.source,
            )

        age = now_ts - snapshot.last_update_ts
        if age > self.config.max_market_staleness_sec:
            if self.config.halt_on_stale_market:
                self.circuit_breaker.halt(
                    "STALE_MARKET",
                    f"market data stale for {snapshot.symbol}: age={age:.3f}s"
                )
            return SafetyDecision.deny(
                code="STALE_MARKET",
                reason=f"market data too old: {age:.3f}s",
                symbol=snapshot.symbol,
                age=age,
                max_age=self.config.max_market_staleness_sec,
            )

        return SafetyDecision.allow("market fresh", symbol=snapshot.symbol, age=age)

    def check_spread(self, snapshot: MarketSnapshot) -> SafetyDecision:
        spread_bps = snapshot.spread_bps

        if spread_bps is None:
            if (
                snapshot.bid is not None
                and snapshot.ask is not None
                and snapshot.bid > 0
                and snapshot.ask >= snapshot.bid
            ):
                mid = (snapshot.bid + snapshot.ask) / 2.0
                if mid > 0:
                    spread_bps = ((snapshot.ask - snapshot.bid) / mid) * 10000.0

        if spread_bps is None:
            return SafetyDecision.deny(
                code="SPREAD_UNKNOWN",
                reason="unable to determine spread",
                symbol=snapshot.symbol,
            )

        if spread_bps > self.config.max_spread_bps:
            if self.config.halt_on_spread_breach:
                self.circuit_breaker.halt(
                    "SPREAD_BREACH",
                    f"spread too wide for {snapshot.symbol}: {spread_bps:.2f}bps"
                )
            return SafetyDecision.deny(
                code="SPREAD_BREACH",
                reason=f"spread too wide: {spread_bps:.2f}bps",
                symbol=snapshot.symbol,
                spread_bps=spread_bps,
                max_spread_bps=self.config.max_spread_bps,
            )

        return SafetyDecision.allow(
            "spread within bounds",
            symbol=snapshot.symbol,
            spread_bps=spread_bps,
        )

    def check_liquidity(self, snapshot: MarketSnapshot) -> SafetyDecision:
        bid_size = snapshot.best_bid_size
        ask_size = snapshot.best_ask_size
        min_size = self.config.min_top_book_size

        if min_size <= 0:
            return SafetyDecision.allow("liquidity check disabled", symbol=snapshot.symbol)

        if bid_size is None or ask_size is None:
            return SafetyDecision.deny(
                code="LIQUIDITY_UNKNOWN",
                reason="top-of-book liquidity missing",
                symbol=snapshot.symbol,
                bid_size=bid_size,
                ask_size=ask_size,
            )

        if bid_size < min_size or ask_size < min_size:
            if self.config.halt_on_liquidity_breach:
                self.circuit_breaker.halt(
                    "LIQUIDITY_BREACH",
                    f"top-book liquidity too low for {snapshot.symbol}: bid={bid_size}, ask={ask_size}"
                )
            return SafetyDecision.deny(
                code="LIQUIDITY_BREACH",
                reason="insufficient top-of-book liquidity",
                symbol=snapshot.symbol,
                bid_size=bid_size,
                ask_size=ask_size,
                min_size=min_size,
            )

        return SafetyDecision.allow(
            "liquidity within bounds",
            symbol=snapshot.symbol,
            bid_size=bid_size,
            ask_size=ask_size,
        )

    def check_balance_freshness(self, balance: BalanceSnapshot, now_ts: Optional[float] = None) -> SafetyDecision:
        now_ts = now_ts or time.time()

        if balance.last_update_ts is None:
            return SafetyDecision.deny(
                code="BALANCE_TS_MISSING",
                reason="balance timestamp missing",
                asset=balance.asset,
                source=balance.source,
            )

        age = now_ts - balance.last_update_ts
        if age > self.config.max_balance_staleness_sec:
            return SafetyDecision.deny(
                code="STALE_BALANCE",
                reason=f"balance data too old: {age:.3f}s",
                asset=balance.asset,
                age=age,
                max_age=self.config.max_balance_staleness_sec,
            )

        return SafetyDecision.allow("balance fresh", asset=balance.asset, age=age)

    def check_balance_consistency(
        self,
        expected_total: float,
        actual_total: float,
        asset: str = "unknown",
    ) -> SafetyDecision:
        if expected_total <= 0 and actual_total <= 0:
            return SafetyDecision.allow(
                "empty balance state consistent",
                asset=asset,
                expected_total=expected_total,
                actual_total=actual_total,
            )

        base = max(abs(expected_total), 1e-9)
        drift = abs(actual_total - expected_total)
        drift_ratio = drift / base

        if drift_ratio > self.config.max_balance_drift_ratio:
            if self.config.halt_on_balance_mismatch:
                self.circuit_breaker.halt(
                    "BALANCE_MISMATCH",
                    f"balance mismatch for {asset}: expected={expected_total}, actual={actual_total}"
                )
            return SafetyDecision.deny(
                code="BALANCE_MISMATCH",
                reason="balance drift exceeds threshold",
                asset=asset,
                expected_total=expected_total,
                actual_total=actual_total,
                drift=drift,
                drift_ratio=drift_ratio,
                max_drift_ratio=self.config.max_balance_drift_ratio,
            )

        return SafetyDecision.allow(
            "balance consistent",
            asset=asset,
            expected_total=expected_total,
            actual_total=actual_total,
            drift_ratio=drift_ratio,
        )

    def pre_trade_check(
        self,
        market: MarketSnapshot,
        balance: Optional[BalanceSnapshot] = None,
        expected_balance_total: Optional[float] = None,
    ) -> SafetyDecision:
        decision = self.check_circuit_breaker()
        if not decision.allowed:
            return decision

        decision = self.check_market_freshness(market)
        if not decision.allowed:
            return decision

        decision = self.check_spread(market)
        if not decision.allowed:
            return decision

        decision = self.check_liquidity(market)
        if not decision.allowed:
            return decision

        if balance is not None:
            decision = self.check_balance_freshness(balance)
            if not decision.allowed:
                return decision

        if balance is not None and expected_balance_total is not None:
            decision = self.check_balance_consistency(
                expected_total=expected_balance_total,
                actual_total=balance.total,
                asset=balance.asset,
            )
            if not decision.allowed:
                return decision

        return SafetyDecision.allow(
            "pre-trade checks passed",
            market_symbol=market.symbol,
            balance_asset=(balance.asset if balance else None),
        )
