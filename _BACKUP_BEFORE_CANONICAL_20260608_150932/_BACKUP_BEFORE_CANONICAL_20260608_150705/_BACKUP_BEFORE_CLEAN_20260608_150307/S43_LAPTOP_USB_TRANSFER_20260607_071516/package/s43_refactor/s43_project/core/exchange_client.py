from .priority import Priority
from .logger import Logger
from .clock_arbiter import ClockArbiter
from .api_http_error import ApiHttpError
from .shared_async_rate_limiter import SharedAsyncRateLimiter
from .temporary_pause import TemporaryPause
from .circuit_breaker import CircuitBreaker
from .priority_semaphore import PrioritySemaphore
from .bot_config import BotConfig
from .api_error import ApiError
from .async_rate_limiter import AsyncRateLimiter

class ExchangeClient:
    _RE_AUTH_SCHEME = re.compile(r"^(token|bearer|jwt)\s+(.+)$", re.IGNORECASE)
    _RE_PAUSE_SECONDS = re.compile(r"(\d+(?:\.\d+)?)\s*(?:s|sec|second|seconds|)", re.IGNORECASE)
    _RE_PAUSE_TA = re.compile(r"تا\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
    _PERSIAN_DIGITS = str.maketrans("\u06f0\u06f1\u06f2\u06f3\u06f4\u06f5\u06f6\u06f7\u06f8\u06f9", "0123456789")
    @staticmethod
    def _split_auth_token(raw: str) -> Tuple[str, str]:
        t = str(raw or "").strip()
        if (t.startswith("'") and t.endswith("'")) or (t.startswith('"') and t.endswith('"')):
            t = t[1:-1].strip()
        try:
            t = re.sub(r"^authorization\s*:\s*", "", t, flags=re.IGNORECASE).strip()
        except Exception:
            t = t.strip()
        scheme = "Token"
        m = ExchangeClient._RE_AUTH_SCHEME.match(t)
        if m:
            scheme = str(m.group(1)).title()
            t = str(m.group(2)).strip()
        else:
            try:
                if t.count(".") == 2 and len(t) > 20:
                    scheme = "Bearer"
            except Exception:
                pass
        try:
            t = re.sub(r"\s+", "", t)
        except Exception:
            t = t.replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "")
        return scheme, t
    def __init__(
        self,
        cfg: BotConfig,
        token: str,
        limiter: SharedAsyncRateLimiter,
        logger: logging.Logger,
        breaker: Optional[CircuitBreaker] = None,
    ):
        _s43_debug_print("### EXCHANGECLIENT_INIT_ENTER ###", flush=True)
        self.cfg = cfg
        self._auth_scheme, self._token = self._split_auth_token(token)
        if not self._token:
            self._auth_scheme = "Token"
            self._token = str(token or "").strip()
        try:
            if "arzplus" in str(getattr(cfg, "base_url", "") or "").lower():
                self._auth_scheme = "Token"
        except Exception:
            pass
        self.api_key = self._token
        self._headers_public = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._headers_private = dict(self._headers_public)
        if self._token:
            self._headers_private["Authorization"] = f"{self._auth_scheme or 'Token'} {self._token}"
        self._headers = self._headers_private
        try:
            _tok = str(getattr(self, "_token", "") or "")
            _base = str(getattr(cfg, "base_url", "") or "")
            _scheme = str(getattr(self, "_auth_scheme", "") or "")
            _masked = (_tok[:4] + "..." + _tok[-4:]) if len(_tok) >= 8 else ("set" if _tok else "empty")
            _pref = "raw"
            if _tok.startswith("Token "):
                _pref = "starts_with_Token_space"
            elif _tok.startswith("Bearer "):
                _pref = "starts_with_Bearer_space"
            _msg = (
                "event=ARZ_AUTH_DEBUG "
                f"base={_base} scheme={_scheme} tok_len={len(_tok)} "
                f"tok_mask={_masked} tok_prefix_state={_pref}"
            )
            if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
                try:
                    _lg = getattr(self, "_log", None)
                    if hasattr(_lg, "warning"):
                        _lg.warning(_msg)
                    elif callable(_lg):
                        _lg(_msg)
                    else:
                        print(_msg, flush=True)
                except Exception:
                    print(_msg, flush=True)
        except Exception:
            pass
        self._limiter = limiter
        self._logger = logger
        self._breaker = breaker or CircuitBreaker(
            cfg.circuit_breaker_errors,
            cfg.circuit_breaker_cooldown_sec,
            logger,
        )
        self._sem = PrioritySemaphore(1)  #
        self._session: Optional[aiohttp.ClientSession] = None
        self._last_all_tickers_snapshot: Optional[dict] = None
        self.last_update_time: float = 0.0
        self._last_market_stats_snapshot: Optional[dict] = None
        self.last_latency_ms: Optional[float] = None
        self.jitter_ms: Optional[float] = None
        self._lat_hist = __import__("collections").deque(maxlen=30)
        self._working_depth_ep: Optional[str] = None
        self._working_depth_ep_map: Dict[str, str] = {}
        self._working_depth_symid_map: Dict[str, str] = {}
        self._depth_ep_lock = asyncio.Lock()
        self._depth_ep_last_sym: Optional[str] = None
        self._depth_ep_last_ok_ts: float = 0.0
        self._arz_meta_cache: Optional[List[dict]] = None
        self._arz_meta_ts: float = 0.0
        self._arz_universe: List[str] = []
        self._arz_universe_ts: float = 0.0
        self._arz_scan_cursor: int = 0
        self._arz_stats_cache: Dict[str, Tuple[float, dict]] = {}
        self._arz_stats_ttl_sec: float = max(10.0, float(_env_float("ARZPLUS_STATS_TTL_SEC", 45.0)))
        self._arz_hydrate_batch: int = max(6, int(_env_int("ARZPLUS_HYDRATE_BATCH", 14)))
        self._arz_universe_refresh_sec: float = max(30.0, float(_env_float("ARZPLUS_UNIVERSE_REFRESH_SEC", 600.0)))
        # ArzPlus auth/HTTP diagnostics state (no strategy impact)
        self._last_server_date_ts: float = 0.0
        self._last_clock_drift_s: float = 0.0
        self._last_clock_warn_ts: float = 0.0
        self._last_403_log_ts_by_ep: Dict[str, float] = {}
        # Auth signing clock offset (seconds) for minor server drift self-heal (ArzPlus).
        self._auth_time_offset_s: float = 0.0
        self._auth_time_offset_lock = threading.Lock()
        self._last_clock_selfheal_ts: float = 0.0
    def _ensure_ready(self) -> None:
        'Self-heal missing runtime attributes (defensive, keeps bot one-piece).'
        try:
            cfg = getattr(self, "cfg", None)
            if cfg is None:
                return
        except Exception:
            return
        try:
            if not hasattr(self, "_token") or getattr(self, "_token", None) is None:
                raw = getattr(self, "api_key", "") or ""
                scheme, tok = self._split_auth_token(str(raw))
                self._auth_scheme, self._token = scheme, tok or str(raw or "").strip()
        except Exception:
            pass
        try:
            if not getattr(self, "_auth_scheme", None):
                if "arzplus" in str(getattr(self.cfg, "base_url", "") or "").lower():
                    self._auth_scheme = "Token"
                else:
                    self._auth_scheme = "Bearer"
        except Exception:
            pass
        try:
            hp = getattr(self, "_headers_public", None)
            if not isinstance(hp, dict):
                self._headers_public = {"Accept": "application/json", "Content-Type": "application/json"}
        except Exception:
            self._headers_public = {"Accept": "application/json", "Content-Type": "application/json"}
        try:
            hv = getattr(self, "_headers_private", None)
            if not isinstance(hv, dict):
                self._headers_private = dict(getattr(self, "_headers_public", {}) or {})
            if getattr(self, "_token", "") and "Authorization" not in self._headers_private:
                self._headers_private["Authorization"] = f"{getattr(self, '_auth_scheme', 'Token') or 'Token'} {getattr(self, '_token', '')}"
        except Exception:
            pass
        try:
            if not hasattr(self, "_headers") or not isinstance(getattr(self, "_headers", None), dict):
                self._headers = getattr(self, "_headers_private", None) or getattr(self, "_headers_public", None) or {}
        except Exception:
            pass
        try:
            if not hasattr(self, "_limiter") or getattr(self, "_limiter", None) is None:
                rpm = int(getattr(cfg, "rate_limit_per_min", 100) or 100)
                self._limiter = SharedAsyncRateLimiter(max(10, rpm))
        except Exception:
            try:
                self._limiter = SharedAsyncRateLimiter(100)
            except Exception:
                pass
        try:
            if not hasattr(self, "_logger") or getattr(self, "_logger", None) is None:
                self._logger = logging.getLogger("RazTraderPlus")
        except Exception:
            pass
        try:
            if not hasattr(self, "_breaker") or getattr(self, "_breaker", None) is None:
                self._breaker = CircuitBreaker(
                    int(getattr(cfg, "circuit_breaker_errors", 6) or 6),
                    float(getattr(cfg, "circuit_breaker_cooldown_sec", 45.0) or 45.0),
                    self._logger if isinstance(getattr(self, "_logger", None), logging.Logger) else logging.getLogger("RazTraderPlus"),
                )
        except Exception:
            pass
        try:
            if not hasattr(self, "_sem") or getattr(self, "_sem", None) is None:
                self._sem = PrioritySemaphore(1)
        except Exception:
            pass
        try:
            if not hasattr(self, "_session"):
                self._session = None
        except Exception:
            pass
        try:
            if not hasattr(self, "_depth_ep_lock") or getattr(self, "_depth_ep_lock", None) is None:
                self._depth_ep_lock = asyncio.Lock()
        except Exception:
            pass
        try:
            if not hasattr(self, "_working_depth_ep_map") or not isinstance(getattr(self, "_working_depth_ep_map", None), dict):
                self._working_depth_ep_map = {}
        except Exception:
            pass
        try:
            if not hasattr(self, "_working_depth_symid_map") or not isinstance(getattr(self, "_working_depth_symid_map", None), dict):
                self._working_depth_symid_map = {}
        except Exception:
            pass
        try:
            if not hasattr(self, "_arz_stats_cache") or not isinstance(getattr(self, "_arz_stats_cache", None), dict):
                self._arz_stats_cache = {}
        except Exception:
            pass
    async def _discover_depth_endpoint(self, symbol: str) -> str:
        sym0 = _canon_symbol(symbol)
        aliases = _symbol_aliases(sym0) or [sym0]
        try:
            m = getattr(self, "_working_depth_ep_map", None)
            if isinstance(m, dict):
                ep0 = m.get(sym0)
                if isinstance(ep0, str) and ep0:
                    return ep0
        except Exception:
            pass
        candidates: List[str] = []
        try:
            cand_env = str(os.environ.get("DEPTH_ENDPOINT_CANDIDATES", "") or "").strip()
        except Exception:
            cand_env = ""
        if cand_env:
            candidates.extend([c.strip() for c in cand_env.split(",") if c.strip()])
        candidates.extend([
            "/market/depth/{sym}",
            "/market/depth/{sym}/",
            "/market/depth?symbol={sym}",
            "/market/depth",
            "/market/orderbook/{sym}",
            "/market/orderbook?symbol={sym}",
            "/market/orderbook",
            "/market/order-book/{sym}",
            "/market/order-book",
            "/depth/{sym}",
            "/depth?symbol={sym}",
            "/depth",
            "/api/v1/depth/{sym}",
            "/api/v1/depth",
            "/api/v1/orderbook/{sym}",
            "/api/v1/orderbook",
        ])
        seen: set = set()
        uniq: List[str] = []
        for ep in candidates:
            if ep and ep not in seen:
                uniq.append(ep)
                seen.add(ep)
        try:
            probe_to = float(os.environ.get("DEPTH_DISCOVER_TIMEOUT_SEC", "3.0" if _env_bool("TERMUX_MODE", False) else "2.0") or 2.0)
        except Exception:
            probe_to = 2.0
        probe_to = max(0.9, float(probe_to))
        def _call_specs(ep: str, a: str) -> List[Tuple[str, Optional[dict]]]:
            if not ep:
                return []
            if "{sym}" in ep:
                try:
                    return [(ep.format(sym=a), None)]
                except Exception:
                    return []
            return [
                (ep, {"symbol": a}),
                (ep, {"market": a}),
                (ep, {"pair": a}),
            ]
        def _looks_like_book(payload: Any) -> bool:
            try:
                if payload is None:
                    return False
                if isinstance(payload, dict):
                    d = payload.get("data") if isinstance(payload.get("data"), dict) else payload
                    return bool(
                        (isinstance(d, dict) and (("bids" in d) or ("asks" in d)))
                        or ("bids" in payload) or ("asks" in payload)
                        or ("orderbook" in payload) or ("orderBook" in payload) or ("order_book" in payload)
                    )
                if isinstance(payload, list) and payload:
                    for x in payload[:2]:
                        if isinstance(x, dict) and _looks_like_book(x):
                            return True
                return False
            except Exception:
                return False
        last_err = ""
        for ep in uniq:
            for a in (aliases[: max(1, min(3, len(aliases)))]):
                for url, params in _call_specs(ep, a):
                    t0 = time.time()
                    try:
                        if getattr(self._logger, "isEnabledFor", None) and self._logger.isEnabledFor(logging.DEBUG):
                            try:
                                self._logger.debug("event=DEPTH_DISCOVER_TRY sym=%s ep=%s url=%s params=%s", sym0, ep, url, params)
                            except Exception:
                                pass
                        res = await asyncio.wait_for(
                            self.request("GET", url, auth=False, params=params, priority=bool(priority)),
                            timeout=probe_to,
                        )
                        if _looks_like_book(res):
                            try:
                                self._working_depth_ep_map[sym0] = ep
                            except Exception:
                                pass
                            try:
                                self._working_depth_symid_map[sym0] = str(a)
                            except Exception:
                                pass
                            self._working_depth_ep = ep
                            self._depth_ep_last_sym = sym0
                            try:
                                self._logger.info("event=DEPTH_EP_OK sym=%s ep=%s dt_ms=%.0f", sym0, ep, (time.time() - t0) * 1000.0)
                            except Exception:
                                pass
                            return ep
                    except Exception as e:
                        try:
                            last_err = str(e or "").strip()
                        except Exception:
                            last_err = ""
                        if getattr(self._logger, "isEnabledFor", None) and self._logger.isEnabledFor(logging.DEBUG):
                            try:
                                self._logger.debug("event=DEPTH_DISCOVER_FAIL sym=%s ep=%s err=%s dt_ms=%.0f", sym0, ep, last_err[:160], (time.time() - t0) * 1000.0)
                            except Exception:
                                pass
                        continue
        try:
            self._logger.warning("event=DEPTH_EP_DISCOVER_FAIL sym=%s last_err=%s", sym0, str(last_err)[:160])
        except Exception:
            pass
        return "/market/depth/{sym}"
    def invalidate_depth_endpoint(self, symbol: str, reason: str = "") -> None:
        sym = _canon_symbol(symbol)
        try:
            m = getattr(self, "_working_depth_ep_map", None)
            if isinstance(m, dict):
                m.pop(sym, None)
        except Exception:
            pass
        try:
            m2 = getattr(self, "_working_depth_symid_map", None)
            if isinstance(m2, dict):
                m2.pop(sym, None)
        except Exception:
            pass
        try:
            if getattr(self, "_depth_ep_last_sym", None) == sym:
                self._working_depth_ep = None
                self._depth_ep_last_sym = None
        except Exception:
            pass
        if getattr(self._logger, "isEnabledFor", None) and self._logger.isEnabledFor(logging.DEBUG):
            try:
                self._logger.debug("event=DEPTH_EP_INVALIDATE sym=%s reason=%s", sym, str(reason or "")[:80])
            except Exception:
                pass
    async def get_depth(self, symbol: str, priority: bool = False) -> dict:
        q = str(getattr(self.cfg, "quote", "") or "").upper().strip()
        sym = _canon_pair(symbol, default_quote=q)
        if q and sym.upper() == q:
            return {}
        if self._is_arzplus():
            last_err: Optional[Exception] = None
            for ep2 in (f"/market/depth/{sym}", f"/market/depth/{sym}/"):
                try:
                    return await self.request("GET", ep2, auth=False, params=None, priority=bool(priority))
                except Exception as e:
                    last_err = e
            for ep2 in ("/market/depth", "/market/depth/"):
                try:
                    return await self.request("GET", ep2, auth=False, params={"symbol": sym}, priority=bool(priority))
                except Exception as e:
                    last_err = e
            if last_err:
                raise last_err
            return {}
        ep = None
        try:
            m = getattr(self, "_working_depth_ep_map", None)
            if isinstance(m, dict):
                ep = m.get(sym)
        except Exception:
            ep = None
        if not ep:
            try:
                if getattr(self, "_depth_ep_last_sym", None) == sym:
                    ep = getattr(self, "_working_depth_ep", None)
            except Exception:
                ep = None
        if not ep:
            lock = getattr(self, "_depth_ep_lock", None)
            if lock is None:
                ep = await self._discover_depth_endpoint(sym)
            else:
                async with lock:
                    try:
                        m = getattr(self, "_working_depth_ep_map", None)
                        if isinstance(m, dict):
                            ep = m.get(sym)
                    except Exception:
                        ep = None
                    if not ep:
                        ep = await self._discover_depth_endpoint(sym)
        try:
            if isinstance(ep, str) and ep:
                self._working_depth_ep_map[sym] = ep
                self._working_depth_ep = ep
                self._depth_ep_last_sym = sym
        except Exception:
            pass
        def _build_call(ep_t: str, sym_used: str) -> Tuple[str, Optional[dict]]:
            url = ep_t
            params = None
            try:
                if isinstance(ep_t, str) and "{sym}" in ep_t:
                    url = ep_t.format(sym=sym_used)
                    params = None
                else:
                    params = {"symbol": sym_used}
            except Exception:
                url = ep_t
                params = {"symbol": sym_used}
            return url, params
        sym_used = sym
        try:
            m = getattr(self, "_working_depth_symid_map", None)
            if isinstance(m, dict):
                su = m.get(sym)
                if isinstance(su, str) and su:
                    sym_used = su
        except Exception:
            sym_used = sym
        url, params = _build_call(str(ep), sym_used)
        try:
            timeout = float(os.getenv("DEPTH_REQ_TIMEOUT_SEC", "7.0" if _env_bool("TERMUX_MODE", False) else "5.0") or 5.0)
        except Exception:
            timeout = 5.0
        timeout = max(1.0, float(timeout))
        t0 = time.time()
        try:
            out = await asyncio.wait_for(
                self.request("GET", url, auth=False, params=params, priority=bool(priority)),
                timeout=timeout,
            )
            try:
                self._depth_ep_last_ok_ts = float(time.time())
            except Exception:
                pass
            if getattr(self._logger, "isEnabledFor", None) and self._logger.isEnabledFor(logging.DEBUG):
                try:
                    self._logger.debug("event=DEPTH_OK sym=%s ep=%s dt_ms=%.0f", sym, str(ep), (time.time() - t0) * 1000.0)
                except Exception:
                    pass
            return out
        except Exception as e:
            msg = ""
            try:
                msg = str(e or "").strip()
            except Exception:
                msg = ""
            is_404 = ("HTTP 404" in msg) or msg.startswith("404") or (" 404" in msg)
            if is_404:
                try:
                    self.invalidate_depth_endpoint(sym, reason="HTTP_404")
                except Exception:
                    pass
                try:
                    lock = getattr(self, "_depth_ep_lock", None)
                    if lock is None:
                        ep2 = await self._discover_depth_endpoint(sym)
                    else:
                        async with lock:
                            ep2 = await self._discover_depth_endpoint(sym)
                    sym_used2 = sym
                    try:
                        m = getattr(self, "_working_depth_symid_map", None)
                        if isinstance(m, dict):
                            su2 = m.get(sym)
                            if isinstance(su2, str) and su2:
                                sym_used2 = su2
                    except Exception:
                        sym_used2 = sym
                    url2, params2 = _build_call(str(ep2), sym_used2)
                    out = await asyncio.wait_for(
                        self.request("GET", url2, auth=False, params=params2, priority=bool(priority)),
                        timeout=timeout,
                    )
                    try:
                        self._working_depth_ep_map[sym] = str(ep2)
                        self._working_depth_ep = str(ep2)
                        self._depth_ep_last_sym = sym
                        self._depth_ep_last_ok_ts = float(time.time())
                    except Exception:
                        pass
                    if getattr(self._logger, "isEnabledFor", None) and self._logger.isEnabledFor(logging.DEBUG):
                        try:
                            self._logger.debug("event=DEPTH_OK_RETRY sym=%s ep=%s dt_ms=%.0f", sym, str(ep2), (time.time() - t0) * 1000.0)
                        except Exception:
                            pass
                    return out
                except Exception:
                    pass
            try:
                self._logger.warning("event=DEPTH_FETCH_FAIL sym=%s ep=%s err=%s", sym, str(ep), msg[:180])
            except Exception:
                pass
            raise
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=float(self.cfg.request_timeout_sec))
            headers = {
                "User-Agent": self.cfg.user_agent,
                "Accept": "application/json",
            }
            try:
                ns =  _dns_public_nameservers()
            except Exception:
                ns = []
            try:
                if ns:
                    resolver = aiohttp.AsyncResolver(nameservers=ns)
                else:
                    resolver = aiohttp.AsyncResolver()
            except Exception:
                try:
                    resolver = aiohttp.DefaultResolver()
                except Exception:
                    resolver = None
            try:
                ttl = int(_env_int("DNS_CACHE_TTL_SEC", 300) or 300)
            except Exception:
                ttl = 300
            fam = 0
            try:
                termux_force = bool(_env_bool("TERMUX_MODE", False))
            except Exception:
                termux_force = False
            try:
                if termux_force or bool(_env_bool("DNS_FORCE_IPV4", False)):
                    fam = socket.AF_INET
            except Exception:
                fam = socket.AF_INET if termux_force else 0
            try:
                connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=int(ttl), use_dns_cache=True, resolver=resolver, family=fam if fam else 0)
            except Exception:
                connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=int(ttl), use_dns_cache=True, resolver=resolver)
            self._session = aiohttp.ClientSession(headers=headers, timeout=timeout, connector=connector)
        return self._session
    async def reset_session(self) -> bool:
        """Best-effort network reset (used by ActiveWatchdog recovery).

        """
        try:
            sess = getattr(self, "_session", None)
            if sess is not None and (not getattr(sess, "closed", True)):
                await sess.close()
        except Exception:
            pass
        try:
            self._session = None
        except Exception:
            pass
        try:
            self.last_update_time = 0.0
        except Exception:
            pass
        try:
            br = getattr(self, "_breaker", None)
            if br is not None and hasattr(br, "reset"):
                br.reset()
        except Exception:
            pass
        try:
            lim = getattr(self, "_limiter", None)
            if lim is not None and hasattr(lim, "reset"):
                out = lim.reset()
                if asyncio.iscoroutine(out):
                    await out
        except Exception:
            pass
        return True
    async def reset_http(self) -> bool:
        return await self.reset_session()
    async def reset_network(self) -> bool:
        return await self.reset_session()
    @staticmethod
    def _is_transient_for_breaker(exc: Exception) -> bool:
        try:
            if isinstance(exc, (asyncio.TimeoutError, aiohttp.ClientError, OSError)):
                return True
        except Exception:
            pass
        try:
            msg = str(exc or "")
        except Exception:
            msg = ""
        msgu = msg.upper()
        if "TRANSIENT HTTP" in msgu or "BAD JSON" in msgu or "JSONDECODE" in msgu:
            return True
        for code in ("HTTP 429", "HTTP 500", "HTTP 502", "HTTP 503", "HTTP 504"):
            if code in msgu:
                return True
        return False
    @staticmethod
    def _safe_body_for_log(raw: str, limit: int = 180) -> str:
        try:
            s = str(raw or "")
        except Exception:
            return ""
        try:
            s = s.replace("\n", " ").replace("\r", " ").strip()
        except Exception:
            pass
        try:
            s = s.encode("ascii", "ignore").decode("ascii", "ignore")
        except Exception:
            pass
        if len(s) > int(limit):
            s = s[: int(limit)]
        return s

    @staticmethod
    def _sanitize_body_for_debug(raw: str, limit: int = 300) -> str:
        """Short body snippet for logs (unicode-safe, redacted, max `limit` chars)."""
        try:
            s = str(raw or "")
        except Exception:
            return ""
        try:
            s = s.replace("\r", " ").replace("\n", " ")
            s = re.sub(r"\s+", " ", s).strip()
        except Exception:
            pass
        try:
            # Reuse global redactor (tokens/keys) if present
            if "_pp200_redact" in globals() and callable(globals().get("_pp200_redact")):
                s = globals()["_pp200_redact"](s)
        except Exception:
            pass
        if len(s) > int(limit):
            s = s[: int(limit)]
        return s

    @staticmethod
    def _waf_headers_subset(resp_headers: Dict[str, str]) -> Dict[str, str]:
        """Return a compact subset of server/WAF-related headers."""
        out: Dict[str, str] = {}
        if not isinstance(resp_headers, dict):
            return out
        keys_keep = {
            "date", "server", "via", "content-type", "content-length",
            "cf-ray", "cf-cache-status", "cf-request-id", "cf-worker",
            "cf-bgj", "cf-apo-via", "cf-ipcountry",
            "x-request-id", "x-correlation-id", "x-amzn-requestid", "x-amz-cf-id",
            "x-sucuri-id", "x-sucuri-cache", "x-waf", "x-akamai-transformed",
            "x-kong-proxy-latency", "x-kong-upstream-latency", "x-envoy-upstream-service-time",
        }
        try:
            for k, v in resp_headers.items():
                kk = str(k or "").strip()
                if not kk:
                    continue
                lk = kk.lower()
                if lk in keys_keep or lk.startswith("cf-") or "cloudflare" in lk or "waf" in lk:
                    out[kk] = str(v)
        except Exception:
            return out
        return out

    @staticmethod
    def _parse_http_date_to_ts(date_val: str) -> Optional[float]:
        """Parse RFC1123 Date header to epoch seconds."""
        try:
            try:
                try:
                    from email.utils import parsedate_to_datetime
                except:
                    pass
            except:
                pass
            dt = parsedate_to_datetime(str(date_val))
            if dt is None:
                return None
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return float(dt.timestamp())
        except Exception:
            return None

    def _clock_drift_from_headers(self, resp_headers: Dict[str, str]) -> Tuple[Optional[float], Optional[float]]:
        """Return (server_ts, drift_seconds) using HTTP Date header when available."""
        try:
            if not isinstance(resp_headers, dict):
                return None, None
            date_val = resp_headers.get("Date") or resp_headers.get("date") or ""
            if not date_val:
                return None, None
            st = self._parse_http_date_to_ts(str(date_val))
            if st is None:
                return None, None
            lt = float(time.time())
            # Apply auth time offset (self-healed from minor drift) so drift checks reflect corrected signing time.
            off = 0.0
            try:
                lk = getattr(self, "_auth_time_offset_lock", None)
                if lk is not None:
                    with lk:
                        off = float(getattr(self, "_auth_time_offset_s", 0.0) or 0.0)
                else:
                    off = float(getattr(self, "_auth_time_offset_s", 0.0) or 0.0)
            except Exception:
                off = 0.0
            drift = abs((float(lt) + float(off)) - float(st))
            return float(st), float(drift)
        except Exception:
            return None, None

    def _arzplus_health_check_clock(self, *, resp_headers: Dict[str, str], endpoint: str = "") -> None:
        """Health-check: compare local time with server time; warn if drift > 2s."""
        try:
            if not self._is_arzplus():
                return
            st, drift = self._clock_drift_from_headers(resp_headers or {})
            if drift is None:
                return
            self._last_server_date_ts = float(st or 0.0)
            self._last_clock_drift_s = float(drift or 0.0)
            # Minor drift self-heal: adjust auth signing time offset for small skews (<= 2s).
            try:
                if float(drift) > 0.0 and float(drift) <= 2.0 and st is not None:
                    now_raw = float(time.time())
                    lk = getattr(self, "_auth_time_offset_lock", None)
                    cur_off = 0.0
                    try:
                        if lk is not None:
                            with lk:
                                cur_off = float(getattr(self, "_auth_time_offset_s", 0.0) or 0.0)
                        else:
                            cur_off = float(getattr(self, "_auth_time_offset_s", 0.0) or 0.0)
                    except Exception:
                        cur_off = 0.0
                    delta = float(st) - (float(now_raw) + float(cur_off))
                    if abs(float(delta)) > 0.0 and abs(float(delta)) <= 2.0:
                        do_log = False
                        try:
                            last2 = float(getattr(self, "_last_clock_selfheal_ts", 0.0) or 0.0)
                            do_log = (now_raw - last2) >= 60.0
                            setattr(self, "_last_clock_selfheal_ts", float(now_raw))
                        except Exception:
                            do_log = False
                        try:
                            if lk is not None:
                                with lk:
                                    setattr(self, "_auth_time_offset_s", float(cur_off) + float(delta))
                            else:
                                setattr(self, "_auth_time_offset_s", float(cur_off) + float(delta))
                        except Exception:
                            pass
                        if do_log:
                            try:
                                self._logger.info(
                                    "event=ARZPLUS_CLOCK_SELFHEAL endpoint=%s drift_s=%.3f delta_s=%.3f new_offset_s=%.3f",
                                    str(endpoint or ""), float(drift), float(delta), float(cur_off + delta),
                                )
                            except Exception:
                                pass
            except Exception:
                pass
            if float(drift) <= 2.0:
                return
            now = float(time.time())
            # throttle warnings
            if (now - float(self._last_clock_warn_ts or 0.0)) < 60.0:
                return
            self._last_clock_warn_ts = now
            try:
                self._logger.warning(
                    "event=ARZPLUS_CLOCK_SKEW_WARN exchange=arzplus endpoint=%s drift_s=%.3f local_ts=%.3f server_ts=%.3f",
                    str(endpoint or ""), float(drift), float(now), float(st),
                )
            except Exception:
                pass
        except Exception:
            return

    def _arzplus_detect_403_cause(
        self,
        *,
        endpoint: str,
        body_snip: str,
        resp_headers: Dict[str, str],
        drift_s: Optional[float],
    ) -> str:
        """Heuristic root-cause for ArzPlus 403 (permission scope / IP-WAF block / clock skew)."""
        try:
            # 1) clock skew has top priority
            if drift_s is not None and float(drift_s) > 2.0:
                return "clock_skew"
        except Exception:
            pass
        try:
            h = resp_headers or {}
            srv = str(h.get("server") or h.get("Server") or "").lower()
            # Cloudflare / WAF / IP block hints
            if ("cf-ray" in {k.lower() for k in h.keys()}) or ("cloudflare" in srv):
                return "ip_waf_block"
            b = str(body_snip or "").lower()
            if any(x in b for x in ("cloudflare", "attention required", "access denied", "forbidden", "waf", "blocked", "ip")):
                return "ip_waf_block"
        except Exception:
            pass
        try:
            ep = str(endpoint or "").lower()
            b = str(body_snip or "").lower()
            if "/wallet/balance" in ep or "balance" in ep:
                if any(x in b for x in ("permission", "scope", "not allowed", "denied", "unauthorized", "token")):
                    return "permission_scope_balance"
                # if it's only balance endpoint and not WAF, assume permission/IP allowlist issue
                return "permission_scope_balance"
        except Exception:
            pass
        return "unknown"

    def _arzplus_log_403(
        self,
        *,
        endpoint: str,
        method: str,
        http_status: int,
        raw: str,
        resp_headers: Dict[str, str],
        req_headers: Dict[str, str],
        drift_s: Optional[float],
        cause: str,
    ) -> None:
        """Emit the required 403 diagnostic log line (throttled per endpoint)."""
        try:
            if not self._is_arzplus():
                return
            ep = str(endpoint or "")
            now = float(time.time())
            last = float((self._last_403_log_ts_by_ep or {}).get(ep, 0.0) or 0.0)
            if (now - last) < 20.0:
                return
            self._last_403_log_ts_by_ep[ep] = now
            body_snip = self._sanitize_body_for_debug(raw, limit=300)
            waf_hdrs = self._waf_headers_subset(resp_headers or {})
            # auth masking (never log token)
            auth_fp = ""
            try:
                auth_val = str((req_headers or {}).get("Authorization") or "")
                if auth_val and ("_token_fingerprint" in globals()) and callable(globals().get("_token_fingerprint")):
                    auth_fp = globals()["_token_fingerprint"](auth_val)
            except Exception:
                auth_fp = ""
            try:
                self._logger.error(
                    "event=ARZPLUS_HTTP_403 exchange=arzplus endpoint=%s method=%s http_status=%s body=%s headers=%s api_key=%s api_secret=%s auth_fp=%s cause=%s drift_s=%s",
                    ep,
                    str(method or "GET"),
                    int(http_status or 0),
                    body_snip,
                    json.dumps(waf_hdrs, ensure_ascii=False, separators=(',', ':')),
                    "****",
                    "****",
                    str(auth_fp or ""),
                    str(cause or ""),
                    (f"{float(drift_s):.3f}" if drift_s is not None else "-"),
                )
            except Exception:
                pass
        except Exception:
            return
    @classmethod
    def _extract_rate_limit_pause_sec(cls, raw: str, default: float = 1.0) -> float:
        try:
            s = str(raw or "")
        except Exception:
            return float(default)
        try:
            obj = json.loads(s) if s and s.strip().startswith("{") else None
            if isinstance(obj, dict):
                s2 = obj.get("detail") or obj.get("message") or obj.get("error") or ""
                if s2:
                    s = str(s2)
        except Exception:
            pass
        try:
            s = s.translate(cls._PERSIAN_DIGITS)
        except Exception:
            pass
        m = cls._RE_PAUSE_SECONDS.search(s)
        if not m:
            m = cls._RE_PAUSE_TA.search(s)
        if not m:
            return float(default)
        try:
            v = float(m.group(1))
        except Exception:
            return float(default)
        return float(max(0.5, min(10.0, v)))
    def _raise_if_breaker_open(self) -> None:
        if self._breaker.is_open():
            try:
                rem = float(self._breaker.remaining_sec())
            except Exception:
                rem = 0.0
            raise TemporaryPause("Circuit breaker open (API).", pause_sec=rem)
    def _build_url(self, endpoint: str) -> str:
        ep = str(endpoint or "").strip()
        return f"{self.cfg.base_url}{ep if ep.startswith('/') else '/' + ep}"
    def _build_headers(self, auth: bool) -> dict:
        headers: dict = {
            "Accept": "application/json",
            "User-Agent": str(getattr(self.cfg, "user_agent", "PhoenixBot/1.0") or "PhoenixBot/1.0"),
        }
        if not auth:
            return headers
        if not self._token:
            raise ApiError("Missing API token for private endpoint.")
        try:
            hp = getattr(self, "_headers_private", None)
            if isinstance(hp, dict):
                headers.update(hp)
        except Exception:
            pass
        if "Authorization" not in headers:
            auth_value = f"{getattr(self, '_auth_scheme', 'Token') or 'Token'} {self._token}"
            _s43_debug_print(f"[AUTHDBG_HEADER] present={bool(auth_value)} scheme={str(auth_value).split()[0] if str(auth_value).split() else ''} len={len(str(auth_value))}")
            headers["Authorization"] = auth_value
        # Include Date header for ArzPlus private requests using self-healed signing time offset.
        try:
            if self._is_arzplus():
                if ("Date" not in headers) and ("date" not in headers):
                    try:
                        try:
                            from email.utils import formatdate
                        except:
                            pass
                    except:
                        pass
                    off = 0.0
                    try:
                        lk = getattr(self, "_auth_time_offset_lock", None)
                        if lk is not None:
                            with lk:
                                off = float(getattr(self, "_auth_time_offset_s", 0.0) or 0.0)
                        else:
                            off = float(getattr(self, "_auth_time_offset_s", 0.0) or 0.0)
                    except Exception:
                        off = 0.0
                    headers["Date"] = formatdate(timeval=float(time.time()) + float(off), usegmt=True)
        except Exception:
            pass
        return headers
    def _update_network_metrics(self, t0: float) -> None:
        try:
            lat_ms = (time.time() - float(t0)) * 1000.0
            self.last_latency_ms = float(lat_ms)
            self._lat_hist.append(float(lat_ms))
            if len(self._lat_hist) >= 5:
                avg = sum(self._lat_hist) / float(len(self._lat_hist))
                self.jitter_ms = sum(abs(x - avg) for x in self._lat_hist) / float(len(self._lat_hist))
            else:
                self.jitter_ms = 0.0
        except Exception:
            pass
    async def _fetch_text(
        self,
        sess: aiohttp.ClientSession,
        method_u: str,
        url: str,
        payload: Optional[dict],
        params: Optional[dict],
        headers: dict,
    ) -> Tuple[int, str, Dict[str, str]]:
        async with sess.request(method_u, url, json=payload, params=params, headers=headers) as resp:
            raw = await resp.text()
            try:
                rh = {str(k): str(v) for k, v in (getattr(resp, "headers", {}) or {}).items()}
            except Exception:
                rh = {}
            return int(getattr(resp, "status", 0) or 0), raw, rh
    async def _handle_http_errors(
        self,
        status: int,
        raw: str,
        *,
        endpoint: str = "",
        method: str = "",
        url: str = "",
        resp_headers: Optional[Dict[str, str]] = None,
        req_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        st = int(status or 0)
        rh = dict(resp_headers or {})
        qh = dict(req_headers or {})
        # Health-check clock drift (warn only; no strategy impact)
        try:
            self._arzplus_health_check_clock(resp_headers=rh, endpoint=str(endpoint or ""))
        except Exception:
            pass
        match st:
            case 429:
                pause = self._extract_rate_limit_pause_sec(raw, default=1.0)
                try:
                    await self._limiter.penalize(pause, hard=True)
                except Exception:
                    pass
                raise TemporaryPause("Rate limited by exchange (HTTP 429).", pause_sec=pause)
            case 500 | 502 | 503 | 504:
                body = self._safe_body_for_log(raw)
                raise ApiError(f"Transient HTTP {st}: {body}")
            case 401 | 403:
                body_snip = self._sanitize_body_for_debug(raw, limit=300)
                # Determine clock drift, WAF/IP allowlist, or permission scope issues
                _st, drift = self._clock_drift_from_headers(rh)
                cause = self._arzplus_detect_403_cause(
                    endpoint=str(endpoint or ""),
                    body_snip=str(body_snip or ""),
                    resp_headers=rh,
                    drift_s=drift,
                )
                if st == 403 and self._is_arzplus() and cause in ("clock_skew", "ip_waf_block"):
                    raise TradingHalt(f"ARZPLUS_403_{cause}")
                if st == 403 and ("/wallet/balance" in str(endpoint or "").lower()):
                    self._arzplus_log_403(
                        endpoint=str(endpoint or ""),
                        method=str(method or ""),
                        http_status=st,
                        raw=str(raw or ""),
                        resp_headers=rh,
                        req_headers=qh,
                        drift_s=drift,
                        cause=cause,
                    )
                # Keep message compatible with existing checks ("HTTP 401"/"HTTP 403" substring)
                raise ApiHttpError(
                    f"HTTP {st}: {body_snip}",
                    exchange=("arzplus" if self._is_arzplus() else ""),
                    endpoint=str(endpoint or ""),
                    method=str(method or ""),
                    url=str(url or ""),
                    http_status=st,
                    body=str(body_snip or ""),
                    resp_headers=rh,
                    req_headers=qh,
                    drift_s=drift,
                    cause=cause,
                    auth_mask="****",
                    auth_fp="",
                )
            case s if s >= 400:
                body = self._safe_body_for_log(raw)
                raise ApiError(f"HTTP {s}: {body}")
            case _:
                return
    def _decode_json(self, raw: str) -> dict:
        try:
            return json.loads(raw) if raw else {}
        except json.JSONDecodeError as e:
            body = self._safe_body_for_log(raw)
            raise ApiError(f"Bad JSON: {e}: {body}")
    async def _on_success(self) -> None:
        self._breaker.record_success()
        try:
            self.last_update_time = time.time()
        except Exception:
            pass
        try:
            await self._limiter.reward()
        except Exception:
            pass
    def _record_failure_if_transient(self, exc: Exception) -> None:
        if self._is_transient_for_breaker(exc):
            self._breaker.record_failure(exc)
    def _harden_request(
        self,
        *,
        method: str,
        endpoint: str,
        url: str,
        headers: dict,
        payload: Optional[dict],
        params: Optional[dict],
        auth: bool,
    ) -> None:
        """Root hardening for outbound HTTP.

        This is intentionally in the *base* client so it cannot be bypassed by
        incorrect subclass overrides (no monkey-patching, single call-site).
        """
        method_u = str(method or "").upper()
        if method_u not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
            raise ApiError(f"Unsupported HTTP method: {method_u}")
        ep = str(endpoint or "")
        if "\r" in ep or "\n" in ep:
            raise ApiError("Bad endpoint (CR/LF).")
        u = str(url or "")
        if "\r" in u or "\n" in u:
            raise ApiError("Bad url (CR/LF).")
        if payload is not None and (not isinstance(payload, dict)):
            raise ApiError("payload must be a dict (or None).")
        if params is not None and (not isinstance(params, dict)):
            raise ApiError("params must be a dict (or None).")
        if not isinstance(headers, dict):
            raise ApiError("headers must be a dict.")
        for k, v in list(headers.items()):
            if v is None:
                continue
            sv = str(v)
            if "\r" in sv or "\n" in sv:
                raise ApiError(f"Bad header value (CR/LF) for {str(k)[:32]}.")
        if bool(auth) and "Authorization" not in headers:
            raise ApiError("Missing Authorization header for private request.")
        # Ensure we never drift outside the configured base_url.
        try:
            base = str(getattr(self.cfg, "base_url", "") or "")
            if base and (not u.startswith(base)):
                raise ApiError("Refusing to send request outside configured base_url.")
        except Exception:
            pass

    async def _request_impl(
        self,
        method: str,
        endpoint: str,
        payload: Optional[dict] = None,
        auth: bool = False,
        params: Optional[dict] = None,
        priority: bool = False,
    ) -> dict:
        max_tries = 3
        base_delay = float(_env_float("HTTP_RETRY_BASE_SEC", 0.35) or 0.35)
        cap_delay = float(_env_float("HTTP_RETRY_CAP_SEC", 3.0) or 3.0)
        for attempt in range(1, max_tries + 1):
            self._ensure_ready()
            self._raise_if_breaker_open()
            await self._limiter.wait()
            method_u = str(method or "GET").upper()
            url = self._build_url(endpoint)
            headers = self._build_headers(auth)
            self._harden_request(
                method=method_u,
                endpoint=str(endpoint or ""),
                url=url,
                headers=headers,
                payload=payload,
                params=params,
                auth=bool(auth),
            )
            async with self._sem:
                sess = await self._get_session()
                try:
                    t0 = time.time()
                    status, raw, resp_headers = await self._fetch_text(sess, method_u, url, payload, params, headers)
                    self._update_network_metrics(t0)
                    await self._handle_http_errors(
                        status,
                        raw,
                        endpoint=str(endpoint or ''),
                        method=method_u,
                        url=url,
                        resp_headers=resp_headers,
                        req_headers=headers,
                    )
                    data = self._decode_json(raw)
                    await self._on_success()
                    return data
                except TemporaryPause as e: self._record_failure_if_transient(e); raise
                except (aiohttp.ClientError, asyncio.TimeoutError, OSError, ApiError) as e:
                    msg = str(e)
                    retryable = isinstance(e, (aiohttp.ClientError, asyncio.TimeoutError, OSError)) or ("Transient HTTP" in msg)
                    if retryable and attempt < max_tries:
                        delay = min(cap_delay, base_delay * (2 ** (attempt - 1)))
                        await asyncio.sleep(delay)
                        continue
                    self._record_failure_if_transient(e)
                    raise
    async def request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[dict] = None,
        auth: bool = False,
        params: Optional[dict] = None,
        priority: bool = False,
    ) -> dict:
        return await self._request_impl(method, endpoint, payload=payload, auth=auth, params=params, priority=priority)

    async def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[dict] = None,
        auth: bool = False,
        params: Optional[dict] = None,
        priority: bool = False,
    ) -> dict:
        # Backward-compatible alias for older call sites.
        return await self._request_impl(method, endpoint, payload=payload, auth=auth, params=params, priority=priority)
    async def get_symbols(self) -> dict:
        tmo = float(_env_float("TICKERS_REQ_TIMEOUT", _env_float("BATCH_TICKERS_TIMEOUT_SEC", 6.5)) or 5.0)
        return await asyncio.wait_for(self.request("GET", "/market/symbols/", auth=False, params=None), timeout=tmo)
    async def get_all_tickers(self) -> dict:
        if self._is_arzplus():
            return await self._arzplus_market_snapshot()
        now = time.time()
        endpoints = (
            "/market/tickers/",
            "/market/tickers",
            "/market/ticker/",
            "/market/ticker",
        )
        last_err = None
        def _to_unix_seconds(ts_val: Any) -> Optional[float]:
            try:
                v = float(ClockArbiter._epoch_to_seconds(ts_val))
                if v <= 0.0 or (not math.isfinite(v)):
                    return None
                if v < 946684800.0 or v > (float(now) + 300.0):
                    return None
                return float(v)
            except Exception:
                return None
        def _extract_server_time(payload: Any) -> float:
            if isinstance(payload, dict):
                for k in ("server_time", "serverTime", "time", "timestamp", "ts", "t"):
                    if k in payload:
                        v = _to_unix_seconds(payload.get(k))
                        if v:
                            return v
                for k in ("meta", "metadata", "result", "data"):
                    if k in payload and isinstance(payload.get(k), dict):
                        v = _extract_server_time(payload.get(k))
                        if v:
                            return v
            return now
        def _extract_ticker_rows(payload: Any) -> List[dict]:
            if isinstance(payload, list):
                return [x for x in payload if isinstance(x, dict)]
            if not isinstance(payload, dict):
                return []
            for k in ("tickers", "data", "result", "results", "items", "rows", "symbols", "markets", "pairs"):
                v = payload.get(k)
                if isinstance(v, list):
                    return [x for x in v if isinstance(x, dict)]
                if isinstance(v, dict):
                    vv = v.get("tickers") or v.get("items") or v.get("rows") or v.get("symbols") or v.get("markets") or v.get("pairs")
                    if isinstance(vv, list):
                        return [x for x in vv if isinstance(x, dict)]
                    if isinstance(vv, dict):
                        if len(vv) >= 5 and all(isinstance(_v, dict) for _v in vv.values()):
                            rows = []
                            for _sym, _row in vv.items():
                                if not isinstance(_sym, str) or not isinstance(_row, dict):
                                    continue
                                rr = dict(_row)
                                rr.setdefault("symbol", _sym)
                                rows.append(rr)
                            if rows:
                                return rows
            if all(isinstance(v, dict) for v in payload.values()) and any(isinstance(k, str) for k in payload.keys()):
                if len(payload) >= 10:
                    rows = []
                    for sym, row in payload.items():
                        if not isinstance(row, dict):
                            continue
                        if "symbol" not in row and isinstance(sym, str):
                            row = dict(row)
                            row["symbol"] = sym
                        rows.append(row)
                    return rows
            return []
        for ep in endpoints:
            try:
                tmo = float(_env_float("TICKERS_REQ_TIMEOUT", _env_float("BATCH_TICKERS_TIMEOUT_SEC", 6.5)) or 5.0)
                payload = await asyncio.wait_for(self.request("GET", ep, auth=False, params=None), timeout=tmo)
                server_time = _extract_server_time(payload)
                rows = _extract_ticker_rows(payload)
                by_symbol: Dict[str, dict] = {}
                for r in rows:
                    sym = r.get("symbol") or r.get("name") or r.get("market") or r.get("pair") or r.get("sym") or r.get("s")
                    if not sym:
                        continue
                    sym = _canon_symbol(sym)
                    rr = dict(r)
                    rr["symbol"] = sym
                    by_symbol[sym] = rr
                if by_symbol:
                    snap = {"server_time": server_time, "tickers": rows, "by_symbol": by_symbol}
                    try:
                        self._last_all_tickers_snapshot = snap
                    except Exception:
                        pass
                    try:
                        self.last_update_time = time.time()
                    except Exception:
                        pass
                    return snap
            except Exception as e:
                last_err = e
        try:
            payload = await self.get_symbols()
            server_time = _extract_server_time(payload)
            rows = _extract_ticker_rows(payload) or []
            by_symbol: Dict[str, dict] = {}
            for r in rows:
                sym = r.get("symbol") or r.get("name") or r.get("market") or r.get("pair") or r.get("sym") or r.get("s")
                if not sym:
                    continue
                sym = _canon_symbol(sym)
                rr = dict(r)
                rr["symbol"] = sym
                by_symbol[sym] = rr
            snap = {"server_time": server_time, "tickers": rows, "by_symbol": by_symbol}
            try:
                self._last_all_tickers_snapshot = snap
            except Exception:
                pass
            try:
                self.last_update_time = time.time()
            except Exception:
                pass
            return snap
        except Exception:
            if last_err:
                raise last_err
            return {"server_time": now, "tickers": [], "by_symbol": {}}
    async def get_all_tickers_optimized(self) -> dict:
        'Fetch tickers with a sanity pass to ensure priced rows.'
        now = time.time()
        snap = await self.get_all_tickers()
        def _px_from_row(row: Any) -> float:
            try:
                if isinstance(row, dict) and isinstance(row.get("raw"), dict):
                    row = row.get("raw")
                if not isinstance(row, dict):
                    return 0.0
                for k in (
                    "mid", "mark", "markPrice", "last", "last_price", "lastPrice", "last_trade_price", "lastTradePrice",
                    "price", "close", "closePrice", "c", "p", "rate", "value", "latest", "ltp", "tradePrice",
                ):
                    v = _safe_float(row.get(k), 0.0)
                    if v and float(v) > 0.0:
                        return float(v)
                bid = _safe_float(row.get("bid", row.get("bestBid", row.get("bidPrice", row.get("buy", row.get("b", 0.0))))), 0.0) or 0.0
                ask = _safe_float(row.get("ask", row.get("bestAsk", row.get("askPrice", row.get("sell", row.get("a", 0.0))))), 0.0) or 0.0
                if bid > 0.0 and ask > 0.0:
                    return float(bid + ask) / 2.0
                if bid > 0.0:
                    return float(bid)
                if ask > 0.0:
                    return float(ask)
            except Exception:
                pass
            return 0.0
        def _priced_count(s: Any) -> int:
            if not isinstance(s, dict):
                return 0
            by = s.get("by_symbol") if isinstance(s.get("by_symbol"), dict) else None
            if not isinstance(by, dict):
                by = s if (len(s) >= 5 and all(isinstance(v, dict) for v in s.values())) else {}
            cnt = 0
            try:
                for _k, _v in (by or {}).items():
                    if isinstance(_v, dict) and _px_from_row(_v) > 0.0:
                        cnt += 1
                        if cnt >= 12:
                            break
            except Exception:
                return cnt
            return cnt
        try:
            min_ok = int(_env_int("TICKERS_MIN_PRICED", 3) or 3)
        except Exception:
            min_ok = 3
        min_ok = max(1, min(12, int(min_ok)))
        need_hydrate = (_priced_count(snap) < min_ok)
        if need_hydrate:
            mkt: Any = None
            try:
                mkt = await self.get_market_snapshot()
            except Exception:
                mkt = None
            if isinstance(mkt, dict) and mkt:
                try:
                    snap_d = dict(snap) if isinstance(snap, dict) else {"server_time": now, "tickers": [], "by_symbol": {}}
                except Exception:
                    snap_d = {"server_time": now, "tickers": [], "by_symbol": {}}
                by0 = snap_d.get("by_symbol") if isinstance(snap_d.get("by_symbol"), dict) else {}
                if not isinstance(by0, dict):
                    by0 = {}
                merged_by: Dict[str, dict] = { _canon_symbol(k): (dict(v) if isinstance(v, dict) else {"symbol": _canon_symbol(k), "value": v})
                                               for k, v in (by0 or {}).items()
                                               if isinstance(k, str) }
                numeric_keys = {
                    "mid", "mark", "markPrice", "last", "last_price", "lastPrice", "price", "close", "closePrice",
                    "bid", "bestBid", "bidPrice", "buy", "b", "ask", "bestAsk", "askPrice", "sell", "a",
                    "volume", "vol", "value", "turnover", "quoteVolume", "q",
                }
                for k, v in mkt.items():
                    cs = _canon_symbol(k)
                    if not cs:
                        continue
                    src = dict(v) if isinstance(v, dict) else {"symbol": cs, "value": v}
                    src.setdefault("symbol", cs)
                    dst0 = merged_by.get(cs)
                    dst = dict(dst0) if isinstance(dst0, dict) else {"symbol": cs}
                    dst.setdefault("symbol", cs)
                    for kk, vv in src.items():
                        if kk not in dst or dst.get(kk) is None or dst.get(kk) == "":
                            dst[kk] = vv
                            continue
                        if kk in numeric_keys:
                            dv = _safe_float(dst.get(kk), 0.0) or 0.0
                            sv = _safe_float(vv, 0.0) or 0.0
                            if dv <= 0.0 and sv > 0.0:
                                dst[kk] = vv
                    try:
                        mid0 = _safe_float(dst.get("mid"), 0.0) or 0.0
                        if mid0 <= 0.0:
                            bid = _safe_float(dst.get("bid", dst.get("bestBid", dst.get("bidPrice", dst.get("buy", dst.get("b"))))), 0.0) or 0.0
                            ask = _safe_float(dst.get("ask", dst.get("bestAsk", dst.get("askPrice", dst.get("sell", dst.get("a"))))), 0.0) or 0.0
                            if bid > 0.0 and ask > 0.0:
                                dst["mid"] = (float(bid) + float(ask)) / 2.0
                    except Exception:
                        pass
                    try:
                        px = _px_from_row(dst)
                        if px > 0.0:
                            dst.setdefault("last", float(px))
                    except Exception:
                        pass
                    merged_by[cs] = dst
                snap_d["by_symbol"] = merged_by
                try:
                    snap_d["tickers"] = list(merged_by.values())
                except Exception:
                    snap_d["tickers"] = []
                try:
                    st = snap_d.get("server_time", now)
                    st_s = float(ClockArbiter._epoch_to_seconds(st))
                    if (not math.isfinite(st_s)) or st_s <= 0.0:
                        snap_d["server_time"] = now
                except Exception:
                    snap_d["server_time"] = now
                snap = snap_d
        try:
            self._last_all_tickers_snapshot = snap
        except Exception:
            pass
        try:
            self.last_update_time = float(time.time())
        except Exception:
            pass
        return snap
    def get_current_age(self, now: Optional[float] = None) -> float:
        now_f = float(time.time() if now is None else now)
        snap = getattr(self, "_last_all_tickers_snapshot", None)
        if isinstance(snap, dict):
            st = snap.get("server_time")
            if st is not None:
                try:
                    st_s = float(ClockArbiter._epoch_to_seconds(st))
                    if st_s > 0.0 and math.isfinite(st_s):
                        return abs(now_f - st_s)
                except Exception:
                    pass
        return float("inf")
    @staticmethod
    def _as_payload_number(x) -> str:
        try:
            if x is None:
                return "0"
            if isinstance(x, bool):
                return "1" if x else "0"
            if isinstance(x, int):
                return str(int(x))
            if isinstance(x, float):
                s = ("%.12f" % float(x)).rstrip("0").rstrip(".")
                return s if s else "0"
            s = str(x).strip()
            if not s:
                return "0"
            try:
                s = s.translate(getattr(ExchangeClient, "_PERSIAN_DIGITS"))
            except Exception:
                pass
            s = s.replace(",", "")
            return s
        except Exception:
            return str(x)
    @staticmethod
    def _norm_side(side: str) -> str:
        s = str(side or "").strip().lower()
        if s in ("buy", "b", "long"):
            return "buy"
        if s in ("sell", "s", "short"):
            return "sell"
        return s or "buy"
    def _is_arzplus(self) -> bool:
        try:
            return "arzplus" in str(getattr(self.cfg, "base_url", "") or "").lower()
        except Exception:
            return False
    async def _arzplus_market_snapshot(self) -> dict:
        'ArzPlus public market snapshot.'
        now = float(time.time())
        last_err: Optional[Exception] = None
        endpoints = (
            "/market/symbols/",
            "/market/symbols",
            "/market/stats",
            "/market/stats/",
            "/market/summary",
            "/market/summary/",
            "/market/tickers",
            "/market/tickers/",
        )
        for ep in endpoints:
            try:
                tmo = float(_env_float("TICKERS_REQ_TIMEOUT", _env_float("BATCH_TICKERS_TIMEOUT_SEC", 6.5)) or 6.0)
                payload = await asyncio.wait_for(self.request("GET", ep, auth=False, params=None), timeout=tmo)
            except Exception as e:
                last_err = e
                continue
            if isinstance(payload, dict):
                for k in ("data", "result"):
                    if k in payload and isinstance(payload.get(k), (dict, list)):
                        payload = payload.get(k)
                        break
            rows: List[dict] = []
            by_symbol: Dict[str, dict] = {}
            if isinstance(payload, list):
                rows = [r for r in payload if isinstance(r, dict)]
            elif isinstance(payload, dict):
                if isinstance(payload.get("results"), list):
                    rows = [r for r in payload.get("results") if isinstance(r, dict)]
                else:
                    ok = True
                    for v in payload.values():
                        if v is None:
                            continue
                        if not isinstance(v, dict):
                            ok = False
                            break
                    if ok:
                        for k, v in payload.items():
                            s = _canon_symbol(k)
                            if s:
                                by_symbol[s] = dict(v or {})
                        rows = []
                    else:
                        rows = []
            if rows:
                for r in rows:
                    sym_raw = r.get("symbol") or r.get("name") or r.get("market") or r.get("pair") or r.get("code")
                    s = _canon_symbol(sym_raw)
                    if not s:
                        continue
                    by_symbol[s] = dict(r)
            if by_symbol:
                for s, info in list(by_symbol.items()):
                    if not isinstance(info, dict):
                        by_symbol.pop(s, None)
                        continue
                    p = _safe_float(
                        info.get("last") or info.get("price") or info.get("close") or info.get("last_price") or info.get("lastPrice"),
                        default=0.0, translate_digits=True, allow_percent=False, finite=True, na_values=True, strip=True
                    ) or 0.0
                    if p and (info.get("price") in (None, "", 0, "0")):
                        info["price"] = p
                    if p and (info.get("last") in (None, "", 0, "0")):
                        info["last"] = p
                    chp = info.get("change_percent") or info.get("changePercent") or info.get("percent") or info.get("change_pct")
                    chp_f = _safe_float(chp, default=None, translate_digits=False, allow_percent=True, finite=True, na_values=True, strip=True)
                    if chp_f is not None:
                        if abs(chp_f) <= 1.0 and abs(chp_f) > 0:
                            chp_f = chp_f * 100.0
                        info["change_percent"] = chp_f
                    vol = info.get("quote_volume") or info.get("quoteVolume") or info.get("base_volume") or info.get("baseVolume") or info.get("volume")
                    vol_f = _safe_float(vol, default=0.0, translate_digits=True, allow_percent=False, finite=True, na_values=True, strip=True) or 0.0
                    info["volume"] = vol_f
                    by_symbol[s] = info
                try:
                    self._last_market_stats_snapshot = dict(by_symbol)
                except Exception:
                    pass
                try:
                    self.last_update_time = now
                except Exception:
                    pass
                return by_symbol
        if last_err:
            raise last_err
        return {}
    async def _arzplus_symbols_meta(self, *, base_asset: Optional[str] = None, asset: Optional[str] = None) -> List[dict]:
        'Fetch ArzPlus symbols/markets list.'
        last_err: Optional[Exception] = None
        payload: Any = None
        try:
            payload = await self.request("GET", "/market/symbols/", auth=False, params=None)
        except Exception as e:
            last_err = e
        if payload is None and (base_asset or asset):
            variants: List[Dict[str, Any]] = []
            if base_asset:
                q = str(base_asset).upper()
                variants.extend([
                    {"base_asset": q},
                    {"quote_asset": q},
                    {"baseAsset": q},
                    {"quoteAsset": q},
                    {"quote": q},
                ])
            if asset:
                a = str(asset).upper()
                variants.extend([
                    {"asset": a},
                    {"base": a},
                    {"base_asset": a},
                    {"baseAsset": a},
                ])
            for params in variants:
                try:
                    payload = await self.request("GET", "/market/symbols/", auth=False, params=params)
                    break
                except Exception as e:
                    last_err = e
                    continue
        if payload is None:
            if last_err:
                raise last_err
            return []
        rows: List[dict] = []
        if isinstance(payload, list):
            rows = [x for x in payload if isinstance(x, dict)]
        elif isinstance(payload, dict):
            for k in ("results", "data", "items", "rows", "symbols", "markets"):
                v = payload.get(k)
                if isinstance(v, list):
                    rows = [x for x in v if isinstance(x, dict)]
                    break
        return rows
    async def _arzplus_symbol_stats(self, symbol: str) -> dict:
        q = str(getattr(self.cfg, "quote", "") or "").upper().strip()
        sym = _canon_pair(symbol, default_quote=q)
        last_err: Optional[Exception] = None
        for ep in (f"/market/symbols/{sym}", f"/market/symbols/{sym}/"):
            try:
                payload = await self.request("GET", ep, auth=False, params=None)
                if isinstance(payload, dict):
                    d = payload.get("data")
                    if isinstance(d, dict) and d:
                        return d
                    r = payload.get("result")
                    if isinstance(r, dict) and r:
                        return r
                return payload if isinstance(payload, dict) else {}
            except Exception as e:
                last_err = e
                continue
        if last_err:
            raise last_err
        return {}

    ################################################################################################
    # REPAIR CANDIDATE INSERTION - REVIEW BEFORE APPLYING
    # These methods were extracted from accidental nested/top-level blocks.
    # Generated by s43_repair_candidate.py. Do not trust blindly.
    ################################################################################################

    # ---- repaired candidate method: get_market_snapshot from lines 2719-2852 ----
    async def get_market_snapshot(self) -> dict:
        now = time.time()
        last_err: Optional[Exception] = None
        if self._is_arzplus():
            try:
                snap = await self._arzplus_market_snapshot()
                by = snap.get("by_symbol") if isinstance(snap, dict) else None
                if not isinstance(by, dict):
                    by = snap if isinstance(snap, dict) else {}
                if isinstance(by, dict):
                    try:
                        self.last_update_time = now
                    except Exception:
                        pass
                    try:
                        self._last_market_stats_snapshot = by
                    except Exception:
                        pass
                    return by
            except Exception as e:
                last_err = e
        endpoints = ("/market/stats", "/market/stats/")
        for ep in endpoints:
            try:
                tmo = float(_env_float("TICKERS_REQ_TIMEOUT", _env_float("BATCH_TICKERS_TIMEOUT_SEC", 6.5)) or 5.0)
                payload = await asyncio.wait_for(self.request("GET", ep, auth=False, params=None), timeout=tmo)
                stats: Optional[dict] = None
                rows_list: Optional[List[dict]] = None
                if isinstance(payload, list):
                    rows_list = [x for x in payload if isinstance(x, dict)]
                elif isinstance(payload, dict):
                    for kk in ("data", "result", "results", "items", "rows", "tickers", "markets", "pairs", "symbols"):
                        vv = payload.get(kk)
                        if isinstance(vv, list):
                            rows_list = [x for x in vv if isinstance(x, dict)]
                            break
                        if isinstance(vv, dict):
                            for kk2 in ("data", "items", "rows", "tickers", "markets", "pairs", "symbols"):
                                vv2 = vv.get(kk2)
                                if isinstance(vv2, list):
                                    rows_list = [x for x in vv2 if isinstance(x, dict)]
                                    break
                            if rows_list is not None:
                                break
                if rows_list:
                    stats = {}
                    for r in rows_list:
                        sym1 = r.get("symbol") or r.get("name") or r.get("market") or r.get("pair") or r.get("sym") or r.get("s")
                        if not sym1:
                            continue
                        cs = _canon_symbol(sym1)
                        if not cs:
                            continue
                        rr = dict(r)
                        rr.setdefault("symbol", cs)
                        stats[cs] = rr
                if isinstance(payload, dict):
                    if isinstance(payload.get("stats"), dict):
                        stats = payload.get("stats")
                    elif isinstance(payload.get("data"), dict) and isinstance(payload["data"].get("stats"), dict):
                        stats = payload["data"]["stats"]
                    elif isinstance(payload.get("result"), dict) and isinstance(payload["result"].get("stats"), dict):
                        stats = payload["result"]["stats"]
                    elif all(isinstance(v, dict) for v in payload.values()) and len(payload) >= 10:
                        stats = payload
                if isinstance(stats, dict) and stats:
                    norm: Dict[str, dict] = {}
                    try:
                        for k0, v0 in stats.items():
                            if isinstance(v0, dict):
                                cs = _canon_symbol(v0.get("symbol", k0))
                                if not cs:
                                    continue
                                vv = dict(v0)
                                vv.setdefault("symbol", cs)
                                norm[cs] = vv
                            else:
                                cs = _canon_symbol(k0)
                                if not cs:
                                    continue
                                norm[cs] = {"symbol": cs, "value": v0}
                    except Exception:
                        norm = {}
                        for k0, v0 in (stats or {}).items():
                            cs = _canon_symbol(k0)
                            if not cs:
                                continue
                            norm[cs] = dict(v0) if isinstance(v0, dict) else {"symbol": cs, "value": v0}
                            if isinstance(norm[cs], dict):
                                norm[cs].setdefault("symbol", cs)
                    try:
                        self.last_update_time = now
                    except Exception:
                        pass
                    try:
                        self._last_market_stats_snapshot = norm
                    except Exception:
                        pass
                    return norm
            except Exception as e:
                last_err = e
        try:
            m = await self.get_all_market_stats()
            if isinstance(m, dict) and m:
                try:
                    self.last_update_time = now
                except Exception:
                    pass
                try:
                    self._last_market_stats_snapshot = m
                except Exception:
                    pass
                out: Dict[str, dict] = {}
                for k, v in m.items():
                    kk = _canon_symbol(k)
                    if isinstance(v, dict) and isinstance(v.get("raw"), dict):
                        out[kk] = v["raw"]
                    elif isinstance(v, dict):
                        out[kk] = dict(v)
                    else:
                        out[kk] = {"value": v}
                try:
                    self._last_market_stats_snapshot = out
                except Exception:
                    pass
                return out
        except Exception:
            pass
        if last_err:
            try:
                self._logger.debug("event=MARKET_STATS_FAIL err=%s", last_err)
            except Exception:
                pass
        return {}

    # ---- repaired candidate method: get_last_update_age from lines 2853-2900 ----
    def get_last_update_age(self, now: float = None) -> float:
        """Return seconds since last successful public API update.

        """
        try:
            now_epoch = float(_epoch_to_sec(time.time() if now is None else now))
        except Exception:
            now_epoch = float(time.time())
        try:
            now_mono = float(time.monotonic())
        except Exception:
            now_mono = 0.0
        try:
            ts_raw = getattr(self, "last_update_time", 0.0) or 0.0
        except Exception:
            ts_raw = 0.0
        try:
            ts_raw_f = float(ts_raw or 0.0)
        except Exception:
            ts_raw_f = 0.0
        try:
            ts_epoch = float(_epoch_to_sec(ts_raw_f))
        except Exception:
            ts_epoch = 0.0
        if ts_epoch >= 946684800.0:
            try:
                if now_epoch > 0.0 and ts_epoch > (now_epoch + 300.0):
                    return float("inf")
            except Exception:
                pass
            try:
                return max(0.0, float(now_epoch - ts_epoch))
            except Exception:
                return float("inf")
        ts_mono = ts_raw_f
        try:
            if ts_mono > 1e11:
                ts_mono = ts_mono / 1000.0
            elif ts_mono > 1e8:
                ts_mono = ts_mono / 1000.0
        except Exception:
            pass
        try:
            if ts_mono > 0.0 and now_mono > 0.0 and ts_mono <= (now_mono + 300.0):
                return max(0.0, float(now_mono - ts_mono))
        except Exception:
            pass
        return float("inf")

    # ---- repaired candidate method: get_all_market_stats from lines 2901-2992 ----
    async def get_all_market_stats(self) -> dict:
        if self._is_arzplus():
            try:
                snap = await self._arzplus_market_snapshot()
                by = snap.get("by_symbol") if isinstance(snap, dict) else None
                if not isinstance(by, dict):
                    by = snap if isinstance(snap, dict) else {}
                if isinstance(by, dict):
                    return by
            except Exception:
                pass
        last_exc: Optional[Exception] = None
        try:
            tmo = float(_env_float("MARKET_STATS_REQ_TIMEOUT", _env_float("MARKET_STATS_TIMEOUT_SEC", 5.0)) or 5.0)
        except Exception:
            tmo = 5.0
        tmo = float(max(1.5, min(20.0, tmo)))
        def _extract_map(payload: Any) -> Dict[str, dict]:
            out: Dict[str, dict] = {}
            if payload is None:
                return out
            if isinstance(payload, dict):
                for k in ("stats", "symbols", "markets", "data", "result"):
                    v = payload.get(k)
                    if isinstance(v, dict) and v:
                        payload = v
                        break
                    if isinstance(v, list) and v:
                        payload = v
                        break
                if isinstance(payload, dict):
                    if len(payload) >= 5 and all(isinstance(v, dict) for v in payload.values()):
                        for sym, row in payload.items():
                            if not isinstance(sym, str) or not isinstance(row, dict):
                                continue
                            cs = _canon_symbol(sym)
                            rr = dict(row)
                            rr.setdefault("symbol", cs)
                            out[cs] = rr
                        return out
            rows: List[dict] = []
            if isinstance(payload, list):
                rows = [x for x in payload if isinstance(x, dict)]
            elif isinstance(payload, dict):
                for k in ("rows", "items", "tickers", "symbols", "markets", "pairs"):
                    v = payload.get(k)
                    if isinstance(v, list):
                        rows = [x for x in v if isinstance(x, dict)]
                        break
            for r in rows:
                try:
                    sym = r.get("symbol") or r.get("name") or r.get("market") or r.get("pair") or r.get("sym") or r.get("s")
                    if not sym:
                        continue
                    cs = _canon_symbol(sym)
                    rr = dict(r)
                    rr["symbol"] = cs
                    out[cs] = rr
                except Exception:
                    continue
            return out
        for ep in ("/market/stats/", "/market/stats", "/market/summary/", "/market/summary", "/market/symbols/", "/market/symbols"):
            try:
                payload = await asyncio.wait_for(self.request("GET", ep, auth=False), timeout=tmo)
                m = _extract_map(payload)
                if m:
                    try:
                        self.last_update_time = time.time()
                    except Exception:
                        pass
                    return m
            except Exception as e:
                last_exc = e
        try:
            snap = await asyncio.wait_for(self.get_all_tickers(), timeout=tmo)
            if isinstance(snap, dict):
                by = snap.get("by_symbol")
                if isinstance(by, dict) and by:
                    out: Dict[str, dict] = {}
                    for k, v in by.items():
                        cs = _canon_symbol(k)
                        if isinstance(v, dict):
                            rr = dict(v)
                            rr.setdefault("symbol", cs)
                            out[cs] = rr
                    if out:
                        return out
        except Exception as e:
            last_exc = last_exc or e
        if last_exc:
            raise last_exc
        return {}

    # ---- repaired candidate method: get_trades from lines 2993-3011 ----
    async def get_trades(self, symbol: str) -> dict:
        q = str(getattr(self.cfg, "quote", "") or "").upper().strip()
        try:
            sym = _canon_pair(symbol, default_quote=q)
        except Exception:
            try:
                sym = _canon_symbol(symbol)
            except Exception:
                sym = str(symbol or "")
        last_exc: Optional[Exception] = None
        for ep in ("/market/trades/", "/market/trades"):
            try:
                return await self.request("GET", ep, params={"symbol": sym}, auth=False)
            except Exception as e:
                last_exc = e
                continue
        if last_exc:
            raise last_exc
        return {}

    # ---- repaired candidate method: get_balance from lines 3012-3065 ----
    async def get_balance(self) -> dict:
        try:
            _cls = type(self)
            _wdu = float(getattr(_cls, "_balance_disabled_until_global", 0.0) or 0.0)
        except Exception:
            _wdu = 0.0
        if _wdu > time.time():
            try:
                print(f"ISOCHK_GLOBAL_COOLDOWN phase=get_balance until={int(_wdu)} fail_count={int(getattr(type(self), '_balance_fail_count_global', 0) or 0)} token_present={bool(getattr(self, '_token', None))} auth_scheme={getattr(self, '_auth_scheme', None)} base_url={getattr(self, 'base_url', None)}", flush=True)
            except Exception:
                pass
            return {}
        try:
            _s43_debug_print(f"[AUTHDBG_GETBAL] token_present={bool(getattr(self, '_token', None))} auth_scheme={getattr(self, '_auth_scheme', None)} cache_valid={self._balance_cache_valid() if hasattr(self, '_balance_cache_valid') else 'NA'}")
            last_exc: Optional[Exception] = None
            for ep in ("/wallet/balance/", "/wallet/balance"):
                try:
                    try:
                        def _s43_mask_authdbg(v):
                            v = str(v or "")
                            if len(v) <= 0:
                                return "<EMPTY>"
                            if len(v) <= 12:
                                return v[:2] + "...len=" + str(len(v))
                            return v[:6] + "..." + v[-4:] + ":len=" + str(len(v))
                        _hp = getattr(self, "_headers_private", None) or {}
                        _authv = ""
                        try:
                            _authv = _hp.get("Authorization", "") if hasattr(_hp, "get") else ""
                        except Exception:
                            _authv = ""
                        _tok = getattr(self, "_token", "")
                        _scheme = getattr(self, "_auth_scheme", None)
                        _w = (
                            getattr(self, "wallet_name", None)
                            or getattr(self, "_wallet_name", None)
                            or getattr(self, "name", None)
                            or getattr(self, "_name", None)
                            or getattr(self, "label", None)
                            or getattr(self, "_label", None)
                            or "UNKNOWN"
                        )
                        _base = getattr(self, "base_url", None) or getattr(self, "_base_url", None) or ""
                        _s43_debug_print(
                            f"AUTHDBG_BALANCE_V1 wallet={_w} ep={ep} "
                            f"scheme={_scheme} "
                            f"token={_s43_mask_authdbg(_tok)} "
                            f"auth={_s43_mask_authdbg(_authv)} "
                            f"token_len={len(str(_tok or ''))} "
                            f"auth_len={len(str(_authv or ''))} "
                            f"base={_base}",
                            flush=True,
                        )
                    except Exception as _authdbg_e:
                        _s43_debug_print(f"AUTHDBG_BALANCE_V1_FAIL err={type(_authdbg_e).__name__}:{_authdbg_e}", flush=True)
                    return await self.request("GET", ep, auth=True)
                except Exception as e:
                    last_exc = e
                    continue
            if last_exc:
                raise last_exc
            try:
                _fc = int(getattr(type(self), "_balance_fail_count_global", 0) or 0) + 1
            except Exception:
                _fc = 1
            try:
                _du_new = time.time() + 120.0
                setattr(type(self), "_balance_fail_count_global", _fc)
                setattr(type(self), "_balance_disabled_until_global", _du_new)
            except Exception:
                pass
            try:
                print(f"ISOCHK_GLOBAL_EMPTY phase=get_balance fail_count={_fc} token_present={bool(getattr(self, '_token', None))} auth_scheme={getattr(self, '_auth_scheme', None)} base_url={getattr(self, 'base_url', None)}", flush=True)
            except Exception:
                pass
            return {}
        except Exception as e:
            try:
                _fc = int(getattr(type(self), "_balance_fail_count_global", 0) or 0) + 1
            except Exception:
                _fc = 1
            try:
                _du_new = time.time() + 120.0
                setattr(type(self), "_balance_fail_count_global", _fc)
                setattr(type(self), "_balance_disabled_until_global", _du_new)
            except Exception:
                pass
            try:
                print(f"ISOCHK_GLOBAL phase=get_balance err={type(e).__name__}:{e} fail_count={_fc} token_present={bool(getattr(self, '_token', None))} auth_scheme={getattr(self, '_auth_scheme', None)} base_url={getattr(self, 'base_url', None)}", flush=True)
            except Exception:
                pass
            return {}

    # ---- repaired candidate method: conn_check from lines 3066-3183 ----
    async def conn_check(self, *, timeout_sec: Optional[float] = None) -> Tuple[bool, float, int]:
        """Lightweight connectivity check with DNS/path double-verify (Termux / mobile networks).

        Returns: (ok, rtt_ms, http_status_code)
        Sets: self._conn_last_diag in {"OK","DNS_OR_PATH","TOTAL_DOWN","CONN_CHECK_FAIL"}
        """
        try:
            now = float(time.time())
        except Exception:
            now = float(time.time())
        try:
            ttl = float(_env_float("CONN_CHECK_TTL_SEC", 5.0) or 5.0)
        except Exception:
            ttl = 5.0
        try:
            last_ok = float(getattr(self, "_conn_last_ok_ts", 0.0) or 0.0)
        except Exception:
            last_ok = 0.0
        if last_ok > 0.0 and float(ttl) > 0.0 and (now - last_ok) <= float(ttl):
            try:
                setattr(self, "_conn_last_diag", "OK")
            except Exception:
                pass
            try:
                return True, float(getattr(self, "_conn_last_rtt_ms", 0.0) or 0.0), int(getattr(self, "_conn_last_code", 200) or 200)
            except Exception:
                return True, 0.0, 200
        try:
            tmo = float(timeout_sec if timeout_sec is not None else float(_env_float("CONN_CHECK_TIMEOUT_SEC", 2.5) or 2.5))
        except Exception:
            tmo = 2.5
        tmo = float(max(0.8, min(12.0, tmo)))
        endpoints = ("/market/symbols/", "/market/symbols", "/market/tickers/", "/market/tickers")
        last_code = 0
        last_err = ""
        dns_like = False
        def _dnsish(err: BaseException) -> bool:
            try:
                s = (str(err) or "").lower()
            except Exception:
                s = ""
            pats = (
                "name or service not known",
                "temporary failure in name resolution",
                "nodename nor servname provided",
                "gaierror",
                "dns",
                "cannot connect to host",
                "no address associated",
                "connection reset",
                "network is unreachable",
                "connect call failed",
            )
            return any(p in s for p in pats)
        async def _tcp_probe_1111(timeout: float) -> bool:
            try:
                timeout = float(max(0.4, min(4.0, timeout)))
            except Exception:
                timeout = 1.2
            try:
                r, w = await asyncio.wait_for(asyncio.open_connection("1.1.1.1", 443), timeout=timeout)
                try:
                    w.close()
                    if hasattr(w, "wait_closed"):
                        await w.wait_closed()
                except Exception:
                    pass
                return True
            except Exception:
                return False
        for ep in endpoints:
            url = self._build_url(ep)
            try:
                sess = await self._get_session()
                headers = self._build_headers(False)
                t0 = time.time()
                async with sess.request("GET", url, headers=headers, timeout=aiohttp.ClientTimeout(total=tmo)) as resp:
                    last_code = int(getattr(resp, "status", 0) or 0)
                    _ = await resp.text()
                rtt_ms = (time.time() - float(t0)) * 1000.0
                if last_code:
                    try:
                        setattr(self, "_conn_last_ok_ts", float(now))
                        setattr(self, "_conn_last_rtt_ms", float(rtt_ms))
                        setattr(self, "_conn_last_code", int(last_code))
                        setattr(self, "_conn_last_diag", "OK")
                    except Exception:
                        pass
                    if 200 <= int(last_code) < 500:
                        return True, float(rtt_ms), int(last_code)
            except Exception as e:
                last_err = str(e)
                try:
                    if _dnsish(e):
                        dns_like = True
                except Exception:
                    pass
                continue
        diag = "CONN_CHECK_FAIL"
        try:
            if dns_like or _dnsish(Exception(last_err)):
                ok_probe = await _tcp_probe_1111(timeout=min(1.6, max(0.8, tmo * 0.6)))
                diag = "DNS_OR_PATH" if ok_probe else "TOTAL_DOWN"
            else:
                ok_probe = await _tcp_probe_1111(timeout=min(1.2, max(0.6, tmo * 0.45)))
                if not ok_probe:
                    diag = "TOTAL_DOWN"
        except Exception:
            diag = "CONN_CHECK_FAIL"
        try:
            setattr(self, "_conn_last_diag", str(diag))
        except Exception:
            pass
        try:
            self._logger.debug("event=CONN_CHECK_FAIL code=%s diag=%s err=%s", str(last_code), str(diag), _short(last_err, 120))
        except Exception:
            pass
        return False, 0.0, int(last_code or 0)

    # ---- repaired candidate method: place_order from lines 3184-3335 ----
    async def place_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        cid: Optional[str] = None,
        *,
        fill_type: str = "limit",
        market: str = "spot",
        reduce_only: Optional[bool] = None,
        **kwargs: Any,
    ) -> dict:
        try:
            if _termux_env_bool("TERMUX_MODE", False):
                _termux_mark_order_activity()
        except Exception:
            pass

        # PHASE4_ORDER_GATE_MAIN
        if (not bool(getattr(self, "_dry_run", False))) and (not bool(getattr(self, "_live_trading_armed", False))):
            try:
                _gate_log = getattr(self, "_logger", None) or getattr(self, "log", None)
                if hasattr(_gate_log, "warning"):
                    _gate_log.warning(
                        "event=LIVE_TRADING_OFF_BLOCKED_ORDER sym=%s side=%s qty=%s price=%s cid=%s reason=LIVE_TRADING_IS_OFF",
                        symbol, side, amount, price, str(cid)[:40] if cid is not None else None,
                    )
            except Exception:
                pass
            return {}

        if (
            not bool(getattr(self, "_ai_live_trading_armed", False))
            and bool(getattr(getattr(self, "_cfg", getattr(self, "cfg", None)), "autonomous_ai", False))
        ):
            try:
                _gate_log = getattr(self, "_logger", None) or getattr(self, "log", None)
                if hasattr(_gate_log, "warning"):
                    _gate_log.warning(
                        "event=AI_LIVE_TRADING_OFF_BLOCKED_ORDER sym=%s side=%s qty=%s price=%s cid=%s reason=AI_LIVE_TRADING_IS_OFF",
                        symbol, side, amount, price, str(cid)[:40] if cid is not None else None,
                    )
            except Exception:
                pass
            return {}

        q = str(getattr(self.cfg, "quote", "") or "").upper().strip()
        try:
            sym = _canon_pair(symbol, default_quote=q)
        except Exception:
            try:
                sym = _canon_symbol(symbol)
            except Exception:
                sym = str(symbol or "")

        market_raw = market
        market_norm = str(market or "spot").lower().strip()
        market_aliases = {
            "spot": "spot",
            "cash": "spot",
            "future": "futures",
            "futures": "futures",
            "perp": "futures",
            "perpetual": "futures",
            "swap": "futures",
        }
        market_norm = market_aliases.get(market_norm, market_norm)
        if market_norm not in ("spot", "futures"):
            self._logger.error("Unsupported market type requested: %s -> %s", market_raw, market_norm)
            raise ValueError(f"Unsupported market type: {market_raw}")

        fill_norm = str(fill_type or "limit").lower().strip()
        fill_aliases = {
            "limit": "limit",
            "lmt": "limit",
            "market": "market",
            "mkt": "market",
        }
        fill_norm = fill_aliases.get(fill_norm, fill_norm)
        if fill_norm not in ("limit", "market"):
            self._logger.error("Unsupported fill_type requested: %s -> %s", fill_type, fill_norm)
            raise ValueError(f"Unsupported fill_type: {fill_type}")

        if fill_norm == "limit" and price is None:
            raise ValueError("Price must be specified for LIMIT orders.")

        payload: Dict[str, Any] = {
            "symbol": sym,
            "amount": self._as_payload_number(amount),
            "side": self._norm_side(side),
            "fill_type": fill_norm,
            "market": market_norm,
        }

        if price is not None:
            payload["price"] = self._as_payload_number(price)
        else:
            payload["price"] = None

        if cid:
            payload["client_id"] = str(cid)

        extra: Dict[str, Any] = dict(kwargs or {})

        if reduce_only is not None:
            extra["reduce_only"] = bool(reduce_only)

        if market_norm == "futures":
            extra["reduce_only"] = bool(extra.get("reduce_only", False))
            if "leverage" in extra and extra.get("leverage") is not None:
                try:
                    extra["leverage"] = float(extra.get("leverage"))
                except (TypeError, ValueError):
                    self._logger.warning("Invalid futures leverage ignored: %r", extra.get("leverage"))
                    extra.pop("leverage", None)
        else:
            if bool(extra.get("reduce_only", False)):
                self._logger.warning("reduce_only=True ignored for spot order.")
            extra.pop("reduce_only", None)

        for protected_key in ("symbol", "amount", "price", "side", "fill_type", "market", "client_id"):
            extra.pop(protected_key, None)

        payload.update(extra)

        try:
            if bool(_env_bool("CONN_CHECK_BEFORE_ORDER", True)):
                ok, rtt_ms, code = await self.conn_check()
                if not ok:
                    pause = float(_env_float("CONN_CHECK_PAUSE_SEC", 4.0) or 4.0)
                    diag = str(getattr(self, "_conn_last_diag", "") or "CONN_CHECK_FAIL").upper().strip()
                    if diag not in ("DNS_OR_PATH", "TOTAL_DOWN"):
                        diag = "CONN_CHECK_FAIL"
                    raise TemporaryPause(f"NET_{diag} code={int(code)}", pause_sec=pause)
        except TemporaryPause:
            raise
        except Exception as e:
            pause = float(_env_float("CONN_CHECK_PAUSE_SEC", 4.0) or 4.0)
            raise TemporaryPause(f"NET_CONN_CHECK_ERR {type(e).__name__}", pause_sec=pause)

        last_exc: Optional[Exception] = None
        for ep in ("/market/orders/", "/market/orders"):
            try:
                return await self.request("POST", ep, payload=payload, auth=True)
            except Exception as e:
                last_exc = e
                continue

        if last_exc:
            raise last_exc
        return {}

    # ---- repaired candidate method: place_limit from lines 3336-3365 ----
    async def place_limit(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        cid: Optional[str] = None,
        *,
        notional_irt: Optional[float] = None,
        market: str = "spot",
        reduce_only: Optional[bool] = None,
        leverage: Optional[Union[int, float]] = None,
        **kwargs: Any,
    ) -> dict:
        extra: Dict[str, Any] = dict(kwargs or {})
        if notional_irt is not None and "notional_irt" not in extra:
            extra["notional_irt"] = notional_irt

        return await self.place_order(
            symbol=symbol,
            side=side,
            amount=qty,
            price=price,
            cid=cid,
            fill_type="limit",
            market=market,
            reduce_only=reduce_only,
            leverage=leverage,
            **extra,
        )

    # ---- repaired candidate method: place_market from lines 3367-3395 ----
    async def place_market(
        self,
        symbol: str,
        side: str,
        qty: float,
        cid: Optional[str] = None,
        *,
        notional_irt: Optional[float] = None,
        market: str = "spot",
        reduce_only: Optional[bool] = None,
        leverage: Optional[Union[int, float]] = None,
        **kwargs: Any,
    ) -> dict:
        extra: Dict[str, Any] = dict(kwargs or {})
        if notional_irt is not None and "notional_irt" not in extra:
            extra["notional_irt"] = notional_irt

        return await self.place_order(
            symbol=symbol,
            side=side,
            amount=qty,
            price=0.0,
            cid=cid,
            fill_type="market",
            market=market,
            reduce_only=reduce_only,
            leverage=leverage,
            **extra,
        )

    # ---- repaired candidate method: cancel_all_orders from lines 3396-3459 ----
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> dict:
        payload: Dict[str, Any] = {}
        try:
            if _termux_env_bool("TERMUX_MODE", False):
                _termux_mark_order_activity()
        except Exception:
            pass
        if symbol:
            try:
                payload["symbol"] = _canon_symbol(symbol)
            except Exception:
                payload["symbol"] = str(symbol or "")
        try:
            if bool(_env_bool("CONN_CHECK_BEFORE_ORDER", True)):
                ok, rtt_ms, code = await self.conn_check()
                if not ok:
                    pause = float(_env_float("CONN_CHECK_PAUSE_SEC", 4.0) or 4.0)
                    diag = str(getattr(self, "_conn_last_diag", "") or "CONN_CHECK_FAIL").upper().strip()
                    if diag not in ("DNS_OR_PATH", "TOTAL_DOWN"):
                        diag = "CONN_CHECK_FAIL"
                    raise TemporaryPause(f"NET_{diag} code={int(code)}", pause_sec=pause)
        except TemporaryPause:
            raise
        except Exception as e:
            pause = float(_env_float("CONN_CHECK_PAUSE_SEC", 4.0) or 4.0)
            raise TemporaryPause(f"NET_CONN_CHECK_ERR {type(e).__name__}", pause_sec=pause)
        last_exc: Optional[Exception] = None
        for ep in (
            "/market/orders/cancel_all/",
            "/market/orders/cancel_all",
            "/market/orders/cancel-all/",
            "/market/orders/cancel-all",
        ):
            try:
                return await self.request("POST", ep, payload=payload or None, auth=True)
            except Exception as e:
                last_exc = e
                continue
        try:
            r = await self.list_orders(symbol=symbol, status="open", limit=200, offset=0)
            items = []
            if isinstance(r, dict):
                v = r.get("data") or r.get("orders") or r.get("items") or r.get("result") or r.get("list") or []
                if isinstance(v, list):
                    items = [o for o in v if isinstance(o, dict)]
            max_n = int(_env_int("CANCEL_ALL_FALLBACK_MAX", 40) or 40)
            max_n = max(5, min(200, max_n))
            canceled = 0
            for o in (items or [])[:max_n]:
                oid = o.get("id") or o.get("order_id") or o.get("orderId")
                if oid is None:
                    continue
                try:
                    await self.cancel_order(oid)
                    canceled += 1
                except Exception as e:
                    last_exc = e
                    continue
            return {"ok": True, "canceled": int(canceled), "fallback": True}
        except Exception as e:
            last_exc = e
        if last_exc:
            raise last_exc
        return {"ok": False}

    # ---- repaired candidate method: list_orders from lines 3460-3512 ----
    async def list_orders(self, symbol: str = None, status: str = None, limit: int = 50, offset: int = 0) -> dict:
        base_params: Dict[str, Any] = {}
        is_arz = _is_arzplus_client(self)
        if symbol:
            try:
                q = str(getattr(self.cfg, "quote", "") or "").upper().strip(); base_params["symbol"] = _canon_pair(symbol, default_quote=q)
            except Exception:
                base_params["symbol"] = str(symbol)
        if not is_arz:
            try:
                base_params["limit"] = int(limit) if limit is not None else 50
            except Exception:
                base_params["limit"] = 50
            try:
                base_params["offset"] = int(offset) if offset is not None else 0
            except Exception:
                base_params["offset"] = 0
        st = None
        try:
            st = str(status).strip().lower() if status is not None else None
        except Exception:
            st = None
        if self._is_arzplus() and st in ("open", "opened", "active", "pending"):
            st = "new"
        eps: List[str] = ["/market/orders/", "/market/orders"]
        if st in ("open", "opened", "active", "pending"):
            eps.extend([
                "/market/orders/open/",
                "/market/orders/open",
                "/market/open_orders/",
                "/market/open_orders",
            ])
        param_variants: List[Dict[str, Any]] = []
        if st:
            param_variants.append({"status": st})
            param_variants.append({"state": st})
        else:
            param_variants.append({})
        last_err = None
        for ep in eps:
            for pv in param_variants:
                params = dict(base_params)
                try:
                    params.update(pv or {})
                except Exception:
                    pass
                try:
                    return await self.request("GET", ep, auth=True, params=(params or None))
                except Exception as e:
                    last_err = e
        if last_err:
            raise last_err
        return {}

    # ---- repaired candidate method: cancel_order from lines 3513-3557 ----
    async def cancel_order(self, order_id) -> dict:
        oid = order_id
        try:
            oid = int(order_id)
        except Exception:
            oid = str(order_id)
        payload: Dict[str, Any] = {"order_id": oid, "id": oid}
        try:
            if _termux_env_bool("TERMUX_MODE", False):
                _termux_mark_order_activity()
        except Exception:
            pass
        try:
            if bool(_env_bool("CONN_CHECK_BEFORE_ORDER", True)):
                ok, rtt_ms, code = await self.conn_check()
                if not ok:
                    pause = float(_env_float("CONN_CHECK_PAUSE_SEC", 4.0) or 4.0)
                    diag = str(getattr(self, "_conn_last_diag", "") or "CONN_CHECK_FAIL").upper().strip()
                    if diag not in ("DNS_OR_PATH", "TOTAL_DOWN"):
                        diag = "CONN_CHECK_FAIL"
                    raise TemporaryPause(f"NET_{diag} code={int(code)}", pause_sec=pause)
        except TemporaryPause:
            raise
        except Exception as e:
            pause = float(_env_float("CONN_CHECK_PAUSE_SEC", 4.0) or 4.0)
            raise TemporaryPause(f"NET_CONN_CHECK_ERR {type(e).__name__}", pause_sec=pause)
        last_err = None
        for ep in (f"/market/orders/{oid}/cancel/", f"/market/orders/{oid}/cancel"):
            try:
                return await self.request("POST", ep, payload=None, auth=True)
            except Exception as e:
                last_err = e
        for ep in (f"/market/orders/{oid}/", f"/market/orders/{oid}"):
            try:
                return await self.request("DELETE", ep, payload=None, auth=True)
            except Exception as e:
                last_err = e
        for ep in ("/market/orders/cancel/", "/market/orders/cancel"):
            try:
                return await self.request("POST", ep, payload=payload, auth=True)
            except Exception as e:
                last_err = e
        if last_err:
            raise last_err
        return {}