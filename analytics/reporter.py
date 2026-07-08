import json
import csv
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict


DEFAULT_LOG_FILE = "governance_audit.log"

TEXT_LOG_PATTERN = re.compile(
    r"^\[(?P<phase>[^\]]+)\]\s+"
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\|\s+"
    r"Action:\s*(?P<action>.*?)\s+\|\s+"
    r"Outcome:\s*(?P<outcome>.*?)\s+\|\s+"
    r"Rule:\s*(?P<rule>.*?)\s+\|\s+"
    r"Reason:\s*(?P<reason>.*)$"
)


def parse_json_line(line: str):
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def parse_text_log_line(line: str):
    match = TEXT_LOG_PATTERN.match(line.strip())
    if not match:
        return None

    data = match.groupdict()
    return {
        "source_format": "phase_text_log",
        "phase": data.get("phase"),
        "timestamp": data.get("timestamp"),
        "action": data.get("action"),
        "outcome": str(data.get("outcome", "")).upper(),
        "rule": data.get("rule"),
        "reason": data.get("reason"),
    }


def parse_log_line(line: str):
    line = line.strip()
    if not line:
        return None

    obj = parse_json_line(line)
    if obj is not None:
        return obj

    obj = parse_text_log_line(line)
    if obj is not None:
        return obj

    return None


def load_records(log_file=DEFAULT_LOG_FILE):
    path = Path(log_file)
    if not path.exists():
        raise FileNotFoundError(f"Log file not found: {log_file}")

    records = []
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            obj = parse_log_line(line)
            if obj is not None:
                records.append(obj)
    return records


def normalize_reason(record):
    reason = record.get("reason")
    if reason:
        return str(reason).strip()

    denial_reason = record.get("denial_reason")
    if denial_reason:
        return str(denial_reason).strip()

    details = record.get("details")
    if isinstance(details, dict):
        for key in ("reason", "denial_reason", "message", "error"):
            if details.get(key):
                return str(details[key]).strip()

    return "UNKNOWN"


def normalize_action(record):
    for key in ("action", "event", "type", "operation"):
        value = record.get(key)
        if value:
            return str(value).strip()
    return "UNKNOWN"


def normalize_outcome(record):
    for key in ("outcome", "decision", "status", "result"):
        value = record.get(key)
        if value:
            return str(value).strip().upper()
    return "UNKNOWN"


def summarize_records(records):
    total = len(records)
    outcomes = Counter()
    reasons = Counter()
    actions = Counter()
    action_outcomes = defaultdict(Counter)

    risk_denials = 0

    for record in records:
        outcome = normalize_outcome(record)
        reason = normalize_reason(record)
        action = normalize_action(record)

        outcomes[outcome] += 1
        reasons[reason] += 1
        actions[action] += 1
        action_outcomes[action][outcome] += 1

        if outcome == "REJECTED":
            risk_denials += 1

    percentages = {}
    if total > 0:
        for outcome, count in outcomes.items():
            percentages[outcome] = round((count / total) * 100, 2)

    return {
        "total_transactions": total,
        "outcomes": dict(outcomes),
        "outcome_percentages": percentages,
        "risk_denials": risk_denials,
        "top_rejection_reasons": reasons.most_common(10),
        "actions": dict(actions),
        "action_outcomes": {
            action: dict(counter) for action, counter in action_outcomes.items()
        },
    }


def print_report(summary):
    print("=" * 60)
    print("GOVERNANCE ANALYTICS REPORT")
    print("=" * 60)
    print(f"Total Transactions Processed: {summary['total_transactions']}")
    print(f"Outcomes: {summary['outcomes']}")
    print(f"Outcome Percentages: {summary['outcome_percentages']}")
    print(f"Risk Denials: {summary['risk_denials']}")
    print()

    print("Top Rejection Reasons:")
    if summary["top_rejection_reasons"]:
        for reason, count in summary["top_rejection_reasons"]:
            print(f"  - {reason}: {count}")
    else:
        print("  - None")

    print()
    print("Actions:")
    for action, count in summary["actions"].items():
        print(f"  - {action}: {count}")

    print()
    print("Action Outcomes:")
    for action, outcomes in summary["action_outcomes"].items():
        print(f"  - {action}: {outcomes}")

    print("=" * 60)


def export_json(summary, output_file):
    path = Path(output_file)
    with path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def export_csv(summary, output_file):
    path = Path(output_file)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["section", "key", "value"])

        writer.writerow(["summary", "total_transactions", summary["total_transactions"]])
        writer.writerow(["summary", "risk_denials", summary["risk_denials"]])

        for outcome, count in summary["outcomes"].items():
            writer.writerow(["outcomes", outcome, count])

        for outcome, pct in summary["outcome_percentages"].items():
            writer.writerow(["outcome_percentages", outcome, pct])

        for reason, count in summary["top_rejection_reasons"]:
            writer.writerow(["top_rejection_reasons", reason, count])

        for action, count in summary["actions"].items():
            writer.writerow(["actions", action, count])

        for action, outcomes in summary["action_outcomes"].items():
            writer.writerow(["action_outcomes", action, json.dumps(outcomes, ensure_ascii=False)])


def main():
    log_file = DEFAULT_LOG_FILE
    json_output = None
    csv_output = None

    args = sys.argv[1:]

    i = 0
    while i < len(args):
        arg = args[i]

        if arg == "--log" and i + 1 < len(args):
            log_file = args[i + 1]
            i += 2
        elif arg == "--json-out" and i + 1 < len(args):
            json_output = args[i + 1]
            i += 2
        elif arg == "--csv-out" and i + 1 < len(args):
            csv_output = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Unknown or incomplete argument: {arg}")

    records = load_records(log_file)
    summary = summarize_records(records)
    print_report(summary)

    if json_output:
        export_json(summary, json_output)
        print(f"[OK] JSON report written to: {json_output}")

    if csv_output:
        export_csv(summary, csv_output)
        print(f"[OK] CSV report written to: {csv_output}")


if __name__ == "__main__":
    main()
