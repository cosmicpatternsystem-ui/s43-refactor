from pathlib import Path
import shutil, time

p = Path("s43.py")
bak = Path(f"s43.py.bak_fix_literal_newline_separators_again_{int(time.time())}")
shutil.copy2(p, bak)

raw = p.read_text(encoding="utf-8", errors="replace")

# If the file has become one/few physical lines with many literal \n separators,
# convert them back to real newlines.
literal_count = raw.count("\\n")
physical_lines = raw.count("\n") + 1

print(f"before: physical_lines={physical_lines} literal_backslash_n={literal_count}")

if literal_count < 100:
    raise SystemExit("ERROR: file does not look globally literal-\\n corrupted; refusing broad replace")

raw2 = raw.replace("\\n", "\n")

p.write_text(raw2, encoding="utf-8")

print(f"restored newlines; backup={bak}")
print(f"after: physical_lines={raw2.count(chr(10)) + 1} literal_backslash_n={raw2.count(chr(92) + 'n')}")
