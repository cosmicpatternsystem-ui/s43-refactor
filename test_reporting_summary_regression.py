import asyncio
import s43


def _root_exc(e):
    fn = getattr(s43, "_s43_status_root_exc", None)
    if callable(fn):
        try:
            return fn(e)
        except Exception:
            pass
    cur = e
    seen = set()
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        nxt = getattr(cur, "__cause__", None) or getattr(cur, "__context__", None)
        if nxt is None:
            break
        cur = nxt
    return cur


def _format_exc(e):
    fn = getattr(s43, "_s43_status_format_exc", None)
    if callable(fn):
        try:
            return fn(e)
        except Exception:
            pass
    try:
        msg = str(e)
    except Exception:
        msg = ""
    return msg or type(e).__name__


def _classify_exc(e):
    fn = getattr(s43, "_s43_status_classify_exc", None)
    if callable(fn):
        try:
            return fn(e)
        except Exception:
            pass

    text = ""
    try:
        text = f"{type(e).__name__} {_format_exc(e)}".lower()
    except Exception:
        pass

    if "403" in text or "forbidden" in text:
        return "forbidden"
    if "timeout" in text:
        return "timeout"
    if "connection" in text or "network" in text:
        return "network"
    return "exception"


class DummyWallet:
    def __init__(
        self,
        name,
        disabled=False,
        reason="",
        last_balance_ok=False,
    ):
        self.name = name
        self.wallet_disabled = disabled
        self.wallet_disable_reason = reason
        self.last_balance_ok = last_balance_ok


class DummyBot:
    def __init__(self, outcomes):
        self.outcomes = outcomes

    async def _refresh_balance_if_needed(self, w):
        outcome = self.outcomes[w.name]
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    async def _refresh_orders_if_needed(self, w):
        return 0


async def collect_summary(wallets, bot):
    total = 0
    disabled_count = 0
    balance_ok_count = 0
    balance_failed_count = 0
    rows = []

    for w in wallets:
        total += 1
        wn = str(getattr(w, "name", "?") or "?")
        disabled = bool(getattr(w, "wallet_disabled", False))
        reason = str(getattr(w, "wallet_disable_reason", "") or "")
        if disabled:
            disabled_count += 1

        cash = None
        n_orders = None
        balance_ok = False
        balance_error = ""
        balance_error_type = ""
        balance_error_class = ""

        if not disabled:
            try:
                cash = float(await bot._refresh_balance_if_needed(w))
            except Exception as e:
                balance_failed_count += 1
                root = _root_exc(e)
                try:
                    balance_error_type = type(root).__name__
                except Exception:
                    balance_error_type = "Exception"
                balance_error = _format_exc(root)
                balance_error_class = _classify_exc(root)
            else:
                balance_ok = bool(getattr(w, "last_balance_ok", False))

                if getattr(w, "last_balance_ok", False):
                    balance_ok = True
                    balance_ok_count += 1
                else:
                    balance_ok = False
                    balance_failed_count += 1

                    if not balance_error:
                        balance_error_type = "BalanceStatusError"
                        balance_error = "last_balance_ok_false"
                        balance_error_class = "balance_status_failed"
        else:
            balance_ok = False
            if not balance_error:
                balance_error_type = "WalletDisabled"
                balance_error_class = "wallet_disabled"
                balance_error = reason or "wallet_disabled"

        try:
            n_orders = int(await bot._refresh_orders_if_needed(w))
        except Exception:
            n_orders = None

        rows.append(
            {
                "wallet": wn,
                "disabled": disabled,
                "reason": reason,
                "balance_ok": balance_ok,
                "balance_error": balance_error,
                "balance_error_type": balance_error_type,
                "balance_error_class": balance_error_class,
                "cash": cash,
                "open_orders": n_orders,
            }
        )

    return {
        "total": total,
        "disabled_count": disabled_count,
        "balance_ok_count": balance_ok_count,
        "balance_failed_count": balance_failed_count,
        "rows": rows,
    }


def format_summary(result):
    return (
        f"summary wallets={result['total']} "
        f"disabled={result['disabled_count']} "
        f"balance_ok={result['balance_ok_count']} "
        f"balance_failed={result['balance_failed_count']}"
    )


