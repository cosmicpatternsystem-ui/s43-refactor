import s43


def test_redact_argv_for_report_masks_arzplus_authorization_header_value():
    args = [
        "--header",
        "Authorization: Token x",
        "--symbol=BTCIRT",
    ]

    redacted = s43._redact_argv_for_report(args)

    assert redacted == [
        "--header",
        "Authorization: <redacted>",
        "--symbol=BTCIRT",
    ]


def test_redact_argv_for_report_masks_sensitive_equals_args():
    args = [
        "--token=x",
        "--authorization=Token x",
        "--secret=x",
        "--password=x",
        "--bearer=x",
        "--api-key=x",
    ]

    redacted = s43._redact_argv_for_report(args)

    assert redacted == [
        "--token=<redacted>",
        "--authorization=<redacted>",
        "--secret=<redacted>",
        "--password=<redacted>",
        "--bearer=<redacted>",
        "--api-key=<redacted>",
    ]


def test_redact_argv_for_report_masks_sensitive_split_args():
    args = [
        "--token",
        "x",
        "--authorization",
        "Token x",
        "--secret",
        "x",
        "--password",
        "x",
        "--bearer",
        "x",
    ]

    redacted = s43._redact_argv_for_report(args)

    assert redacted == [
        "--token",
        "<redacted>",
        "--authorization",
        "<redacted>",
        "--secret",
        "<redacted>",
        "--password",
        "<redacted>",
        "--bearer",
        "<redacted>",
    ]


def test_redact_argv_for_report_keeps_non_sensitive_args():
    args = [
        "--mode=prod",
        "--symbol=BTCUSDT",
        "--limit",
        "10",
        "--ip-whitelist-note=enabled-in-exchange-panel",
    ]

    redacted = s43._redact_argv_for_report(args)

    assert redacted == args
