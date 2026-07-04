#!/usr/bin/env python3
"""Deterministic policy-to-action matrix for ASO-X autopilot.

This module is the decision layer for the autopilot system. It translates
normalized policy inputs into proposed actions without executing those actions.

Design constraints:
- Standard library only.
- Deterministic output.
- No network access.
- No filesystem writes.
- Safe JSON stdout with ensure_ascii=True.
- Decision and execution remain separated.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Mapping
from typing import Optional
from typing import Sequence


SEVERITY_ORDER: Dict[str, int] = {
    "low": 10,
    "medium": 20,
    "high": 30,
    "critical": 40,
}

ACTION_PRIORITIES: Dict[str, int] = {
    "ignore": 0,
    "log_observation": 10,
    "queue_operator_review": 30,
    "create_alert": 40,
    "request_kill_switch_review": 50,
}

VALID_ACTION_TYPES = frozenset(ACTION_PRIORITIES.keys())

FINANCIAL_EXPOSURE_TAGS = frozenset(
    {
        "financial_exposure",
        "real_money",
        "capital_at_risk",
        "market_risk",
        "credit_risk",
        "liquidity_risk",
        "settlement_risk",
        "counterparty_risk",
    }
)

CONTROL_RISK_TAGS = frozenset(
    {
        "control_failure",
        "policy_violation",
        "ledger_gap",
        "audit_gap",
        "unsafe_execution",
        "unexpected_mutation",
        "kill_switch",
    }
)

HIGH_CONFIDENCE_THRESHOLD = 0.80
MEDIUM_CONFIDENCE_THRESHOLD = 0.50


@dataclass(frozen=True)
class PolicyInput:
    """Normalized signal presented to the policy matrix."""

    subject: str
    signal_type: str
    severity: str
    confidence: float
    source: str
    summary: str
    requires_human_review: bool
    tags: List[str]


@dataclass(frozen=True)
class ProposedAction:
    """Action proposed by policy, not executed by policy."""

    action_type: str
    approval_required: bool
    priority: int
    subject: str
    source_signal_type: str
    source: str
    severity: str
    confidence: float
    reason_codes: List[str]
    rationale: List[str]


@dataclass(frozen=True)
class PolicyDecision:
    """Complete deterministic policy decision envelope."""

    schema_version: str
    decision_engine: str
    input: PolicyInput
    proposed_actions: List[ProposedAction]
    decision_notes: List[str]


class PolicyMatrixError(ValueError):
    """Raised when policy input cannot be normalized safely."""


def _normalize_text(value: Any, field_name: str) -> str:
    if value is None:
        raise PolicyMatrixError("missing required field: " + field_name)
    text = str(value).strip()
    if not text:
        raise PolicyMatrixError("empty required field: " + field_name)
    return text


def _normalize_severity(value: Any) -> str:
    text = _normalize_text(value, "severity").lower()
    aliases = {
        "info": "low",
        "informational": "low",
        "minor": "low",
        "moderate": "medium",
        "med": "medium",
        "major": "high",
        "severe": "critical",
        "crit": "critical",
    }
    normalized = aliases.get(text, text)
    if normalized not in SEVERITY_ORDER:
        raise PolicyMatrixError(
            "invalid severity: "
            + repr(value)
            + "; expected one of "
            + ", ".join(sorted(SEVERITY_ORDER))
        )
    return normalized


def _normalize_confidence(value: Any) -> float:
    if value is None:
        raise PolicyMatrixError("missing required field: confidence")
    try:
        confidence = float(value)
    except (TypeError, ValueError) as exc:
        raise PolicyMatrixError("confidence must be numeric") from exc
    if confidence < 0.0 or confidence > 1.0:
        raise PolicyMatrixError("confidence must be between 0.0 and 1.0")
    return round(confidence, 4)


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("1", "true", "yes", "y", "on"):
            return True
        if text in ("0", "false", "no", "n", "off"):
            return False
    if isinstance(value, int):
        return bool(value)
    raise PolicyMatrixError("requires_human_review must be boolean-like")


def _normalize_tags(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = [item.strip() for item in value.split(",")]
    elif isinstance(value, Iterable):
        raw_items = [str(item).strip() for item in value]
    else:
        raise PolicyMatrixError("tags must be a list or comma-separated string")

    tags = sorted({item.lower() for item in raw_items if item})
    return tags


def normalize_policy_input(raw: Mapping[str, Any]) -> PolicyInput:
    """Normalize and validate raw input into PolicyInput."""

    return PolicyInput(
        subject=_normalize_text(raw.get("subject"), "subject"),
        signal_type=_normalize_text(raw.get("signal_type"), "signal_type").lower(),
        severity=_normalize_severity(raw.get("severity")),
        confidence=_normalize_confidence(raw.get("confidence")),
        source=_normalize_text(raw.get("source"), "source"),
        summary=_normalize_text(raw.get("summary"), "summary"),
        requires_human_review=_normalize_bool(raw.get("requires_human_review", False)),
        tags=_normalize_tags(raw.get("tags", [])),
    )


def _has_any(tags: Sequence[str], candidates: Iterable[str]) -> bool:
    tag_set = set(tags)
    for candidate in candidates:
        if candidate in tag_set:
            return True
    return False


def _make_action(
    action_type: str,
    approval_required: bool,
    policy_input: PolicyInput,
    reason_codes: Sequence[str],
    rationale: Sequence[str],
) -> ProposedAction:
    if action_type not in VALID_ACTION_TYPES:
        raise PolicyMatrixError("invalid action_type generated: " + action_type)

    return ProposedAction(
        action_type=action_type,
        approval_required=approval_required,
        priority=ACTION_PRIORITIES[action_type],
        subject=policy_input.subject,
        source_signal_type=policy_input.signal_type,
        source=policy_input.source,
        severity=policy_input.severity,
        confidence=policy_input.confidence,
        reason_codes=sorted(set(reason_codes)),
        rationale=list(rationale),
    )


def evaluate_policy_input(policy_input: PolicyInput) -> PolicyDecision:
    """Evaluate one normalized policy input.

    The matrix intentionally favors control and auditability over automation.
    It proposes actions only; execution remains the responsibility of the
    autopilot execution layer.
    """

    actions: List[ProposedAction] = []
    notes: List[str] = []

    severity_rank = SEVERITY_ORDER[policy_input.severity]
    has_financial_exposure = _has_any(policy_input.tags, FINANCIAL_EXPOSURE_TAGS)
    has_control_risk = _has_any(policy_input.tags, CONTROL_RISK_TAGS)
    high_confidence = policy_input.confidence >= HIGH_CONFIDENCE_THRESHOLD
    medium_confidence = policy_input.confidence >= MEDIUM_CONFIDENCE_THRESHOLD

    notes.append("decision layer only; no action was executed")

    if policy_input.requires_human_review:
        notes.append("input explicitly requires human review")

    if has_control_risk and severity_rank >= SEVERITY_ORDER["high"]:
        actions.append(
            _make_action(
                action_type="request_kill_switch_review",
                approval_required=True,
                policy_input=policy_input,
                reason_codes=[
                    "CONTROL_RISK",
                    "HIGH_OR_CRITICAL_SEVERITY",
                    "HUMAN_APPROVAL_REQUIRED",
                ],
                rationale=[
                    "control-risk tag detected",
                    "severity is high or critical",
                    "operator review is required before execution",
                ],
            )
        )

    if policy_input.severity == "critical" and high_confidence:
        actions.append(
            _make_action(
                action_type="create_alert",
                approval_required=False,
                policy_input=policy_input,
                reason_codes=[
                    "CRITICAL_SEVERITY",
                    "HIGH_CONFIDENCE",
                ],
                rationale=[
                    "critical severity with high confidence",
                    "alert creation is non-destructive",
                ],
            )
        )

    if (
        severity_rank >= SEVERITY_ORDER["high"]
        and has_financial_exposure
        and medium_confidence
    ):
        actions.append(
            _make_action(
                action_type="queue_operator_review",
                approval_required=True,
                policy_input=policy_input,
                reason_codes=[
                    "FINANCIAL_EXPOSURE",
                    "HIGH_OR_CRITICAL_SEVERITY",
                    "MEDIUM_OR_HIGH_CONFIDENCE",
                    "HUMAN_APPROVAL_REQUIRED",
                ],
                rationale=[
                    "financial exposure tag detected",
                    "severity is high or critical",
                    "real-money related decisions require operator review",
                ],
            )
        )

    if not actions and severity_rank >= SEVERITY_ORDER["medium"]:
        actions.append(
            _make_action(
                action_type="log_observation",
                approval_required=False,
                policy_input=policy_input,
                reason_codes=[
                    "OBSERVATION_ONLY",
                    "MEDIUM_OR_HIGHER_SEVERITY",
                ],
                rationale=[
                    "signal should be retained for audit",
                    "no execution action is justified by the current matrix",
                ],
            )
        )

    if not actions:
        if policy_input.confidence < MEDIUM_CONFIDENCE_THRESHOLD:
            reason_codes = ["LOW_CONFIDENCE", "NO_ACTION"]
            rationale = [
                "confidence is below medium threshold",
                "signal is retained only if upstream ledger captures it",
            ]
            action_type = "ignore"
        else:
            reason_codes = ["LOW_SEVERITY", "OBSERVATION_ONLY"]
            rationale = [
                "severity does not justify escalation",
                "observation logging is sufficient",
            ]
            action_type = "log_observation"

        actions.append(
            _make_action(
                action_type=action_type,
                approval_required=False,
                policy_input=policy_input,
                reason_codes=reason_codes,
                rationale=rationale,
            )
        )

    actions = sorted(
        actions,
        key=lambda item: (
            -item.priority,
            item.action_type,
            item.subject,
            ",".join(item.reason_codes),
        ),
    )

    return PolicyDecision(
        schema_version="policy_matrix.v1",
        decision_engine="aso-x.policy_matrix.deterministic.v1",
        input=policy_input,
        proposed_actions=actions,
        decision_notes=notes,
    )


def evaluate_raw_policy_input(raw: Mapping[str, Any]) -> PolicyDecision:
    """Normalize and evaluate a raw mapping."""

    return evaluate_policy_input(normalize_policy_input(raw))


def decision_to_dict(decision: PolicyDecision) -> Dict[str, Any]:
    """Convert a policy decision to a JSON-serializable dict."""

    return asdict(decision)


def decision_to_json(decision: PolicyDecision, pretty: bool = True) -> str:
    """Serialize a decision with ASCII-safe JSON."""

    if pretty:
        return json.dumps(
            decision_to_dict(decision),
            indent=2,
            sort_keys=True,
            ensure_ascii=True,
        )
    return json.dumps(decision_to_dict(decision), sort_keys=True, ensure_ascii=True)


def _load_json_file(path: str) -> Mapping[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise PolicyMatrixError("input JSON must be an object")
    return data


def _sample_input() -> Dict[str, Any]:
    return {
        "subject": "autopilot.execution.loop",
        "signal_type": "runtime_control_signal",
        "severity": "high",
        "confidence": 0.91,
        "source": "local_smoke_test",
        "summary": "High-severity financial exposure signal for policy matrix validation.",
        "requires_human_review": False,
        "tags": [
            "financial_exposure",
            "real_money",
            "audit_gap",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate a deterministic ASO-X policy-to-action matrix input."
    )
    parser.add_argument(
        "--input-json",
        dest="input_json",
        default=None,
        help="Path to a UTF-8 JSON object containing a policy input.",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Evaluate a built-in deterministic sample input.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Emit compact JSON instead of pretty JSON.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.input_json:
            raw = _load_json_file(args.input_json)
        else:
            raw = _sample_input()

        decision = evaluate_raw_policy_input(raw)
        sys.stdout.write(decision_to_json(decision, pretty=not args.compact))
        sys.stdout.write("\n")
        return 0
    except PolicyMatrixError as exc:
        payload = {
            "ok": False,
            "error_type": "PolicyMatrixError",
            "error": str(exc),
        }
        sys.stderr.write(json.dumps(payload, sort_keys=True, ensure_ascii=True))
        sys.stderr.write("\n")
        return 2
    except json.JSONDecodeError as exc:
        payload = {
            "ok": False,
            "error_type": "JSONDecodeError",
            "error": str(exc),
        }
        sys.stderr.write(json.dumps(payload, sort_keys=True, ensure_ascii=True))
        sys.stderr.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())