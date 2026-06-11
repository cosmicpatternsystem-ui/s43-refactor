import re
from pathlib import Path

FILE = "s43.py"

text = Path(FILE).read_text(errors="ignore")

checks = {

    "place_order": r"\bplace_order\s*\(",
    "_place_order_impl": r"_place_order_impl\s*\(",
    "execute_order": r"execute_order",
    "create_order": r"create_order",
    "submit_order": r"submit_order",
    "send_order": r"send_order",

    "getattr_order": r"getattr\(.*order",
    "callable_order": r"callable\(.*order",

    "asyncio_create_task": r"asyncio\.create_task",
    "ensure_future": r"asyncio\.ensure_future",
    "thread_executor": r"ThreadPoolExecutor",
    "run_in_executor": r"run_in_executor",

    "requests": r"\brequests\b",
    "aiohttp": r"\baiohttp\b",
    "httpx": r"\bhttpx\b",
    "websocket": r"ws://|wss://|websocket",

    "authorization_header": r"Authorization",
    "api_key": r"api[_\-]?key",
    "api_secret": r"api[_\-]?secret",
    "token": r"token",

    "exchange_client": r"class\s+ExchangeClient",
    "fault_inject_exchange": r"_FaultInjectExchange",

    "DRY_RUN": r"DRY_RUN",
    "LIVE_TRADING_ARMED": r"LIVE_TRADING_ARMED",
    "AI_LIVE_TRADING_ARMED": r"AI_LIVE_TRADING_ARMED",
    "ALLOW_ORDERS": r"ALLOW_ORDERS",
    "REAL_FLAG": r"--real",

    "eval": r"\beval\(",
    "exec": r"\bexec\(",
    "subprocess": r"\bsubprocess\b",
    "shell": r"shell=True",
}

print("\\nS43 DEEP SECURITY AUDIT")
print("="*45)

for name, pattern in checks.items():
    matches = re.findall(pattern, text, re.IGNORECASE)
    print(f"{name:25} -> {len(matches)}")

print("\\nInterpretation:")
print("Order functions present ≠ execution possible")
print("Runtime patches determine real safety")
print("="*45)
