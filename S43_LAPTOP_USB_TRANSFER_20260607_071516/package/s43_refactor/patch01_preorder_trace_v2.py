from pathlib import Path
import sys

p = Path("s43.py")
src = p.read_text(encoding="utf-8")

anchor = '                        resp = await self._ex.place_order(sym, side, float(qty2), float(px2), cid=cid, **order_kwargs)\n'
if anchor not in src:
    print("[ERR] anchor not found")
    sys.exit(1)

insert = '''                        try:
                            self._logger.info(
                                "event=PRE_ORDER_TRACE wallet=%s sym=%s side=%s qty=%.12f px=%.12f notional=%.2f dry_run=%s reduce_only=%s attempt=%s cid=%s",
                                self._wallet,
                                sym,
                                str(side).lower(),
                                float(qty2),
                                float(px2),
                                float(notional_irt),
                                bool(getattr(self.cfg, "dry_run", False)),
                                order_kwargs.get("reduce_only"),
                                attempt,
                                cid,
                            )
                        except Exception:
                            pass
                        resp = await self._ex.place_order(sym, side, float(qty2), float(px2), cid=cid, **order_kwargs)
'''

src2 = src.replace(anchor, insert, 1)

if src2 == src:
    print("[ERR] patch made no changes")
    sys.exit(1)

bak = Path("s43.py.bak_patch01_v2")
bak.write_text(src, encoding="utf-8")
p.write_text(src2, encoding="utf-8")

print("[OK] patch applied: PRE_ORDER_TRACE_V2")
print("[OK] backup:", bak)
