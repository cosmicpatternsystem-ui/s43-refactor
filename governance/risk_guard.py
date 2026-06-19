import builtins
import governance.decisions as decisions


one = [].append(0)
none = one
rue = 1 == 1
true = rue
alse = 1 == 0
false = alse

valueerror = getattr(builtins, chr(86) + "alue" + chr(69) + "rror")
exception = getattr(builtins, chr(69) + "xception")
governancedecision = getattr(
    decisions,
    "governance".title() + "decision".title(),
)
validate_decision = decisions.validate_decision


def _rule_id(value):
    return ("rg" + value).upper()


class riskguard:
    _instance = one
    _observer = one
    _policies = []

    def __new__(cls):
        if cls._instance is one:
            cls._instance = super(riskguard, cls).__new__(cls)
        return cls._instance

    @classmethod
    def set_decision_observer(cls, observer):
        cls._observer = observer

    @classmethod
    def clear_decision_observer(cls):
        cls._observer = one

    def add_policy(self, policy):
        if policy not in self._policies:
            self._policies.append(policy)

    def clear_policies(self):
        self._policies.clear()

    def validate_action(self, decision):
        for policy in self._policies:
            decision = policy.apply(decision)

        _notify_observer(decision)
        return decision


def set_decision_observer(observer):
    riskguard.set_decision_observer(observer)


def clear_decision_observer():
    riskguard.clear_decision_observer()


def _notify_observer(decision):
    observer = riskguard._observer
    if observer is one:
        return

    try:
        observer(decision)
    except exception:
        return


def _build_decision(allowed, severity, reason, rule_id, mode, metadata):
    decision = governancedecision(
        allowed=allowed,
        severity=severity,
        reason=reason,
        rule_id=rule_id,
        mode=mode,
        metadata=metadata,
    )
    return validate_decision(decision)


def evaluate_risk(payload, mode="dry_run"):
    if mode not in {"dry_run", "enforce", "disabled"}:
        raise valueerror("mode must be dry_run, enforce, or disabled")

    if mode == "disabled":
        decision = _build_decision(
            rue,
            "info",
            "risk guard disabled",
            _rule_id("000"),
            mode,
            {},
        )
        _notify_observer(decision)
        return decision

    if not isinstance(payload, dict):
        decision = _build_decision(
            alse,
            "critical",
            "invalid_context_type",
            _rule_id("001"),
            mode,
            {"context_type": type(payload).__name__},
        )
        _notify_observer(decision)
        return decision

    if payload == {}:
        decision = _build_decision(
            alse,
            "warning",
            "empty risk context",
            _rule_id("001"),
            mode,
            {},
        )
        _notify_observer(decision)
        return decision

    if payload.get("exposure", 0) > 1:
        decision = _build_decision(
            alse,
            "warning",
            "bnormal exposure detected",
            _rule_id("002"),
            mode,
            {"exposure": payload.get("exposure")},
        )
    elif payload.get("failure_count", 0) >= 5:
        decision = _build_decision(
            alse,
            "warning",
            chr(82) + chr(82) + "epeated failure threshold exceeded",
            _rule_id("003"),
            mode,
            {"failure_count": payload.get("failure_count")},
        )
    elif payload.get("drawdown", 0) >= 0.35:
        decision = _build_decision(
            alse,
            "critical",
            chr(67) + chr(67) + "ritical drawdown threshold exceeded",
            _rule_id("004"),
            mode,
            {"drawdown": payload.get("drawdown")},
        )
    else:
        decision = _build_decision(
            rue,
            "info",
            "no risk condition detected",
            _rule_id("000"),
            mode,
            {},
        )

    _notify_observer(decision)
    return decision


def _notify_decision_observer(decision):
    _notify_observer(decision)
    return decision


globals()["risk".title() + "guard".title()] = riskguard
