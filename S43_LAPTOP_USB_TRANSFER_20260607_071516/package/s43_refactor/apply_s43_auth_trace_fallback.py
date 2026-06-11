from pathlib import Path
from datetime import datetime
import shutil
import sys

target = Path("s43.py")
if not target.exists():
    print("ERROR: s43.py not found")
    sys.exit(1)

src = target.read_text(encoding="utf-8", errors="ignore")

def replace_between(src, start_marker, end_marker, new_block, name):
    a = src.find(start_marker)
    if a == -1:
        print(f"ERROR: start marker not found for {name}")
        sys.exit(2)
    b = src.find(end_marker, a)
    if b == -1:
        print(f"ERROR: end marker not found for {name}")
        sys.exit(3)
    return src[:a] + new_block + src[b:]

# --- patch _arzplus_detect_403_cause ---
start_detect = "    def _arzplus_detect_403_cause("
end_detect = "\n    def _arzplus_log_403("

new_detect = '''    def _arzplus_detect_403_cause(
        self,
        endpoint: str,
        headers: Dict[str, str],
        raw_body: str
    ) -> str:
        """Heuristic root-cause for ArzPlus 403 (permission/scope/IP-WAF/clock/token-shape)."""
        try:
            st, drift = self._clock_drift_from_headers(headers)
            if abs(float(drift)) > 2.0:
                return f"clock_skew drift_s={drift:.3f}"

            hdrs = headers or {}
            server_h = str(hdrs.get("Server", "") or "")
            body_l = str(raw_body or "").lower()

            if "cloudflare" in server_h.lower():
                return "ip_waf_block cloudflare"
            if "forbidden" in body_l and "ip" in body_l:
                return "ip_waf_block body_forbidden_ip"
            if "access denied" in body_l or "request blocked" in body_l:
                return "ip_waf_block generic"

            tok = getattr(self, "_token", None)
            tok_s = str(tok or "")
            if not tok_s:
                return "missing_token"
            if tok_s.lower().startswith("bearer "):
                return "token_field_contains_bearer_prefix"
            if len(tok_s) < 16:
                return f"token_too_short len={len(tok_s)}"

            ep_l = str(endpoint or "").lower()
            if "balance" in ep_l:
                return "permission_scope_balance"

            if "token" in body_l and "invalid" in body_l:
                return "server_says_token_invalid"
            if "scope" in body_l or "permission" in body_l:
                return "permission_scope_unknown"

            return "unknown"
        except Exception as e:
            return f"diag_fail:{type(e).__name__}"'''

# --- patch _arzplus_log_403 ---
start_log = "    def _arzplus_log_403("
end_log = "\n    def "

new_log = '''    def _arzplus_log_403(
        self,
        ep: str,
        method: str,
        st: int,
        raw: str,
        resp_headers: Dict[str, str]
    ) -> None:
        """Emit ArzPlus 403 diagnostic log line (throttled per endpoint)."""
        try:
            if not self._is_arzplus():
                return
            now = float(time.time())
            last = float((self._last_403_log_ts_by_ep or {}).get(ep, 0.0) or 0.0)
            if (now - last) < 20.0:
                return
            self._last_403_log_ts_by_ep[ep] = now

            body_snip = self._sanitize_body_for_debug(raw, limit=300)
            rh = resp_headers or {}
            cause = self._arzplus_detect_403_cause(ep, rh, raw)

            tok = getattr(self, "_token", None)
            tok_s = str(tok or "")
            tok_len = len(tok_s)
            if not tok_s:
                tok_shape = "empty"
            elif tok_s.lower().startswith("bearer "):
                tok_shape = "bearer-prefixed"
            elif "." in tok_s and len(tok_s.split(".")) >= 3:
                tok_shape = "jwt-like"
            elif tok_len >= 32:
                tok_shape = "opaque-long"
            else:
                tok_shape = "opaque-short"

            waf_hdrs = self._waf_headers_subset(rh)
            server_h = str(rh.get("Server", "") or "")[:80]
            date_h = str(rh.get("Date", "") or "")[:80]

            self._logger.error(
                "event=ARZPLUS_HTTP_403 exchange=arzplus endpoint=%s method=%s http_status=%s body=%s server=%s date=%s waf_headers=%s auth_fp=%s token_len=%s token_shape=%s cause=%s",
                ep, method, st, body_snip, server_h, date_h, waf_hdrs, "HIDDEN", tok_len, tok_shape, cause
            )
        except Exception:
            pass
'''

patched = replace_between(src, start_detect, end_detect, new_detect, "_arzplus_detect_403_cause")
patched = replace_between(patched, start_log, end_log, new_log, "_arzplus_log_403")

old_auth_line = '_s43_debug_print(f"[AUTHDBG_HEADER] present={bool(auth_value)} scheme={str(auth_value).split()[0] if str(auth_value).split() else \'\'} len={len(str(auth_value))}")'

new_auth_block = '''_auth_s = str(auth_value or "")
                _auth_parts = _auth_s.split()
                _auth_scheme = _auth_parts[0] if _auth_parts else ""
                _auth_len = len(_auth_s)
                if not _auth_s:
                    _auth_shape = "empty"
                elif _auth_s.lower().startswith("bearer bearer "):
                    _auth_shape = "DOUBLE_BEARER_PREFIX"
                elif _auth_s.lower().startswith("bearer "):
                    _auth_shape = "bearer-header"
                elif "." in _auth_s and len(_auth_s.split(".")) >= 3:
                    _auth_shape = "jwt-like-without-scheme"
                elif _auth_len >= 32:
                    _auth_shape = "opaque-long-without-scheme"
                else:
                    _auth_shape = "opaque-short-without-scheme"
                _s43_debug_print(
                    f"[AUTHDBG_HEADER] present={bool(_auth_s)} scheme={_auth_scheme} len={_auth_len} shape={_auth_shape}"
                )'''

if old_auth_line not in patched:
    print("ERROR: AUTHDBG_HEADER line not found")
    sys.exit(4)

patched = patched.replace(old_auth_line, new_auth_block, 1)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = target.with_name(f"s43_before_fallback_auth_trace_{ts}.py")
shutil.copy2(target, backup)
target.write_text(patched, encoding="utf-8")

print(f"OK: fallback patched {target.name}")
print(f"BACKUP: {backup.name}")
