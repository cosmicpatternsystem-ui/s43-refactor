from pathlib import Path
import re
import sys

p = Path("s43.py")
src = p.read_text(encoding="utf-8")

anchor = '        try:\n            qty2 = float(qty)\n'
if anchor not in src:
    print("[ERR] anchor not found")
    sys.exit(1)

insert = '''        try:
            self._logger.info(
                "event=PRE_ORDER_TRACE wallet=%s sym=%s side=%s qty=%.12f px=%.12f notional=%.2f dry_run=%s max_retries=%s",
                self._wallet,
                sym,
                side,
                float(qty),
                float(price),
                float(notional_irt),
                bool(getattr(self.cfg, "dry_run", False)),
                getattr(self, "max_retries", None),
            )
        except Exception:
            pass

        try:
            qty2 = float(qty)
'''

src2 = src.replace(anchor, insert, 1)

if src2 == src:
    print("[ERR] patch made no changes")
    sys.exit(1)

bak = Path("s43.py.bak_patch01")
bak.write_text(src, encoding="utf-8")
p.write_text(src2, encoding="utf-8")
print("[OK] patch applied: PRE_ORDER_TRACE")
print("[OK] backup:", bak)
