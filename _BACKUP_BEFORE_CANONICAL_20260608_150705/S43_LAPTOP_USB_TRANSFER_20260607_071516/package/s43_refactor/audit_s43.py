import re
from pathlib import Path

TARGET = "s43.py"

patterns = {
    "ORDER_ENTRYPOINT": r"\bplace_order\s*\(",
    "ORDER_IMPL": r"_place_order_impl\s*\(",
    "EXECUTOR_DISPATCH": r'getattr\s*\(.*place_order',
    "CREATE_ORDER": r"\bcreate_order\s*\(",
    "SUBMIT_ORDER": r"\bsubmit_order\s*\(",
    "SEND_ORDER": r"\bsend_order\s*\(",
    "HTTP_CLIENTS": r"\b(requests|httpx|aiohttp)\b",
    "WEBSOCKET": r"\b(websocket|ws://|wss://)\b",
    "API_KEYS": r"(api[_-]?key|secret|Authorization|X-API)",
    "ENV_FLAGS": r"(DRY_RUN|LIVE_TRADING_ARMED|AI_LIVE_TRADING_ARMED|ALLOW_ORDERS|REAL)",
    "EXCHANGE_CLASSES": r"(ExchangeClient|_FaultInjectExchange)",
}

def scan():
    text = Path(TARGET).read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    results = {}

    for name, pattern in patterns.items():
        rx = re.compile(pattern, re.IGNORECASE)
        matches = []

        for i, line in enumerate(lines, 1):
            if rx.search(line):
                matches.append((i, line.strip()))

        results[name] = matches

    return results


def print_report(results):
    print()
    print("S43 SECURITY AUDIT REPORT")
    print("=" * 40)

    for section, matches in results.items():
        print()
        print("[" + section + "]")

        if not matches:
            print("  none")
            continue

        for line_no, content in matches[:20]:
            print(f"  line {line_no}: {content}")

        if len(matches) > 20:
            print(f"  ... {len(matches)-20} more")


if __name__ == "__main__":
    results = scan()
    print_report(results)
