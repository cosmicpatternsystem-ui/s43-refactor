import json
import sys
from pathlib import Path
from collections import Counter


DEFAULT_LOG_FILE = "governance_audit.log"
DEFAULT_JSON_OUT = "governance_log_inspection.json"
DEFAULT_TEXT_OUT = "governance_log_inspection.txt"


def safe_preview(value, max_len=500):
    text = str(value)
    if len(text) > max_len:
        return text[:max_len] + "...<truncated>"
    return text


def classify_record(record):
    if not isinstance(record, dict):
        return {
            "shape": type(record).__name__,
            "has_outcome_like_key": False,
            "has_action_like_key": False,
            "has_reason_like_key": False,
            "keys": [],
        }

    keys = list(record.keys())
    lowered = {str(k).lower() for k in keys}

    outcome_keys = {"outcome", "decision", "status", "result"}
    action_keys = {"action", "event", "type", "operation"}
    reason_keys = {"reason", "denial_reason", "message", "error"}

    details = record.get("details")
    details_keys = []
    if isinstance(details, dict):
        details_keys = list(details.keys())
        lowered_details = {str(k).lower() for k in details_keys}
    else:
        lowered_details = set()

    return {
        "shape": "dict",
        "keys": keys,
        "details_keys": details_keys,
        "has_outcome_like_key": bool(lowered & outcome_keys),
        "has_action_like_key": bool(lowered & action_keys),
        "has_reason_like_key": bool((lowered & reason_keys) or (lowered_details & reason_keys)),
    }


def inspect_log_file(log_file):
    path = Path(log_file)

    result = {
        "log_file": str(path),
        "exists": path.exists(),
        "file_size_bytes": None,
        "total_lines": 0,
        "empty_lines": 0,
        "valid_json_lines": 0,
        "invalid_json_lines": 0,
        "json_shapes": {},
        "top_level_keys": {},
        "outcome_like_key_presence": 0,
        "action_like_key_presence": 0,
        "reason_like_key_presence": 0,
        "sample_valid_records": [],
        "sample_invalid_lines": [],
        "recommendations": [],
    }

    if not path.exists():
        result["recommendations"].append(
            "governance_audit.log was not found. Run governance integration tests or execute a scenario that writes audit events."
        )
        return result

    result["file_size_bytes"] = path.stat().st_size

    shape_counter = Counter()
    key_counter = Counter()

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line_no, raw_line in enumerate(f, start=1):
            result["total_lines"] += 1
            stripped = raw_line.strip()

            if not stripped:
                result["empty_lines"] += 1
                continue

            try:
                record = json.loads(stripped)
                result["valid_json_lines"] += 1

                cls = classify_record(record)
                shape_counter[cls["shape"]] += 1

                for key in cls.get("keys", []):
                    key_counter[str(key)] += 1

                if cls["has_outcome_like_key"]:
                    result["outcome_like_key_presence"] += 1
                if cls["has_action_like_key"]:
                    result["action_like_key_presence"] += 1
                if cls["has_reason_like_key"]:
                    result["reason_like_key_presence"] += 1

                if len(result["sample_valid_records"]) < 5:
                    result["sample_valid_records"].append(
                        {
                            "line": line_no,
                            "record_preview": record,
                            "classification": cls,
                        }
                    )

            except json.JSONDecodeError as exc:
                result["invalid_json_lines"] += 1
                if len(result["sample_invalid_lines"]) < 10:
                    result["sample_invalid_lines"].append(
                        {
                            "line": line_no,
                            "error": str(exc),
                            "raw_preview": safe_preview(stripped, 500),
                        }
                    )

    result["json_shapes"] = dict(shape_counter)
    result["top_level_keys"] = dict(key_counter.most_common(50))

    if result["total_lines"] == 0:
        result["recommendations"].append(
            "The log file exists but is empty. Generate governance audit events before running analytics."
        )

    if result["valid_json_lines"] == 0 and result["invalid_json_lines"] > 0:
        result["recommendations"].append(
            "No valid JSON lines were detected. The reporter expects JSON Lines format: one valid JSON object per line."
        )

    if result["valid_json_lines"] > 0 and result["outcome_like_key_presence"] == 0:
        result["recommendations"].append(
            "Valid JSON exists, but no outcome-like key was found. Reporter looks for one of: outcome, decision, status, result."
        )

    if result["valid_json_lines"] > 0 and result["action_like_key_presence"] == 0:
        result["recommendations"].append(
            "Valid JSON exists, but no action-like key was found. Reporter looks for one of: action, event, type, operation."
        )

    if result["valid_json_lines"] > 0 and result["reason_like_key_presence"] == 0:
        result["recommendations"].append(
            "Valid JSON exists, but no reason-like key was found. Reporter looks for one of: reason, denial_reason, message, error, including inside details."
        )

    if result["valid_json_lines"] > 0 and result["invalid_json_lines"] > 0:
        result["recommendations"].append(
            "Mixed valid and invalid lines detected. Consider cleaning malformed audit entries or making the reporter more tolerant."
        )

    if not result["recommendations"]:
        result["recommendations"].append(
            "Log format looks usable for analytics. If reporter still shows zero transactions, verify that it is reading the same log file path."
        )

    return result


