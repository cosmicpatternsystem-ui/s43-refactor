#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "== S43 Full Persian Scanner / Cleaner Patch =="

if [ ! -f "s43.py" ]; then
  echo "ERROR: s43.py not found. Run this from project root."
  exit 1
fi

TS="$(date +%Y%m%d_%H%M%S)"
TOOL="s43_full_persian_cleaner.py"

cat > "$TOOL" <<'PY'
#!/usr/bin/env python3
import ast
import csv
import io
import re
import sys
import time
import tokenize
from pathlib import Path

TARGET = Path("s43.py")
PERSIAN_RE = re.compile(r"[\u0600-\u06FF]")

def now_ts():
    return time.strftime("%Y%m%d_%H%M%S")

def read_text():
    return TARGET.read_text(encoding="utf-8")

def write_text(text):
    TARGET.write_text(text, encoding="utf-8")

def collect_docstring_spans(text):
    spans = set()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return spans

    def add_doc_node(node):
        body = getattr(node, "body", None)
        if not body:
            return
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(getattr(first, "value", None), ast.Constant)
            and isinstance(first.value.value, str)
        ):
            start = getattr(first, "lineno", None)
            end = getattr(first, "end_lineno", start)
            if start and end:
                for line_no in range(start, end + 1):
                    spans.add(line_no)

    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.Module,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            add_doc_node(node)

    return spans

def collect_token_hits(text):
    hits = []
    doc_lines = collect_docstring_spans(text)

    reader = io.BytesIO(text.encode("utf-8")).readline
    try:
        tokens = tokenize.tokenize(reader)
        for tok in tokens:
            if tok.type not in (tokenize.COMMENT, tokenize.STRING):
                continue
            token_text = tok.string
            if not PERSIAN_RE.search(token_text):
                continue

            line_no = tok.start[0]
            category = "docstring" if line_no in doc_lines and tok.type == tokenize.STRING else (
                "comment" if tok.type == tokenize.COMMENT else "string"
            )

            hits.append({
                "line": line_no,
                "category": category,
                "text": token_text.replace("\t", "\\t").replace("\n", "\\n"),
            })
    except tokenize.TokenError:
        pass

    return hits

def collect_raw_hits(text, token_hits):
    token_lines = {h["line"] for h in token_hits}
    hits = []
    for idx, line in enumerate(text.splitlines(), 1):
        if idx in token_lines:
            continue
        if PERSIAN_RE.search(line):
            hits.append({
                "line": idx,
                "category": "raw_line",
                "text": line.rstrip("\n").replace("\t", "\\t"),
            })
    return hits

def scan():
    text = read_text()
    token_hits = collect_token_hits(text)
    raw_hits = collect_raw_hits(text, token_hits)
    hits = sorted(token_hits + raw_hits, key=lambda x: (x["line"], x["category"]))

    ts = now_ts()
    report = Path(f"s43_persian_full_report_{ts}.tsv")
    repl = Path(f"s43_persian_replacements_{ts}.tsv")

    with report.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["line", "category", "text"])
        for h in hits:
            writer.writerow([h["line"], h["category"], h["text"]])

    with repl.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["line", "category", "old_text", "new_text"])
        for h in hits:
            writer.writerow([h["line"], h["category"], h["text"], ""])

    counts = {}
    for h in hits:
        counts[h["category"]] = counts.get(h["category"], 0) + 1

    print("SCAN COMPLETE")
    print(f"Total Persian hits: {len(hits)}")
    for key in sorted(counts):
        print(f"{key}: {counts[key]}")
    print(f"Report: {report}")
    print(f"Replacement template: {repl}")

    if hits:
        print("")
        print("First 40 hits:")
        for h in hits[:40]:
            short = h["text"]
            if len(short) > 160:
                short = short[:157] + "..."
            print(f"{h['line']}\t{h['category']}\t{short}")

def apply_replacements(path):
    repl_path = Path(path)
    if not repl_path.exists():
        print(f"ERROR: replacement file not found: {repl_path}")
        sys.exit(1)

    text = read_text()
    lines = text.splitlines(keepends=True)

    rows = []
    with repl_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        required = {"line", "category", "old_text", "new_text"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            print("ERROR: invalid replacement TSV header.")
            print("Expected: line<TAB>category<TAB>old_text<TAB>new_text")
            sys.exit(1)

        for row in reader:
            new_text = row.get("new_text", "")
            if new_text == "":
                continue
            try:
                line_no = int(row["line"])
            except ValueError:
                continue
            rows.append((line_no, row["old_text"], new_text))

    if not rows:
        print("No replacements with non-empty new_text found. Nothing applied.")
        return

    backup = Path(f"s43.py.before_full_persian_clean_{now_ts()}")
    backup.write_text(text, encoding="utf-8")

    applied = 0
    failed = []

    for line_no, old_text, new_text in rows:
        if line_no < 1 or line_no > len(lines):
            failed.append((line_no, "line out of range"))
            continue

        old = old_text.replace("\\t", "\t").replace("\\n", "\n")
        new = new_text.replace("\\t", "\t").replace("\\n", "\n")

        original_line = lines[line_no - 1]
        if old not in original_line:
            failed.append((line_no, "old_text not found on line"))
            continue

        lines[line_no - 1] = original_line.replace(old, new, 1)
        applied += 1

    new_full_text = "".join(lines)

    try:
        ast.parse(new_full_text)
    except SyntaxError as exc:
        print("ERROR: replacements would break Python syntax.")
        print(f"SyntaxError: {exc}")
        print(f"Backup preserved: {backup}")
        sys.exit(1)

    write_text(new_full_text)

    print("APPLY COMPLETE")
    print(f"Backup: {backup}")
    print(f"Applied replacements: {applied}")

    if failed:
        print(f"Failed replacements: {len(failed)}")
        for line_no, reason in failed[:30]:
            print(f"{line_no}: {reason}")

    remaining = PERSIAN_RE.findall(new_full_text)
    if remaining:
        print(f"WARNING: Persian characters still remain: {len(remaining)}")
    else:
        print("OK: no Persian characters remain in s43.py")

def main():
    if len(sys.argv) == 1 or sys.argv[1] == "--scan":
        scan()
        return

    if sys.argv[1] == "--apply":
        if len(sys.argv) != 3:
            print("Usage: python s43_full_persian_cleaner.py --apply replacements.tsv")
            sys.exit(1)
        apply_replacements(sys.argv[2])
        return

    print("Usage:")
    print("  python s43_full_persian_cleaner.py --scan")
    print("  python s43_full_persian_cleaner.py --apply replacements.tsv")
    sys.exit(1)

if __name__ == "__main__":
    main()
PY

chmod +x "$TOOL"

echo "[1/4] Compile check before scan..."
python -m py_compile s43.py
echo "OK: s43.py compile passed"

echo "[2/4] Running full Persian scan..."
python "$TOOL" --scan

echo "[3/4] Writing quick grep report..."
grep -nP "[\x{0600}-\x{06FF}]" s43.py > "s43_persian_grep_${TS}.txt" || true

echo "[4/4] Done."
echo ""
echo "Next step:"
echo "1. Open the newest s43_persian_replacements_*.tsv"
echo "2. Fill only the new_text column for items you want to replace"
echo "3. Apply with:"
echo "   python s43_full_persian_cleaner.py --apply s43_persian_replacements_YYYYMMDD_HHMMSS.tsv"
echo "4. Verify with:"
echo "   python -m py_compile s43.py"
echo "   grep -nP \"[\\x{0600}-\\x{06FF}]\" s43.py"
