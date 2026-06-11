#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "[1/7] locating repo root..."
if [ ! -f "s43.py" ]; then
  echo "ERROR: s43.py not found in current directory"
  echo "cd into your repo root and run again."
  exit 1
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR=".phase7_backup_$STAMP"
mkdir -p "$BACKUP_DIR"

echo "[2/7] backing up candidate files..."
for f in run_hardening_tests.py \
         test_phase7a_status_smoke.py \
         test_phase7b_signal_anchor_smoke.py
do
  [ -f "$f" ] && cp -f "$f" "$BACKUP_DIR"/
done

echo "[3/7] creating test_phase7a_status_smoke.py ..."
cat > test_phase7a_status_smoke.py <<'PY'
import unittest
from pathlib import Path


class TestPhase7AStatusSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = Path("s43.py").read_text(encoding="utf-8", errors="ignore")

    def test_has_refresh_balance_anchor(self):
        self.assertIn(
            "async def _refresh_balance_if_needed(self, w: WalletRuntime) -> float:",
            self.src,
        )

    def test_has_status_once_anchor(self):
        self.assertIn(
            "async def _status_once() -> None:",
            self.src,
        )

    def test_status_related_tokens_exist(self):
        # smoke-level only; no production behavior change
        tokens = [
            "_refresh_balance_if_needed",
            "_status_once",
        ]
        for token in tokens:
            with self.subTest(token=token):
                self.assertIn(token, self.src)


if __name__ == "__main__":
    unittest.main()
PY

echo "[4/7] creating test_phase7b_signal_anchor_smoke.py ..."
cat > test_phase7b_signal_anchor_smoke.py <<'PY'
import unittest
from pathlib import Path


class TestPhase7BSignalAnchorSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = Path("s43.py").read_text(encoding="utf-8", errors="ignore")

    def test_has_signal_class_anchor(self):
        self.assertIn("class Signal:", self.src)

    def test_has_signal_evaluate_anchor(self):
        self.assertIn(
            "def evaluate(self, symbol: str, book: OrderBookTop) -> Signal:",
            self.src,
        )

    def test_has_veto_anchor(self):
        self.assertIn("if float(delta) <= float(veto_thr):", self.src)
        self.assertIn('meta["veto"] = True', self.src)

    def test_has_risk_and_phoenix_anchors(self):
        anchors = [
            "class RiskDecision:",
            "class RiskEscalationLayer:",
            "class PhoenixDecision:",
            "class PhoenixEngine:",
        ]
        for anchor in anchors:
            with self.subTest(anchor=anchor):
                self.assertIn(anchor, self.src)


if __name__ == "__main__":
    unittest.main()
PY

echo "[5/7] patching run_hardening_tests.py if present ..."
if [ -f "run_hardening_tests.py" ]; then
python - <<'PY'
from pathlib import Path
p = Path("run_hardening_tests.py")
src = p.read_text(encoding="utf-8", errors="ignore")

targets = [
    "test_phase7a_status_smoke.py",
    "test_phase7b_signal_anchor_smoke.py",
]

original = src

# Strategy:
# If file already mentions target, do nothing.
# Else, try to append to a TEST_FILES style list if present.
# Else, append a harmless marker comment so manual follow-up is easy.

for t in targets:
    if t in src:
        continue

# common patterns
patterns = [
    "TEST_FILES = [",
    "tests = [",
    "ALLOWLIST = [",
    "allowlist = [",
]

patched = False
for pat in patterns:
    idx = src.find(pat)
    if idx != -1:
        insert_pos = src.find("]", idx)
        if insert_pos != -1:
            block = src[idx:insert_pos]
            for t in targets:
                if t not in block:
                    src = src[:insert_pos] + f'    "{t}",\n' + src[insert_pos:]
                    insert_pos = src.find("]", idx)
            patched = True
            break

if not patched:
    marker = "\n# PHASE7_APPEND_NOTE: add these tests to your runner allowlist if needed:\n"
    for t in targets:
        if t not in src:
            marker += f"#   - {t}\n"
    if "PHASE7_APPEND_NOTE" not in src:
        src += marker

if src != original:
    p.write_text(src, encoding="utf-8")
PY
  echo "run_hardening_tests.py patched safely."
else
  echo "run_hardening_tests.py not found; skipped."
fi

echo "[6/7] running tests ..."
python -m unittest -v \
  test_phase7a_status_smoke.py \
  test_phase7b_signal_anchor_smoke.py

echo "[7/7] done."
echo "Backup dir: $BACKUP_DIR"
