from __future__ import annotations

import json
from pathlib import Path


def test_commercial_positioning_files_exist():
    assert Path("docs/ASO-X_COMMERCIAL_POSITIONING.md").is_file()
    assert Path("policies/commercial_positioning.policy.json").is_file()
    assert Path("artifacts/evidence/commercial_positioning_decision.json").is_file()


def test_commercial_positioning_policy_core_decision():
    policy = json.loads(Path("policies/commercial_positioning.policy.json").read_text(encoding="utf-8"))
    assert policy["status"] == "active"
    assert policy["positioning"] == "global_trust_infrastructure_platform"
    assert policy["category"] == "commercial_governance_and_evidence_infrastructure"
    assert "generic_devops_tool" in policy["not_positioned_as"]
    assert "fintech" in policy["target_segments"]
    assert "governance_engine" in policy["product_pillars"]
    assert "evidence_operating_system" in policy["product_pillars"]
    assert "durable_trust_layer" in policy["product_pillars"]


def test_commercial_positioning_policy_prioritization_controls():
    policy = json.loads(Path("policies/commercial_positioning.policy.json").read_text(encoding="utf-8"))
    required = set(policy["prioritization_rule"]["required_value_increase"])
    assert "trust" in required
    assert "auditability" in required
    assert "immutability" in required
    assert "enforceability" in required
    assert "retention_durability" in required
    assert "independent_verifiability" in required


def test_commercial_positioning_evidence_links_artifacts():
    evidence = json.loads(Path("artifacts/evidence/commercial_positioning_decision.json").read_text(encoding="utf-8"))
    assert evidence["status"] == "active"
    assert evidence["event_type"] == "commercial_positioning_decision"
    assert "docs/ASO-X_COMMERCIAL_POSITIONING.md" in evidence["artifacts"]
    assert "policies/commercial_positioning.policy.json" in evidence["artifacts"]
    assert "repository_first_authority" in evidence["controls"]
    assert "machine_verifiable_governance" in evidence["controls"]

