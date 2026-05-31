#!/usr/bin/env python3
import os
import sys
import importlib

EXPECTED_FILLED_SLOTS = {1, 3}
EXPECTED_EMPTY_SLOTS = {2}

SLOT_ENV_KEYS = {
    1: [
        "ARZPLUS_WALLET_1_TOKEN",
        "ARZPLUS_TOKEN_1",
        "TOKEN_1",
        "ACCESS_TOKEN_1",
        "API_TOKEN_1",
    ],
    2: [
        "ARZPLUS_WALLET_2_TOKEN",
        "ARZPLUS_TOKEN_2",
        "TOKEN_2",
        "ACCESS_TOKEN_2",
        "API_TOKEN_2",
    ],
    3: [
        "ARZPLUS_WALLET_3_TOKEN",
        "ARZPLUS_TOKEN_3",
        "TOKEN_3",
        "ACCESS_TOKEN_3",
        "API_TOKEN_3",
    ],
}

DANGEROUS_GENERIC_KEYS = [
    "ARZPLUS_TOKEN",
    "ARZ_PLUS_TOKEN",
    "ARZ_TOKEN",
    "TOKEN",
    "API_TOKEN",
    "ACCESS_TOKEN",
]

PLACEHOLDER_VALUES = {
    "",
    "token",
    "bearer",
    "token ",
    "bearer ",
    "none",
    "null",
    "undefined",
    "changeme",
    "your_token",
    "your-token",
    "paste_token_here",
    "paste-token-here",
}


def clean(v):
    if v is None:
        return ""
    return str(v).strip()


def is_placeholder(v):
    v = clean(v)
    if not v:
        return True

    low = v.lower().strip()

    if low in PLACEHOLDER_VALUES:
        return True

    if low.startswith("token ") and len(v.strip()) <= 10:
        return True

    if low.startswith("bearer ") and len(v.strip()) <= 12:
        return True

    if "<" in v and ">" in v:
        return True

    return False


def mask(v):
    v = clean(v)
    if not v:
        return "EMPTY"

    if len(v) <= 12:
        return f"SET len={len(v)} value={repr(v)}"

    return f"SET len={len(v)} head={v[:8]} tail={v[-4:]}"


def env_value(key):
    return clean(os.getenv(key))


def print_section(title):
    print("")
    print("=" * 70)
    print(title)
    print("=" * 70)


def fail(msg):
    print(f"ERROR: {msg}")
    return False


def warn(msg):
    print(f"WARNING: {msg}")


def ok_msg(msg):
    print(f"OK: {msg}")


def main():
    all_ok = True

    print_section("1) Import check")

    try:
        s43 = importlib.import_module("s43")
        ok_msg("s43 imported successfully")
    except Exception as e:
        print(f"ERROR: failed to import s43: {type(e).__name__}: {e}")
        sys.exit(1)

    if not hasattr(s43, "get_arzplus_token"):
        print("ERROR: s43.get_arzplus_token does not exist")
        sys.exit(1)

    ok_msg("get_arzplus_token exists")

    print_section("2) Environment strict check")

    for slot in (1, 2, 3):
        print(f"\nslot {slot} env keys:")
        for key in SLOT_ENV_KEYS[slot]:
            v = env_value(key)
            print(f"  {key}: {mask(v)}")

            if v and is_placeholder(v):
                all_ok = fail(f"{key} looks like a placeholder/broken token: {repr(v)}")

    print("\nGeneric/fallback env keys:")
    for key in DANGEROUS_GENERIC_KEYS:
        v = env_value(key)
        print(f"  {key}: {mask(v)}")

        if v:
            all_ok = fail(
                f"{key} is set. For strict wallet isolation, generic token variables must be empty."
            )

        if v and is_placeholder(v):
            all_ok = fail(f"{key} looks like a placeholder/broken token: {repr(v)}")

    print_section("3) Slot 2 must be completely empty")

    for key in SLOT_ENV_KEYS[2]:
        v = env_value(key)
        if v:
            all_ok = fail(f"slot 2 key must be empty but is SET: {key} -> {mask(v)}")
        else:
            ok_msg(f"{key} is empty")

    print_section("4) Resolver behavior check")

    resolved = {}

    for slot in (1, 2, 3):
        try:
            tok = clean(s43.get_arzplus_token(slot))
        except Exception as e:
            all_ok = fail(f"get_arzplus_token({slot}) raised {type(e).__name__}: {e}")
            tok = ""

        resolved[slot] = tok
        print(f"slot={slot} resolver={mask(tok)}")

        if tok and is_placeholder(tok):
            all_ok = fail(f"resolver returned placeholder/broken token for slot {slot}: {repr(tok)}")

    print_section("5) Expected mapping check")

    for slot in EXPECTED_FILLED_SLOTS:
        if not resolved.get(slot):
            all_ok = fail(f"slot {slot} must be SET but resolver returned EMPTY")
        else:
            ok_msg(f"slot {slot} is SET")

    for slot in EXPECTED_EMPTY_SLOTS:
        if resolved.get(slot):
            all_ok = fail(f"slot {slot} must be EMPTY but resolver returned: {mask(resolved[slot])}")
        else:
            ok_msg(f"slot {slot} is EMPTY")

    print_section("6) Cross-slot isolation check")

    t1 = resolved.get(1, "")
    t2 = resolved.get(2, "")
    t3 = resolved.get(3, "")

    if t1 and t3 and t1 == t3:
        all_ok = fail("slot 1 and slot 3 tokens are identical. They must be independent.")
    elif t1 and t3:
        ok_msg("slot 1 and slot 3 are different")

    if t2 and (t2 == t1 or t2 == t3):
        all_ok = fail("slot 2 is leaking/copying token from another slot")
    else:
        ok_msg("slot 2 is not leaking another slot token")

    print_section("7) Preferred naming check")

    w1 = env_value("ARZPLUS_WALLET_1_TOKEN")
    w3 = env_value("ARZPLUS_WALLET_3_TOKEN")

    if not w1:
        all_ok = fail("ARZPLUS_WALLET_1_TOKEN should be SET")
    else:
        ok_msg("ARZPLUS_WALLET_1_TOKEN is SET")

    if not w3:
        all_ok = fail("ARZPLUS_WALLET_3_TOKEN should be SET")
    else:
        ok_msg("ARZPLUS_WALLET_3_TOKEN is SET")

    if env_value("ARZPLUS_TOKEN_3"):
        warn("ARZPLUS_TOKEN_3 is SET. It is not fatal, but cleaner setup is to keep only ARZPLUS_WALLET_3_TOKEN.")

    if env_value("ARZPLUS_TOKEN_1"):
        warn("ARZPLUS_TOKEN_1 is SET. It is not fatal, but cleaner setup is to keep only ARZPLUS_WALLET_1_TOKEN.")

    print_section("FINAL RESULT")

    if all_ok:
        print("PASS: Strict ArzPlus token isolation is correct.")
        print("")
        print("Expected final state:")
        print("  slot 1 -> SET")
        print("  slot 2 -> EMPTY")
        print("  slot 3 -> SET")
        sys.exit(0)

    print("FAIL: Strict ArzPlus token isolation has problems. See ERROR lines above.")
    sys.exit(1)


if __name__ == "__main__":
    main()
