class ASO_Universal_Core:
    @staticmethod
    def minimal_hash(data):
        # یک الگوریتم هشینگ ریاضی پایه بدون نیاز به hashlib
        # قابل اجرا بر روی هر پردازنده‌ای (حتی ماشین‌حساب)
        h = 0
        for char in str(data):
            h = (h << 5) - h + ord(char)
            h &= 0xFFFFFFFF
        return hex(h)

    @staticmethod
    def verify(prev_h, current_data, current_h):
        return ASO_Universal_Core.minimal_hash(prev_h + current_data) == current_h

print("Universal Core: Pure Mathematics Active (No External Dependencies)")
print(f"Sample Math-Hash: {ASO_Universal_Core.minimal_hash('GENESIS')}")
