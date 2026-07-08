from pathlib import Path
import re

p = Path("s43.py")
text = p.read_text(encoding="utf-8", errors="replace")
orig = text

text = re.sub(
    r'_env_bool\("AUTONOMOUS_AI"\s*,\s*True\)',
    '_env_bool("AUTONOMOUS_AI", False)',
    text
)

text = re.sub(
    r'_env_bool\("DZH_AI_RESCUES"\s*,\s*True\)',
    '_env_bool("DZH_AI_RESCUES", False)',
    text
)

text = re.sub(
    r'_env_bool\("DZH_AI_RESCUES_ARMED"\s*,\s*_env_bool\("ARZPLUS_LIVE_ARMED"\s*,\s*False\)\)',
    '_env_bool("DZH_AI_RESCUES_ARMED", _env_bool("AI_LIVE_TRADING_ARMED", _env_bool("ARZPLUS_LIVE_ARMED", False)))',
    text
)

insert_block = """
    # Future-proof runtime / AI controls
    ai_mode: str = field(default_factory=lambda: str(os.getenv("AI_MODE", "off")).strip().lower())
    runtime_profile: str = field(default_factory=lambda: str(os.getenv("RUNTIME_PROFILE", ("termux" if _env_bool("TERMUX_MODE", False) else "server"))).strip().lower())
    live_trading_armed: bool = field(default_factory=lambda: _env_bool("LIVE_TRADING_ARMED", _env_bool("ARZPLUS_LIVE_ARMED", False)))
    ai_live_trading_armed: bool = field(default_factory=lambda: _env_bool("AI_LIVE_TRADING_ARMED", False))
"""

if "ai_mode:" not in text and "runtime_profile:" not in text:
    m = re.search(r'(dzh_ai_rescues\s*:\s*bool\s*=\s*field\(default_factory=.*?\)\n)', text, re.S)
    if not m:
        m = re.search(r'(autonomous_ai\s*:\s*bool\s*=\s*field\(default_factory=.*?\)\n)', text, re.S)
    if m:
        text = text[:m.end()] + insert_block + text[m.end():]

if "def _ai_runtime_enabled(" not in text:
    helper = '''

def _ai_runtime_enabled(cfg) -> bool:
    try:
        ai_mode = str(getattr(cfg, "ai_mode", os.getenv("AI_MODE", "off")) or "off").strip().lower()
    except Exception:
        ai_mode = "off"
    if ai_mode in ("", "0", "false", "none", "off", "disabled"):
        return False
    return bool(getattr(cfg, "autonomous_ai", _env_bool("AUTONOMOUS_AI", False)))

def _live_trading_armed(cfg) -> bool:
    return bool(getattr(cfg, "live_trading_armed", _env_bool("LIVE_TRADING_ARMED", _env_bool("ARZPLUS_LIVE_ARMED", False))))

def _ai_live_trading_armed(cfg) -> bool:
    return bool(getattr(cfg, "ai_live_trading_armed", _env_bool("AI_LIVE_TRADING_ARMED", False)))
'''
    m = re.search(r'\nif\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:', text)
    if m:
        text = text[:m.start()] + helper + text[m.start():]
    else:
        text += helper

if text == orig:
    print("NO_TEXT_CHANGE")
else:
    p.write_text(text, encoding="utf-8")
    print("PATCH_APPLIED")
