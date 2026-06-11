import sys

def repair():
    lines = open("s43.py", "r", encoding="utf-8").readlines()
    
    # نگه داشتن هدر و گارد امنیتی ابتدایی (تا خط ۵۶)
    header = lines[:56]
    
    # بقیه فایل را از جایی که کد واقعی کلاس‌ها شروع می‌شود پیدا می‌کنیم
    # معمولا کلاس اصلی با 'class ' شروع می‌شود. 
    # طبق بررسی قبلی، بدنه اصلی فایل بعد از این پچ‌های خراب است.
    
    start_index = -1
    for i, line in enumerate(lines):
        if i < 110: continue # پریدن از بخش خراب
        if line.startswith("class ") or line.startswith("import ") or line.startswith("def "):
            if "_parse_wallet_balance_response_v2" not in line: # رد کردن پچ خراب
                start_index = i
                break
    
    if start_index == -1:
        print("Could not find a safe recovery point.")
        return

    # ساخت فایل جدید سالم
    new_content = "".join(header) + "\n\n" + "".join(lines[start_index:])
    
    with open("s43.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Repaired! Removed corrupted block. Recovery point: line {start_index}")

if __name__ == "__main__":
    repair()
