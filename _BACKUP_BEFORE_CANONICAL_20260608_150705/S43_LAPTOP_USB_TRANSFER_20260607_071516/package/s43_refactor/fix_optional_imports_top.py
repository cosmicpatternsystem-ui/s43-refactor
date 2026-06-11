from pathlib import Path

p = Path("s43.py")
lines = p.read_text(encoding="utf-8").splitlines()

start = None
for i, line in enumerate(lines):
    if line.strip() == "from typing import Any, Dict, List, Optional, Tuple, Union, Callable":
        start = i + 1
        break

if start is None:
    raise SystemExit("ERROR: typing import boundary not found")

end = None
for j in range(start, min(len(lines), start + 80)):
    if line := lines[j].strip():
        if line == "# === PHASE54 AUDIT HELPER START ===":
            end = j
            break

if end is None:
    raise SystemExit("ERROR: PHASE54 AUDIT HELPER START marker not found")

replacement = [
    "",
    "try:",
    "    import requests",
    "except Exception:",
    "    requests = None",
    "",
    "try:",
    "    import aiohttp",
    "except Exception:",
    "    aiohttp = None",
    "",
    "try:",
    "    import telebot",
    "except Exception:",
    "    telebot = None",
    "",
    "try:",
    "    from telebot import types",
    "except Exception:",
    "    types = None",
    "",
    "try:",
    "    from telegram import Update",
    "except Exception:",
    "    Update = None",
    "",
    "try:",
    "    from telegram.ext import (",
    "        Application,",
    "        ApplicationBuilder,",
    "        CommandHandler,",
    "        MessageHandler,",
    "        CallbackQueryHandler,",
    "        ContextTypes,",
    "        filters,",
    "    )",
    "except Exception:",
    "    Application = None",
    "    ApplicationBuilder = None",
    "    CommandHandler = None",
    "    MessageHandler = None",
    "    CallbackQueryHandler = None",
    "    ContextTypes = None",
    "    filters = None",
    "",
]

lines[start:end] = replacement

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"patched optional imports block: replaced lines {start+1}..{end}")