def write_json_report(result, output_file):
    path = Path(output_file)
    with path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


def write_text_report(result, output_file):
    path = Path(output_file)
    lines = []

    lines.append("=" * 70)
    lines.append("GOVERNANCE AUDIT LOG INSPECTION REPORT")
    lines.append("=" * 70)
    lines.append(f"Log File: {result['log_file']}")
    lines.append(f"Exists: {result['exists']}")
    lines.append(f"File Size Bytes: {result['file_size_bytes']}")
    lines.append(f"Total Lines: {result['total_lines']}")
    lines.append(f"Empty Lines: {result['empty_lines']}")
    lines.append(f"Valid JSON Lines: {result['valid_json_lines']}")
    lines.append(f"Invalid JSON Lines: {result['invalid_json_lines']}")
    lines.append("")
    lines.append("JSON Shapes:")
    if result["json_shapes"]:
        for key, value in result["json_shapes"].items():
            lines.append(f"  - {key}: {value}")
    else:
        lines.append("  - None")

    lines.append("")
    lines.append("Top-Level Keys:")
    if result["top_level_keys"]:
        for key, value in result["top_level_keys"].items():
            lines.append(f"  - {key}: {value}")
    else:
        lines.append("  - None")

    lines.append("")
    lines.append("Key Presence:")
    lines.append(f"  - Outcome-like keys: {result['outcome_like_key_presence']}")
    lines.append(f"  - Action-like keys: {result['action_like_key_presence']}")
    lines.append(f"  - Reason-like keys: {result['reason_like_key_presence']}")

    lines.append("")
    lines.append("Sample Valid Records:")
    if result["sample_valid_records"]:
        for item in result["sample_valid_records"]:
            lines.append(f"  - Line {item['line']}: {safe_preview(item['record_preview'], 1000)}")
            lines.append(f"    Classification: {item['classification']}")
    else:
        lines.append("  - None")

    lines.append("")
    lines.append("Sample Invalid Lines:")
    if result["sample_invalid_lines"]:
        for item in result["sample_invalid_lines"]:
            lines.append(f"  - Line {item['line']}: {item['error']}")
            lines.append(f"    Raw: {item['raw_preview']}")
    else:
        lines.append("  - None")

    lines.append("")
    lines.append("Recommendations:")
    for rec in result["recommendations"]:
        lines.append(f"  - {rec}")

    lines.append("=" * 70)

    with path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def print_console_report(result):
    print("=" * 70)
    print("GOVERNANCE AUDIT LOG INSPECTION REPORT")
    print("=" * 70)
    print(f"Log File: {result['log_file']}")
    print(f"Exists: {result['exists']}")
    print(f"File Size Bytes: {result['file_size_bytes']}")
    print(f"Total Lines: {result['total_lines']}")
    print(f"Empty Lines: {result['empty_lines']}")
    print(f"Valid JSON Lines: {result['valid_json_lines']}")
    print(f"Invalid JSON Lines: {result['invalid_json_lines']}")
    print(f"JSON Shapes: {result['json_shapes']}")
    print(f"Top-Level Keys: {result['top_level_keys']}")
    print(f"Outcome-like Key Presence: {result['outcome_like_key_presence']}")
    print(f"Action-like Key Presence: {result['action_like_key_presence']}")
    print(f"Reason-like Key Presence: {result['reason_like_key_presence']}")
    print()
    print("Recommendations:")
    for rec in result["recommendations"]:
        print(f"  - {rec}")

    if result["sample_valid_records"]:
        print()
        print("Sample Valid Records:")
        for item in result["sample_valid_records"]:
            print(f"  - Line {item['line']}: {safe_preview(item['record_preview'], 700)}")

    if result["sample_invalid_lines"]:
        print()
        print("Sample Invalid Lines:")
        for item in result["sample_invalid_lines"]:
            print(f"  - Line {item['line']}: {item['error']}")
            print(f"    Raw: {item['raw_preview']}")

    print("=" * 70)


def parse_args(argv):
    log_file = DEFAULT_LOG_FILE
    json_out = DEFAULT_JSON_OUT
    text_out = DEFAULT_TEXT_OUT

    i = 0
    while i < len(argv):
        arg = argv[i]

        if arg == "--log" and i + 1 < len(argv):
            log_file = argv[i + 1]
            i += 2
        elif arg == "--json-out" and i + 1 < len(argv):
            json_out = argv[i + 1]
            i += 2
        elif arg == "--text-out" and i + 1 < len(argv):
            text_out = argv[i + 1]
            i += 2
        else:
            raise ValueError(f"Unknown or incomplete argument: {arg}")

    return log_file, json_out, text_out


def main():
    log_file, json_out, text_out = parse_args(sys.argv[1:])
    result = inspect_log_file(log_file)
    print_console_report(result)
    write_json_report(result, json_out)
    write_text_report(result, text_out)
    print(f"[OK] JSON inspection report written to: {json_out}")
    print(f"[OK] Text inspection report written to: {text_out}")


if __name__ == "__main__":
    main()