def test_disabled_wallet_not_counted_as_failed():
    wallets = [
        DummyWallet(
            "w_disabled",
            disabled=True,
            reason="403_forbidden",
            last_balance_ok=False,
        )
    ]
    bot = DummyBot({"w_disabled": 1000})

    result = asyncio.run(collect_summary(wallets, bot))

    assert result["total"] == 1
    assert result["disabled_count"] == 1
    assert result["balance_ok_count"] == 0
    assert result["balance_failed_count"] == 0

    row = result["rows"][0]
    assert row["disabled"] is True
    assert row["balance_ok"] is False
    assert row["balance_error_type"] == "WalletDisabled"
    assert row["balance_error_class"] == "wallet_disabled"
    assert row["balance_error"] == "403_forbidden"


def test_last_balance_ok_false_counts_as_failed():
    wallets = [
        DummyWallet(
            "w_false",
            disabled=False,
            last_balance_ok=False,
        )
    ]
    bot = DummyBot({"w_false": 12345})

    result = asyncio.run(collect_summary(wallets, bot))

    assert result["total"] == 1
    assert result["disabled_count"] == 0
    assert result["balance_ok_count"] == 0
    assert result["balance_failed_count"] == 1

    row = result["rows"][0]
    assert row["disabled"] is False
    assert row["balance_ok"] is False
    assert row["cash"] == 12345.0
    assert row["balance_error_type"] == "BalanceStatusError"
    assert row["balance_error_class"] == "balance_status_failed"
    assert row["balance_error"] == "last_balance_ok_false"


def test_last_balance_ok_true_counts_as_ok():
    wallets = [
        DummyWallet(
            "w_ok",
            disabled=False,
            last_balance_ok=True,
        )
    ]
    bot = DummyBot({"w_ok": 67890})

    result = asyncio.run(collect_summary(wallets, bot))

    assert result["total"] == 1
    assert result["disabled_count"] == 0
    assert result["balance_ok_count"] == 1
    assert result["balance_failed_count"] == 0

    row = result["rows"][0]
    assert row["disabled"] is False
    assert row["balance_ok"] is True
    assert row["cash"] == 67890.0
    assert row["balance_error_type"] == ""
    assert row["balance_error_class"] == ""
    assert row["balance_error"] == ""


def test_refresh_exception_counts_as_failed():
    wallets = [
        DummyWallet(
            "w_exc",
            disabled=False,
            last_balance_ok=False,
        )
    ]
    bot = DummyBot({"w_exc": RuntimeError("403 forbidden")})

    result = asyncio.run(collect_summary(wallets, bot))

    assert result["total"] == 1
    assert result["disabled_count"] == 0
    assert result["balance_ok_count"] == 0
    assert result["balance_failed_count"] == 1

    row = result["rows"][0]
    assert row["disabled"] is False
    assert row["balance_ok"] is False
    assert row["balance_error"] != ""
    assert row["balance_error_type"] == "RuntimeError"
    assert row["balance_error_class"] in ("forbidden", "exception")


def test_mixed_summary_matches_expected_counts():
    wallets = [
        DummyWallet("w_ok", disabled=False, last_balance_ok=True),
        DummyWallet("w_false", disabled=False, last_balance_ok=False),
        DummyWallet("w_disabled", disabled=True, reason="403_forbidden", last_balance_ok=False),
    ]
    bot = DummyBot(
        {
            "w_ok": 5000,
            "w_false": 4000,
            "w_disabled": 3000,
        }
    )

    result = asyncio.run(collect_summary(wallets, bot))

    assert result["total"] == 3
    assert result["disabled_count"] == 1
    assert result["balance_ok_count"] == 1
    assert result["balance_failed_count"] == 1


def test_summary_string_matches_expected_contract():
    wallets = [
        DummyWallet("w_ok", disabled=False, last_balance_ok=True),
        DummyWallet("w_false", disabled=False, last_balance_ok=False),
        DummyWallet("w_disabled", disabled=True, reason="403_forbidden", last_balance_ok=False),
    ]
    bot = DummyBot(
        {
            "w_ok": 5000,
            "w_false": 4000,
            "w_disabled": 3000,
        }
    )

    result = asyncio.run(collect_summary(wallets, bot))
    summary = format_summary(result)

    assert summary == "summary wallets=3 disabled=1 balance_ok=1 balance_failed=1"


def main():
    tests = [
        test_disabled_wallet_not_counted_as_failed,
        test_last_balance_ok_false_counts_as_failed,
        test_last_balance_ok_true_counts_as_ok,
        test_refresh_exception_counts_as_failed,
        test_mixed_summary_matches_expected_counts,
        test_summary_string_matches_expected_contract,
    ]

    for t in tests:
        t()
        print(f"PASS {t.__name__}")

    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
