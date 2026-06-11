import sys
from pathlib import Path
import py_compile

TARGET = Path("s43.py")
content = TARGET.read_text(encoding="utf-8")

# الگوهای جدید برای پیدا کردن نقاط تزریق در فایل تمیز شده
# 1. بخش Balance
bal_anchor = "bal = await self.client.get_balance()"
# 2. بخش Market Snapshot
mkt_anchor = "self.public.get_market_snapshot()"

if bal_anchor not in content:
    print("ERROR: Balance anchor not found. File structure might be different.")
    sys.exit(1)

print("Found anchors. Applying guards...")

# تزریق گارد Balance
bal_guard = """
        # SAFETY_BALANCE_GUARD
        if bal is None:
            bal = 0.0
        elif not isinstance(bal, (int, float, dict, list, tuple)):
            try:
                bal = float(bal)
            except:
                bal = 0.0
"""
content = content.replace(bal_anchor, bal_anchor + bal_guard)

# تزریق گارد Market (بسیار مهم برای جلوگیری از خطای Nonetype)
mkt_repair = """stats_map = await asyncio.wait_for(self.public.get_market_snapshot(), timeout=20)
                # SAFETY_MARKET_GUARD
                if not isinstance(stats_map, dict) or not stats_map:
                    stats_map = {}
"""
# جایگزینی با احتیاط (فرض بر این است که کد اصلی مشابه متد wait_for است)
if "stats_map = await asyncio.wait_for(self.public.get_market_snapshot()" in content:
    content = content.replace("stats_map = await asyncio.wait_for(self.public.get_market_snapshot(), timeout=20)", mkt_repair)
elif "stats_map = await self.public.get_market_snapshot()" in content:
    content = content.replace("stats_map = await self.public.get_market_snapshot()", "stats_map = await self.public.get_market_snapshot()\n                if not isinstance(stats_map, dict): stats_map = {}")

TARGET.write_text(content, encoding="utf-8")

# تست نهایی
try:
    py_compile.compile("s43.py", doraise=True)
    print("SUCCESS: Guards injected and file is valid!")
except Exception as e:
    print(f"CRITICAL ERROR: Injection broke the file: {e}")
