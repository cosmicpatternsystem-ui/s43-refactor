from pathlib import Path

p = Path("s43.py")
lines = p.read_text(encoding="utf-8").splitlines()

start = None
end = None

for i, line in enumerate(lines):
    if line.strip() == "class _DashRingHandler(logging.Handler):":
        start = i
        break

if start is None:
    raise SystemExit("ERROR: class _DashRingHandler not found")

for j in range(start + 1, min(len(lines), start + 120)):
    if line := lines[j].strip():
        if line.startswith("def _parse_age("):
            end = j
            break

if end is None:
    raise SystemExit("ERROR: def _parse_age boundary not found")

replacement = [
    "class _DashRingHandler(logging.Handler):",
    "    def __init__(self, maxlen: int = 400):",
    "        super().__init__(level=logging.INFO)",
    "        from collections import deque as _s43_deque",
    "        self.records = _s43_deque(maxlen=maxlen)",
    "        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))",
    "",
    "    def emit(self, record):",
    "        try:",
    "            msg = self.format(record)",
    "        except Exception:",
    "            try:",
    "                msg = record.getMessage()",
    "            except Exception:",
    "                msg = str(record)",
    "        try:",
    "            self.records.append(msg)",
    "        except Exception:",
    "            pass",
    "",
    "    def tail(self, n: int = 100):",
    "        try:",
    "            n = int(n)",
    "        except Exception:",
    "            n = 100",
    "        try:",
    "            return list(self.records)[-max(0, n):]",
    "        except Exception:",
    "            return []",
    "",
    "",
    "# === S43_INTERNAL_NAMEERROR_FALLBACKS ===",
    "S43_FALLBACK_MODE = False",
    "",
    "try:",
    "    TradingHalt",
    "except NameError:",
    "    class TradingHalt(RuntimeError):",
    "        pass",
    "",
    "try:",
    "    TemporaryPause",
    "except NameError:",
    "    class TemporaryPause(RuntimeError):",
    "        pass",
    "",
    "",
    "def _parisa_embedded_code_bytes() -> bytes:",
    "    import base64 as _base64",
    "    import zlib as _zlib",
    "    return _zlib.decompress(_base64.b64decode(PARISA_B64_ZLIB))",
    "",
    "",
    "def _extract_parisa_to_file(out_path: str) -> str:",
    "    try:",
    "        from pathlib import Path",
    "    except Exception as e:",
    "        raise SystemExit(f'pathlib missing: {e}')",
    "",
    "    data = _parisa_embedded_code_bytes()",
    "    p = Path(out_path).expanduser()",
    "    try:",
    "        p = p.resolve()",
    "    except Exception:",
    "        p = Path(os.path.abspath(str(p)))",
    "",
    "    p.parent.mkdir(parents=True, exist_ok=True)",
    "    p.write_bytes(data)",
    "    return str(p)",
    "",
    "",
]

lines[start:end] = replacement
p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"patched _DashRingHandler/fallback/parisa block: lines {start+1}..{end}")
