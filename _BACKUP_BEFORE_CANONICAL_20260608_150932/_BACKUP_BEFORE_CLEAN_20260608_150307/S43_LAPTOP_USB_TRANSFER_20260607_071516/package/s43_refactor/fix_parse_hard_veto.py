from pathlib import Path

p = Path("s43.py")
lines = p.read_text(encoding="utf-8").splitlines()

def_line = None
for i, line in enumerate(lines):
    if line.startswith("def _parse_hard_veto_sources_env("):
        def_line = i
        break

if def_line is None:
    raise SystemExit("ERROR: def _parse_hard_veto_sources_env not found")

end = None
for j in range(def_line + 1, min(len(lines), def_line + 80)):
    if lines[j].startswith("import os"):
        end = j
        break

if end is None:
    raise SystemExit("ERROR: import os after _parse_hard_veto_sources_env not found")

replacement = [
    "def _parse_hard_veto_sources_env(default_sources=None):",
    '    """',
    "    Fail-safe fallback for _parse_hard_veto_sources_env.",
    "    Returns safe default values to prevent dashboard crash.",
    '    """',
    "    hard_sources = default_sources if default_sources is not None else []",
    "    hard_sources_env_set = False",
    "    hard_all_sources = list(hard_sources)",
    "    strict_unknown_hard = False",
    "    return hard_sources, hard_sources_env_set, hard_all_sources, strict_unknown_hard",
    "",
    "",
]

lines[def_line:end] = replacement

p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"patched _parse_hard_veto_sources_env at old lines {def_line+1}..{end}")
