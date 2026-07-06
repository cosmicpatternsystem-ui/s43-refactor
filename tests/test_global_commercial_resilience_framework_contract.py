from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_global_commercial_resilience_framework_exists():
    path = ROOT / "docs" / "strategy" / "GLOBAL_COMMERCIAL_RESILIENCE_FRAMEWORK.md"
    assert path.exists(), "Global commercial resilience framework must exist"


def test_global_commercial_resilience_framework_is_normative():
    path = ROOT / "docs" / "strategy" / "GLOBAL_COMMERCIAL_RESILIENCE_FRAMEWORK.md"
    text = path.read_text(encoding="utf-8")
    required = [
        "Canonical.",
        "Normative.",
        "Repository-governed.",
        "Commercially binding",
        "Commercial Non-Negotiables",
        "Pricing Discipline",
        "Payment and Cash Realization",
        "Commitment Integrity",
        "Counterparty Fitness",
        "Exception Governance",
        "Deal Review Triggers",
        "Renewal Protection",
        "Global Operating Doctrine",
        "Anti-Fragility Controls",
        "Minimum Evidence Standard",
        "Enforcement",
    ]
    for item in required:
        assert item in text, f"Missing required framework marker: {item}"


def test_global_commercial_resilience_framework_contains_no_go_and_cash_rules():
    path = ROOT / "docs" / "strategy" / "GLOBAL_COMMERCIAL_RESILIENCE_FRAMEWORK.md"
    text = path.read_text(encoding="utf-8")
    required = [
        "NO-GO Band",
        "NO-GO Counterparty Triggers",
        "Cash Preservation Rules",
        "Revenue quality outranks headline revenue.",
        "Cash certainty outranks booked optimism.",
        "Delivery truth outranks sales enthusiasm.",
        "Margin discipline outranks discretionary discounting.",
        "No commercial exception is valid if it is not documented.",
    ]
    for item in required:
        assert item in text, f"Missing resilience control: {item}"
