class TradingPolicy:
    """Single source of truth for execution permissions by health state.

    """
    def __init__(self, bot: Any):
        self.bot = bot
    def health_state(self) -> str:
        try:
            st = str(getattr(self.bot, "_hw_state", "INIT") or "INIT").upper()
        except Exception:
            st = "INIT"
        if st == "LIVE":
            st = "OK"
        if st not in ("INIT", "OK", "DEGRADED", "CRITICAL", "HALTED"):
            st = "DEGRADED"
        return st
    def allow(self, action: str) -> Tuple[bool, str]:
        a = str(action or "").upper().strip()
        st_full = self.health_state()
        try:
            st_exec = str(getattr(self.bot, "_hw_want_exec", "") or "").upper().strip()
        except Exception:
            st_exec = ""
        st = st_exec if st_exec in ("INIT", "OK", "DEGRADED", "CRITICAL", "HALTED") else st_full
        try:
            if bool(getattr(self.bot, "_engine_halted", False)):
                if a in ("EXIT", "REDUCE", "MANAGE"):
                    return True, f"ALLOW_{a}_HALTED"
                return False, "DENY_ENGINE_HALTED"
        except Exception:
            pass
        if st == "INIT":
            if a in ("EXIT", "REDUCE", "MANAGE"):
                return True, f"ALLOW_{a}_INIT"
            return False, "DENY_INIT_NO_ENTRY"
        if st == "OK":
            return True, "ALLOW_OK"
        if st == "DEGRADED":
            if a == "ENTRY":
                try:
                    if bool(_env_bool("TERMUX_MODE", False)) and bool(_env_bool("TERMUX_ALLOW_ENTRY_DEGRADED", True)):
                        return True, "ALLOW_ENTRY_DEGRADED_TERMUX"
                except Exception:
                    pass
                return False, "DENY_DEGRADED_NO_ENTRY"
            return True, f"ALLOW_{a}_DEGRADED"
        if st == "CRITICAL":
            if a == "ENTRY":
                return False, "DENY_CRITICAL_NO_ENTRY"
            if a in ("EXIT", "REDUCE", "MANAGE"):
                return True, f"ALLOW_{a}_CRITICAL"
            return False, "DENY_CRITICAL_ONLY_EXIT_REDUCE"
        if a in ("EXIT", "REDUCE", "MANAGE"):
            return True, f"ALLOW_{a}_HALTED"
        return False, "DENY_HALTED"