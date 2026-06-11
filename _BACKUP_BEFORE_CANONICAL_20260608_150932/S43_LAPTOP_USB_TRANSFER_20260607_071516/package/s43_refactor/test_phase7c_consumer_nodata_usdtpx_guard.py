import asyncio
import os
import time
import types
import unittest
from unittest.mock import Mock, patch
from unittest import mock

import s43


class TestPhase7CConsumerNoDataUsdtPxGuard(unittest.TestCase):
    def test_consumer_nodata_usdtpx_sets_hold_rejects_and_returns_before_entry_multiplier(
        self,
    ):
        sym = "BTCUSDT"

        old_warmup = os.environ.get("BOT_WARMUP_SEC")
        os.environ["BOT_WARMUP_SEC"] = "1"

        old_boot_ts = getattr(s43, "_BOOT_TS", None)
        had_boot_ts = hasattr(s43, "_BOOT_TS")

        try:
            try:
                setattr(s43, "_BOOT_TS", time.time() - 30.0)
            except Exception:
                pass

            bot = object.__new__(s43.TradingBotOps)
            bot._log = Mock()

            bot.cfg = types.SimpleNamespace(
                phoenix_enabled=True,
                phoenix_gate_mode="soft",
                phoenix_min_conf=0.10,
                phoenix_entry_threshold=0.10,
                sanity_enabled=True,
                advanced_analytics_enabled=False,
                max_open_positions=10,
                data_risk_no_entry=False,
                risk_cooldown_sec=0,
                min_depth_latency_ms=500.0,
                phoenix_allow_spot_ready=False,
            )

            bot.advanced_analytics = None

            sig = types.SimpleNamespace(
                action="ENTRY",
                score=0.80,
                confidence=0.90,
                reason="TEST_BUY",
                meta={},
            )

            w = types.SimpleNamespace(
                name="test_wallet",
                dyn_max_notional_frac=1.0,
                cfg=types.SimpleNamespace(
                    buy_threshold=0.20,
                    sell_threshold=0.20,
                    collective_max_notional_frac=1.0,
                ),
                positions={},
                assets_snapshot={},
                alpha=types.SimpleNamespace(
                    evaluate=Mock(return_value=sig),
                ),
                cortex=types.SimpleNamespace(),
                last_engine_status=None,
                last_engine_reason=None,
                last_engine_ts=None,
                last_event=None,
                sanity_halt=False,
            )

            entry_multiplier_called = False

            def fake_entry_multiplier(*args, **kwargs):
                nonlocal entry_multiplier_called
                entry_multiplier_called = True
                return 1.0, {}

            w.cortex.entry_multiplier = fake_entry_multiplier

            async def _fetch_spot(_sym):
                if _sym in ("USDTIRT", "USDT", "USDTTMN"):
                    return None
                return 100.0

            bot.feed = types.SimpleNamespace(
                fetch_spot=mock.AsyncMock(side_effect=_fetch_spot),
                peek_mid=Mock(return_value=0.0),
                _spot_cache={
                    sym: 100.0,
                    "USDTIRT": None,
                    "USDT": None,
                    "USDTTMN": None,
                },
            )

            bot.usdt_px = None
            bot._usdt_px = None
            bot.last_usdt_px = None
            bot._last_usdt_px = None
            bot.usdt_irt = None
            bot._usdt_irt = None

            bot.phoenix = types.SimpleNamespace(
                update=Mock(
                    return_value=types.SimpleNamespace(
                        state="LONG",
                        confidence=0.90,
                        composite=0.50,
                        rsi=55.0,
                        shadow_score=None,
                        shadow_label="TEST",
                        ready=True,
                        reason="TEST_READY",
                    )
                )
            )

            bot.sanity = types.SimpleNamespace(evaluate=Mock(return_value=(False, "")))

            bot.orders = types.SimpleNamespace(
                pending=Mock(return_value=[]),
            )

            bot.dzh = types.SimpleNamespace(
                observe_alpha=Mock(),
                evaluate_entry=Mock(return_value=(True, "OK")),
            )

            bot.risk = types.SimpleNamespace(
                safe_mode=False,
                safe_level=Mock(return_value="OFF"),
                size_notional=Mock(return_value=1000.0),
                can_open_explain=Mock(return_value=(True, "OK", {})),
            )

            bot.net = types.SimpleNamespace(
                is_safe_mode=Mock(return_value=False),
            )

            bot._phoenix_px_hist = {}
            bot._cycle_best_conf = 0.0
            bot._last_buy_ts = {}
            bot._last_risk_ts = {}

            with patch.object(
                s43, "_obs_reject", create=True
            ) as obs_reject, patch.object(
                s43, "_record_why_no_trade", create=True
            ) as record_why_no_trade, patch.object(
                s43, "_VETO_REG", create=True
            ) as veto_reg:
                now = time.time()
                book = types.SimpleNamespace(
                    bid=1_000_000.0,
                    ask=1_001_000.0,
                    mid=1_000_500.0,
                    spread_bps=10.0,
                    ts=now,
                    timestamp=now,
                    _ts_event=now,
                    _source="TEST_BOOK",
                )

                w.book = book
                w.last_book = book
                w.top = book
                w.orderbook = book
                w.order_book = book
                w.book_top = book

                bot.obsvc = types.SimpleNamespace(
                    peek=mock.Mock(return_value=book),
                    request_refresh=mock.AsyncMock(return_value=None),
                )

                bot.feed._cache = {}
                bot.feed.get_book = mock.Mock(return_value=book)
                bot.feed.book = mock.Mock(return_value=book)
                bot.feed.top = mock.Mock(return_value=book)
                bot.feed.get_top = mock.Mock(return_value=book)
                bot.feed.orderbook = mock.Mock(return_value=book)
                bot.feed.get_orderbook = mock.Mock(return_value=book)
                bot.feed.get_orderbook_top = mock.Mock(return_value=book)

                bot.recorder = None

                asyncio.run(bot._process_symbol_heartbeat(w, sym, cash_irt=10_000.0))

                self.assertFalse(
                    entry_multiplier_called,
                    "entry_multiplier should not be called on NO_DATA:USDT_PX; "
                    f"last_event={getattr(w, 'last_event', None)!r}, "
                    f"last_engine_status={getattr(w, 'last_engine_status', None)!r}, "
                    f"last_engine_reason={getattr(w, 'last_engine_reason', None)!r}",
                )
                self.assertEqual(w.last_engine_status, "Hold")
                self.assertEqual(w.last_engine_reason, "NO_DATA:USDT_PX")
                self.assertIsInstance(w.last_engine_ts, float)

                info_messages = [
                    str(call.args[0])
                    for call in bot._log.info.call_args_list
                    if call.args
                ]
                self.assertFalse(
                    any("event=COLLECTIVE_BOOST" in msg for msg in info_messages),
                    "COLLECTIVE_BOOST was reached after NO_DATA:USDT_PX. infos=%r"
                    % info_messages,
                )

                obs_reject.assert_called()
                obs_args, obs_kwargs = obs_reject.call_args

                self.assertGreaterEqual(len(obs_args), 2)
                self.assertIs(obs_args[0], w)
                self.assertEqual(obs_args[1], "NO_DATA:USDT_PX")
                self.assertEqual(obs_kwargs.get("symbol"), sym)

                reject_meta = obs_kwargs.get("meta")
                self.assertIsInstance(reject_meta, dict)
                self.assertEqual(reject_meta.get("sym"), sym)

                veto_reg.note.assert_called()
                veto_blob = {
                    "args": veto_reg.note.call_args.args,
                    "kwargs": veto_reg.note.call_args.kwargs,
                }
                self.assertIn("NO_DATA:USDT_PX", repr(veto_blob))
                self.assertIn("Hold", repr(veto_blob))

                record_why_no_trade.assert_called()
                why_blob = {
                    "args": record_why_no_trade.call_args.args,
                    "kwargs": record_why_no_trade.call_args.kwargs,
                }
                self.assertIn("NO_DATA:USDT_PX", repr(why_blob))
                self.assertIn("Hold", repr(why_blob))

        finally:
            if old_warmup is None:
                os.environ.pop("BOT_WARMUP_SEC", None)
            else:
                os.environ["BOT_WARMUP_SEC"] = old_warmup

            try:
                if had_boot_ts:
                    setattr(s43, "_BOOT_TS", old_boot_ts)
                else:
                    delattr(s43, "_BOOT_TS")
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main(verbosity=2)
