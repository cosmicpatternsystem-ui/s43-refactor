from pathlib import Path
from datetime import datetime
import shutil
import sys

p = Path("s43_LATEST.py")
if not p.exists():
    print("ERROR: s43_LATEST.py not found in current directory")
    sys.exit(1)

src = p.read_text(encoding="utf-8", errors="ignore")

old_detect = '''    def _arzplus_detect_403_cause(
        self,
        endpoint: str,
        headers: Dict[str, str],
        raw_body: str
    ) -> str:
        """Heuristic root-cause for ArzPlus 403 (permission scope / IP-WAF block / clock skew)."""
        try:
            # Detect clock drift (Date header vs local)
            st, drift = self._clock_drift_from_headers(headers)
            if abs(drift) > 30.0:
                return f"CLOCK_SKEW_DRIFT_{int(drift)}s"
            
            # Detect WAF/IP block
            if "Cloudflare" in str(headers.get("Server", "")):
                return "WAF_BLOCK_CLOUDFLARE"
            
            # Check token structure
            if not self._token:
                return "MISSING_TOKEN"
            
            return "UNKNOWN_SCOPE_PERMISSION"
        except Exception as e:
            return f"DIAG_FAIL:{type(e).__name__}"'''

new_detect = '''    def _arzplus_detect_403_cause(
        self,
        endpoint: str,
        headers: Dict[str, str],
        raw_body: str
    ) -> str:
        """Heuristic root-cause for ArzPlus 403 (permission scope / IP-WAF block / clock skew)."""
        try:
            # Detect clock drift (Date header vs local)
            st, drift = self._clock_drift_from_headers(headers)
            if abs(drift) > 30.0:
                return f"CLOCK_SKEW_DRIFT_{int(drift)}s"

            # Detect WAF/IP block
            server_h = str(headers.get("Server", "") or "")
            if "Cloudflare" in server_h:
                return "WAF_BLOCK_CLOUDFLARE"

            # Check token presence and rough shape without exposing token
            tok = getattr(self, "_token", None)
            tok_s = str(tok or "")
            if not tok_s:
                return "MISSING_TOKEN"

            if len(tok_s) < 16:
                return f"TOKEN_TOO_SHORT_len_{len(tok_s)}"

            if tok_s.lower().startswith("bearer "):
                return "TOKEN_FIELD_CONTAINS_BEARER_PREFIX"

            body_l = str(raw_body or "").lower()
            if "token" in body_l and "invalid" in body_l:
                return "SERVER_SAYS_TOKEN_INVALID"
            if "permission" in body_l or "scope" in body_l:
                return "UNKNOWN_SCOPE_PERMISSION"
            if "ip" in body_l and ("block" in body_l or "forbidden" in body_l):
                return "POSSIBLE_IP_BLOCK"

            return "UNKNOWN_SCOPE_PERMISSION"
        except Exception as e:
            return f"DIAG_FAIL:{type(e).__name__}"'''

old_log = '''    def _arzplus_log_403(
        self,
        ep: str,
        method: str,
        st: int,
        raw: str,
        rh: Dict[str, str]
    ) -> None:
        """Emit the required 403 diagnostic log line (throttled per endpoint)."""
        try:
            now = float(time.time())
            last = float((self._last_403_log_ts_by_ep or {}).get(ep, 0.0) or 0.0)
            if (now - last) < 20.0:
                return
            self._last_403_log_ts_by_ep[ep] = now
            body_snip = self._sanitize_body_for_debug(raw, limit=300)
            cause = self._arzplus_detect_403_cause(ep, rh, raw)
            self._logger.error(
                "event=ARZPLUS_HTTP_403 exchange=arzplus endpoint=%s method=%s http_status=%s body=%s headers=%s auth_fp=%s cause=%s",
                ep, method, st, body_snip, str(rh)[:100], "HIDDEN", cause
            )
        except Exception:
            pass'''

new_log = '''    def _arzplus_log_403(
        self,
        ep: str,
        method: str,
        st: int,
        raw: str,
        rh: Dict[str, str]
    ) -> None:
        """Emit the required 403 diagnostic log line (throttled per endpoint)."""
        try:
            now = float(time.time())
            last = float((self._last_403_log_ts_by_ep or {}).get(ep, 0.0) or 0.0)
            if (now - last) < 20.0:
                return
            self._last_403_log_ts_by_ep[ep] = now
            body_snip = self._sanitize_body_for_debug(raw, limit=300)
            cause = self._arzplus_detect_403_cause(ep, rh, raw)

            tok = getattr(self, "_token", None)
            tok_s = str(tok or "")
            tok_len = len(tok_s)
            tok_shape = "empty"
            if tok_s:
                if tok_s.lower().startswith("bearer "):
                    tok_shape = "bearer-prefixed"
                elif "." in tok_s and len(tok_s.split(".")) >= 3:
                    tok_shape = "jwt-like"
                elif tok_len >= 32:
                    tok_shape = "opaque-long"
                else:
                    tok_shape = "opaque-short"

            server_h = str((rh or {}).get("Server", "") or "")[:80]
            date_h = str((rh or {}).get("Date", "") or "")[:80]

            self._logger.error(
                "event=ARZPLUS_HTTP_403 exchange=arzplus endpoint=%s method=%s http_status=%s body=%s server=%s date=%s auth_fp=%s token_len=%s token_shape=%s cause=%s",
                ep, method, st, body_snip, server_h, date_h, "HIDDEN", tok_len, tok_shape, cause
            )
        except Exception:
            pass'''

old_auth = '''            _s43_debug_print(f"[AUTHDBG_HEADER] present={bool(auth_value)} scheme={str(auth_value).split()[0] if str(auth_value).split() else ''} len={len(str(auth_value))}")
            headers["Authorization"] = auth_value'''

new_auth = '''            _auth_s = str(auth_value or "")
            _auth_parts = _auth_s.split()
            _auth_scheme = _auth_parts[0] if _auth_parts else ""
            _auth_len = len(_auth_s)
            _auth_shape = "empty"
            if _auth_s:
                if _auth_s.lower().startswith("bearer bearer "):
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
            )
            headers["Authorization"] = auth_value'''

needles = [
    ("_arzplus_detect_403_cause", old_detect),
    ("_arzplus_log_403", old_log),
    ("AUTHDBG_HEADER", old_auth),
]

for name, block in needles:
    if block not in src:
        print(f"ERROR: expected block not found for {name}")
        sys.exit(2)

patched = src.replace(old_detect, new_detect, 1)
patched = patched.replace(old_log, new_log, 1)
patched = patched.replace(old_auth, new_auth, 1)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = p.with_name(f"s43_LATEST_before_auth_trace_{ts}.py")
shutil.copy2(p, backup)
p.write_text(patched, encoding="utf-8")

print(f"OK: patched {p.name}")
print(f"BACKUP: {backup.name}")
