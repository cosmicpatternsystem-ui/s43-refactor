from pathlib import Path

p = Path("s43.py")
lines = p.read_text(encoding="utf-8").splitlines()

start = 5   # line 6
end   = 29  # line 30

replacement = [
    '# -*- coding: utf-8 -*-',
    'from __future__ import annotations',
    '',
    'if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):',
    '    print("### S43_RUNTIME_PROBE_ACTIVE ###")',
    '',
    'import socket',
    '',
    'class TemporaryPause(Exception):',
    '    def __init__(self, message="", pause_sec=None):',
    '        super().__init__(message)',
    '        self.pause_sec = pause_sec',
    '',
    'class ApiError(Exception):',
    '    pass',
    '',
    'class ApiHttpError(ApiError):',
    '    def __init__(self, message="", status=None, body=None, headers=None, code=None, payload=None, response=None, **kwargs):',
    '        super().__init__(message)',
    '        self.status = status',
    '        self.body = body',
    '        self.headers = headers',
    '        self.code = code',
    '        self.payload = payload',
    '        self.response = response',
    '        self.extra = dict(kwargs) if kwargs else {}',
    '',
    '',
]

lines[start:end+1] = replacement
p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("patched header")
