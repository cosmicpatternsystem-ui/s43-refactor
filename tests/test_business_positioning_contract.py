from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_business_positioning_declares_real_money_lock() -> None:
    content = read_text("BUSINESS_POSITIONING.md")

    assert "LOCK-BIZ-001" in content
    assert (
        "If ASO-X cannot protect money, unlock money, or prove control over money, "
        "it is not a global-grade business."
    ) in content
    assert "Target Buyer" in content
    assert "Enterprise Value Proposition" in content
    assert "North Star Metric" in content
    assert "global-grade business" in content


def test_enterprise_control_plane_declares_capability_mapping_lock() -> None:
    content = read_text("ENTERPRISE_CONTROL_PLANE.md")

    assert "LOCK-BIZ-002" in content
    assert (
        "Every enterprise-facing ASO-X capability must map to a real-money control, "
        "proof, or enforcement outcome."
    ) in content


def test_enterprise_execution_artifacts_exist() -> None:
    required_artifacts = [
        "ENTERPRISE_CONTROL_PLANE.md",
        "BUYER_PERSONAS.md",
        "REAL_MONEY_USE_CASES.md",
        "ENTERPRISE_ACCEPTANCE_CRITERIA.md",
    ]

    for artifact in required_artifacts:
        assert (ROOT / artifact).is_file(), artifact


def test_enterprise_artifacts_remain_real_money_focused() -> None:
    required_terms_by_artifact = {
        "BUYER_PERSONAS.md": ["Chief Risk Officer", "material loss", "real-money decisions"],
        "REAL_MONEY_USE_CASES.md": ["policy drift", "capital", "auditability"],
        "ENTERPRISE_ACCEPTANCE_CRITERIA.md": ["Protects real money", "auditability", "enterprise-core"],
    }

    for artifact, required_terms in required_terms_by_artifact.items():
        content = read_text(artifact)
        for term in required_terms:
            assert term in content, f"{term!r} missing from {artifact}"
