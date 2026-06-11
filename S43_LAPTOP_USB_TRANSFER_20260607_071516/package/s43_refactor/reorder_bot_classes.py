from pathlib import Path

TARGET = Path("s43.py")
lines = TARGET.read_text(encoding="utf-8").splitlines()

base_start, base_end = -1, -1
ops_start, ops_end = -1, -1
bot_start = -1

# پیدا کردن محدوده‌ها
for i, line in enumerate(lines):
    if line.startswith("class TradingBotBase"):
        base_start = i
    elif line.startswith("class TradingBotOps"):
        ops_start = i
    elif line.startswith("class TradingBot(") or line.startswith("class TradingBot:"):
        if bot_start == -1: bot_start = i

# پیدا کردن پایان کلاس‌ها (تقریبی با شروع کلاس بعدی)
base_end = ops_start
ops_end = bot_start if bot_start > ops_start else len(lines)

if base_start != -1 and bot_start != -1 and base_start > bot_start:
    print(f"[!] Reordering detected: Base at {base_start}, Bot at {bot_start}")
    
    # جدا سازی بخش‌ها
    header = lines[:bot_start]
    bot_class_part = lines[bot_start:base_start]
    base_class_part = lines[base_start:ops_start]
    ops_class_part = lines[ops_start:bot_start if bot_start > ops_start else len(lines)] 
    
    # بازسازی هوشمند: اول Base و Ops، بعد Bot
    # برای سادگی و اطمینان، کلاس‌های پایه را به قبل از اولین استفاده (Bot) می‌بریم
    new_content = lines[:bot_start] + lines[base_start:ops_start] + lines[ops_start:bot_start if bot_start > ops_start else len(lines)]
    
    # حذف کلاس‌های جابجا شده از جای قبلی‌شان در صورت لزوم (بسیار حساس)
    # اما روش امن‌تر: فقط بلاک Bot را پیدا کرده و Base/Ops را دقیقاً قبل از آن تزریق می‌کنیم.
    
    # روش نهایی امن:
    final_lines = []
    base_ops_block = lines[base_start:] # تمام محتوای کلاس‌های پایه تا انتهای فایل
    
    # ساخت فایل جدید: هدر + کلاس‌های پایه + کلاس بات
    # با فرض اینکه بعد از Bot دیگر تعریفی نیست که Bot به آن نیاز داشته باشد
    # ما ریسک نمی‌کنیم و فقط کلاس‌های پایه را به خط ۱۰۰ (بعد از ایمپورت‌ها) منتقل می‌کنیم.
    
    pre_bot = lines[:100]
    the_rest = lines[100:]
    # حذف تعاریف قبلی از the_rest برای جلوگیری از تکرار
    clean_rest = [l for i, l in enumerate(the_rest) if not (i+100 >= base_start)]
    
    content = pre_bot + lines[base_start:] + clean_rest
    # این منطق در فایل‌های بسیار بزرگ ممکن است خطا دهد. 
    # ساده‌ترین راه: جابجایی بلاک TradingBotBase به خط ۱۱۰
    
    base_ops = lines[base_start:]
    original_top = lines[:base_start]
    
    # تزریق کلاس‌های پایه در خط ۱۱۰
    refined = original_top[:110] + lines[base_start:] + original_top[110:]
    TARGET.write_text("\n".join(refined), encoding="utf-8")
    print("[OK] Base classes moved to the top.")
else:
    print("[SKIP] Order seems fine or classes not found.")
