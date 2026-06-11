from pathlib import Path

p = Path("s43.py")
lines = p.read_text(encoding="utf-8").splitlines()

# 1) Remove stray duplicated top-level-indented self.extra before _parse_hard_veto_sources_env
parse_idx = None
for i, line in enumerate(lines):
    if line.startswith("def _parse_hard_veto_sources_env("):
        parse_idx = i
        break

if parse_idx is None:
    raise SystemExit("ERROR: _parse_hard_veto_sources_env not found")

new_lines = []
for i, line in enumerate(lines):
    # remove only suspicious duplicate before the parse function
    if i < parse_idx and line == "        self.extra = dict(kwargs) if kwargs else {}":
        # keep the first valid one inside ApiHttpError, drop later duplicate(s)
        prev_same = any(x == line for x in new_lines)
        if prev_same:
            continue
    new_lines.append(line)

lines = new_lines

# 2) Rewrite _s43_debug_print_enabled and _s43_debug_print block up to SAFE_CALLHANDLERS marker
start = None
for i, line in enumerate(lines):
    if line.startswith("def _s43_debug_print_enabled("):
        start = i
        break

if start is None:
    raise SystemExit("ERROR: def _s43_debug_print_enabled not found")

end = None
for j in range(start + 1, min(len(lines), start + 80)):
    if lines[j].startswith("# ### SAFE_CALLHANDLERS_GUARD_V1 ###"):
        end = j
        break

if end is None:
    raise SystemExit("ERROR: SAFE_CALLHANDLERS marker not found after debug funcs")

replacement = [
    "def _s43_debug_print_enabled() -> bool:",
    "    try:",
    "        import os as _s43_os",
    '        return str(_s43_os.getenv("S43_DEBUG_PRINTS", "")).strip().lower() in (',
    '            "1", "true", "yes", "on", "debug"',
    "        )",
    "    except Exception:",
    "        return False",
    "",
    "def _s43_debug_print(*args, **kwargs):",
    "    if _s43_debug_print_enabled():",
    "        print(*args, **kwargs)",
    "",
    "",
]

lines[start:end] = replacement

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("patched top debug funcs and removed stray duplicate self.extra")
