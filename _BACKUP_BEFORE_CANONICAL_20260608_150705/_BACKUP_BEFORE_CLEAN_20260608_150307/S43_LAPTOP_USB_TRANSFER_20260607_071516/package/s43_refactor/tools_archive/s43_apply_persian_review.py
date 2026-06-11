#!/usr/bin/env python3
import csv
import shutil
import datetime

TARGET = "s43.py"
TSV = "s43_persian_review.tsv"

with open(TARGET, "r", encoding="utf-8") as f:
    lines = f.readlines()

patches = []
with open(TSV, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        if row["apply"].strip().upper() == "YES":
            patches.append(row)

print("Selected patches:", len(patches))

backup = TARGET + ".before_persian_cleanup_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(TARGET, backup)
print("Backup created:", backup)

for p in sorted(patches, key=lambda x: int(x["line"]), reverse=True):
    line = int(p["line"]) - 1
    repl = p["replacement_english"]

    if p["kind"] == "comment":
        lines[line] = repl + "\n"

    elif p["kind"] == "docstring":
        start = int(p["line"]) - 1
        end = int(p["end_line"]) - 1
        new = ['    """\n']
        for l in repl.split("\\n"):
            new.append("    " + l + "\n")
        new.append('    """\n')
        lines[start:end+1] = new

with open(TARGET, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("Persian cleanup patches applied successfully.")
