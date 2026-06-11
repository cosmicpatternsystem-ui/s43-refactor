from pathlib import Path

p = Path("s43.py")
lines = p.read_text(encoding="utf-8").splitlines()

start = None
for i, line in enumerate(lines):
    if line.strip() == "# ### SAFE_CALLHANDLERS_GUARD_V1 ###":
        start = i
        break

if start is None:
    raise SystemExit("ERROR: SAFE_CALLHANDLERS_GUARD_V1 marker not found")

end = None
for j in range(start + 1, min(len(lines), start + 120)):
    if lines[j].startswith("from pathlib import Path"):
        end = j
        break

if end is None:
    raise SystemExit("ERROR: boundary 'from pathlib import Path' not found after SAFE_CALLHANDLERS block")

replacement = [
    "# ### SAFE_CALLHANDLERS_GUARD_V1 ###",
    "# Prevent broken handlers (whose emit is still logging.Handler.emit)",
    "# from crashing all logging with:",
    "#   NotImplementedError: emit must be implemented by Handler subclasses",
    'if not getattr(logging, "_s43_safe_callhandlers_guard_v1", False):',
    '    logging._s43_safe_callhandlers_guard_v1 = True',
    '    _s43_orig_callHandlers = logging.Logger.callHandlers',
    '',
    '    def _s43_safe_callHandlers(self, record):',
    '        c = self',
    '        found = 0',
    '        while c:',
    '            for hdlr in list(getattr(c, "handlers", [])):',
    '                found += 1',
    '                try:',
    '                    if record.levelno < hdlr.level:',
    '                        continue',
    '                    try:',
    '                        if type(hdlr).emit is logging.Handler.emit:',
    '                            continue',
    '                    except Exception:',
    '                        continue',
    '                    hdlr.handle(record)',
    '                except NotImplementedError:',
    '                    continue',
    '                except Exception:',
    '                    continue',
    '',
    '            if not c.propagate:',
    '                c = None',
    '            else:',
    '                c = c.parent',
    '',
    '        if found == 0:',
    '            try:',
    '                if logging.lastResort and record.levelno >= logging.lastResort.level:',
    '                    logging.lastResort.handle(record)',
    '            except Exception:',
    '                pass',
    '',
    '    logging.Logger.callHandlers = _s43_safe_callHandlers',
    '',
    'import traceback',
    'import subprocess',
    'import threading',
    'import sqlite3',
    'import hashlib',
    'import hmac',
    'import base64',
    'import html',
    'import urllib.parse',
]

lines[start:end] = replacement

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"patched SAFE_CALLHANDLERS block: replaced lines {start+1}..{end}")
