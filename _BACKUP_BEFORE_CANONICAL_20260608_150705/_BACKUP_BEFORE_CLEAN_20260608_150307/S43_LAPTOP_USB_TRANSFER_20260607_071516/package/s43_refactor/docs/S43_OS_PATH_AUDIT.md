# S43 OS and Path Audit

Source: s43.py
Mode: observation only
S43_MODIFIED=NO

## Raw Matches

Line 22: if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
Line 243: import subprocess
Line 306: loop_interval_sec: float = field(default_factory=lambda: (_env_float("LOOP_INTERVAL_SEC", 8.0) if _env_bool("TERMUX_MODE", False) else _env_float("LOOP_INTERVAL_SEC", 2.0)))
Line 338: market_age_skip_sec: float = field(default_factory=lambda: max(0.0, _env_float("MARKET_AGE_SKIP_SEC", (6.0 if _env_bool("TERMUX_MODE", False) else 2.0))))
Line 339: market_age_sleep_sec: float = field(default_factory=lambda: max(0.0, _env_float("MARKET_AGE_SLEEP_SEC", (6.0 if _env_bool("TERMUX_MODE", False) else 2.0))))
Line 344: runtime_profile: str = field(default_factory=lambda: str(os.getenv("RUNTIME_PROFILE", ("termux" if _env_bool("TERMUX_MODE", False) else "server"))).strip().lower())
Line 533: p = Path(out_path).expanduser()
Line 537: p = Path(os.path.abspath(str(p)))
Line 539: p.parent.mkdir(parents=True, exist_ok=True)
Line 582: prev_env = {k: os.environ.get(k) for k in keys}
Line 604: cur = os.environ.get(k, "")
Line 606: os.environ[k] = v
Line 775: s = re.sub(r"Age:\s*\d+(?:\.\d+)?s", "Age:", s, flags=re.I)
Line 839: _TERMUX_BOOT_TS = time.time()
Line 840: _TERMUX_LAST_ORDER_TS = _TERMUX_BOOT_TS
Line 915: def is_open(self) -> bool:
Line 1100: if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
Line 1260: cand_env = str(os.environ.get("DEPTH_ENDPOINT_CANDIDATES", "") or "").strip()
Line 1290: probe_to = float(os.environ.get("DEPTH_DISCOVER_TIMEOUT_SEC", "3.0" if _env_bool("TERMUX_MODE", False) else "2.0") or 2.0)
Line 1475: timeout = float(os.getenv("DEPTH_REQ_TIMEOUT_SEC", "7.0" if _env_bool("TERMUX_MODE", False) else "5.0") or 5.0)
Line 1575: termux_force = bool(_env_bool("TERMUX_MODE", False))
Line 1577: termux_force = False
Line 1579: if termux_force or bool(_env_bool("DNS_FORCE_IPV4", False)):
Line 1582: fam = socket.AF_INET if termux_force else 0
Line 1942: def _raise_if_breaker_open(self) -> None:
Line 1943: if self._breaker.is_open():
Line 2181: self._raise_if_breaker_open()
Line 3114: """Lightweight connectivity check with DNS/path double-verify (Termux / mobile networks).
Line 3247: if _termux_env_bool("TERMUX_MODE", False):
Line 3248: _termux_mark_order_activity()
Line 3453: if _termux_env_bool("TERMUX_MODE", False):
Line 3454: _termux_mark_order_activity()
Line 3579: if _termux_env_bool("TERMUX_MODE", False):
Line 3580: _termux_mark_order_activity()
Line 4021: #         """Lightweight connectivity check with DNS/path double-verify (Termux / mobile networks).
Line 4161: #             if _termux_env_bool("TERMUX_MODE", False):
Line 4162: #                 _termux_mark_order_activity()
Line 4389: #             if _termux_env_bool("TERMUX_MODE", False):
Line 4390: #                 _termux_mark_order_activity()
Line 4529: #             if _termux_env_bool("TERMUX_MODE", False):
Line 4530: #                 _termux_mark_order_activity()
Line 4664: self._proc: Optional[asyncio.subprocess.Process] = None
Line 4691: script = _this_script_path()
Line 4693: self._proc = await asyncio.create_subprocess_exec( # S43_EXEC_TRACE
Line 4703: stdin=asyncio.subprocess.PIPE,
Line 4704: stdout=asyncio.subprocess.DEVNULL,
Line 4705: stderr=asyncio.subprocess.DEVNULL,
Line 4897: with open(self._price_cache_path, "r", encoding="utf-8") as f:
Line 4926: with open(self._price_cache_path, "w", encoding="utf-8") as f:
Line 5229: per_to = float(os.getenv("DEPTH_REQ_TIMEOUT_SEC", os.getenv("DEPTH_TIMEOUT_SEC", "7.0" if _env_bool("TERMUX_MODE", False) else "5.0")) or 5.0)
Line 5233: retry_max = int(os.getenv("DEPTH_RETRY_MAX", "4" if _env_bool("TERMUX_MODE", False) else "3") or 3)
Line 5242: retry_max = int(os.getenv("DEPTH_RETRY_MAX", "4" if _env_bool("TERMUX_MODE", False) else "3") or 3)
Line 5257: hard_fail_ttl = float(os.getenv("DEPTH_HARD_FAIL_TTL_SEC", "3600" if _env_bool("TERMUX_MODE", False) else "1800") or 1800.0)
Line 5360: max_age = float(_env_float("DEPTH_DISK_CACHE_MAX_AGE_SEC", (90.0 if _env_bool("TERMUX_MODE", False) else 60.0)) or 0.0)
Line 7288: if os.environ.get("ARZPLUS_LIVE_ARMED") != "YES":
Line 8727: self._schedule_half_open()
Line 8732: self._schedule_half_open()
Line 8733: def _schedule_half_open(self):
Line 9645: with open(path, "r", encoding="utf-8") as f:
Line 9664: with open(tmp, "w", encoding="utf-8") as f:
Line 9669: with open(path, "w", encoding="utf-8") as f:
Line 9883: # Enforce confidence gating for entries (uses Termux adaptive min_conf when enabled)
Line 9886: entry_thr, min_conf, _sm, _resc, _tag = _termux_adaptive_phoenix_gate(self.cfg)
Line 10959: if bool(_env_bool("TERMUX_MODE", False)):
Line 11093: with open(path, "r", encoding="utf-8") as f:
Line 11156: def can_open(
Line 11699: """Aggressive ghost/orphan order pruning (Termux-safe).
Line 11728: with open(path, "r", encoding="utf-8") as f:
Line 12007: with open(path, "w", encoding="utf-8") as f:
Line 12044: is_termux = bool(os.getenv("TERMUX_VERSION"))
Line 12046: is_termux = False
Line 12047: if not is_termux:
Line 12050: if "com.termux" in pref:
Line 12051: is_termux = True
Line 12054: if is_termux:
Line 12276: with open(p, "r", encoding="utf-8") as f:
Line 12312: d = os.path.dirname(os.path.abspath(p))
Line 12320: with open(tmp, "w", encoding="utf-8") as f:
Line 12705: if bool(_env_bool("TERMUX_MODE", False)) and bool(_env_bool("TERMUX_ALLOW_ENTRY_DEGRADED", True)):
Line 12706: return True, "ALLOW_ENTRY_DEGRADED_TERMUX"
Line 13430: _v = _s43_b2_os.environ.get(_n)
Line 13640: "armed": (os.environ.get("ARZPLUS_LIVE_ARMED") == "YES"),
Line 13641: "last_order_ts": float(_TERMUX_LAST_ORDER_TS or 0.0),
Line 13699: with open(path, "r", encoding="utf-8") as f:
Line 13708: global _TERMUX_LAST_ORDER_TS
Line 13709: _TERMUX_LAST_ORDER_TS = float(lo)
Line 14134: p = str(os.environ.get("DASH_EXPORT_PATH", "") or "").strip()
Line 14144: with open(tmp, "w", encoding="utf-8") as f:
Line 14198: d = os.path.dirname(os.path.abspath(path)) or "."
Line 14226: with open(p, "r", encoding="utf-8") as f:
Line 14342: with open(path, "rb") as rf, open(tmp, "wb") as wf:
Line 14362: d = os.path.dirname(os.path.abspath(bak)) or "."
Line 14364: fd = os.open(d, os.O_RDONLY)
Line 14436: if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
Line 14439: if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
Line 14444: if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
Line 14504: _env_tok = _s43_os.environ.get(_env_key, "") if _env_key else ""
Line 14529: if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
Line 14536: if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
Line 14539: if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
Line 14574: if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
Line 14577: if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
Line 14624: if str(__import__("os").environ.get("S43_DEBUG_PRINTS", "")).lower() in ("1", "true", "yes", "on"):
Line 14839: os.environ["LIVE_TRADING"] = "0"
Line 14840: os.environ["DRY_RUN"] = "1"
Line 14849: offline_override = str(os.environ.get("OFFLINE_REVIEW_OVERRIDE", "0")).strip() == "1"
Line 14864: os.environ["LIVE_TRADING"] = "0"
Line 14865: os.environ["DRY_RUN"] = "1"
Line 14871: os.environ["LIVE_TRADING"] = "1"
Line 14872: os.environ["DRY_RUN"] = "0"
Line 14877: os.environ["DRY_RUN"] = "1"
Line 14878: os.environ["LIVE_TRADING"] = "0"
Line 14884: os.environ["PP_SYMBOLS"] = syms
Line 14890: os.environ["WALLET_SLOTS"] = wslots.replace(" ", "")
Line 14895: os.environ["RECORD_TICKS"] = "1"
Line 14898: os.environ["RECORD_DB_PATH"] = dbp
Line 14903: os.environ["DASH"] = "1"
Line 14908: os.environ["WATCHDOG"] = "1"
Line 14914: os.environ["WALLET_CONCURRENCY"] = str(int(wc))
Line 14920: os.environ["DRY_RUN"] = "1"
Line 14921: os.environ["LIVE_TRADING"] = "0"
Line 15474: Auto-patch probe helper for Termux.
Line 15477: return {"ok": True, "tag": "termux_autopatch_stage2"}
Line 15586: termux = _env_bool("TERMUX_MODE", False)
Line 15587: use_momentum = bool(termux and _env_bool("TERMUX_MOMENTUM_SCANNER", True))
Line 15589: min_vol = float(os.environ.get("TERMUX_MIN_VOL_24H_IRT", "20000000" if use_momentum else "50000000"))
Line 15664: if termux and vol < min_vol:
Line 15666: if termux:
Line 15754: self._focus_scan_mode = "momentum_1h" if use_momentum else ("termux" if termux else "v126")
Line 15756: "event=FOCUS_UPDATED mode=%s termux=%s min_vol=%s symbols=%s",
Line 15758: termux,
Line 17048: _always = bool(_env_bool("FOCUS_SCAN_ALWAYS_ON", _env_bool("TERMUX_MODE", False)))
Line 17050: _always = bool(_env_bool("TERMUX_MODE", False))
Line 17058: interval = float(_env_float("FOCUS_SCAN_INTERVAL_SEC", (60.0 if _env_bool("TERMUX_MODE", False) else 1800.0)))
Line 17595: with open(fs_path, "r", encoding="utf-8") as f:
Line 17742: with open(fs_path, "w", encoding="utf-8") as f:
Line 17757: with open(fs_path, "w", encoding="utf-8") as f:
Line 19850: thr, minc, rescue_mult, rescue_on, rescue_tag = _termux_adaptive_phoenix_gate(self.cfg)
Line 19890: setattr(sig, "dzh_reason", f"TERMUX_{(rescue_tag or 'RESCUE')[:48]}")
Line 20017: _thr_tmp, _minc_tmp, _sm_tmp, _resc_on, _tag_tmp = _termux_adaptive_phoenix_gate(self.cfg)
Line 20025: setattr(sig, "dzh_reason", f"TERMUX_{str(_tag_tmp)[:48]}")
Line 22232: global TERMUX_MODE
Line 22234: TERMUX_MODE = bool(os.environ.get("TERMUX_VERSION") or os.environ.get("TERMUX_MODE") == "1" or ("com.termux" in str(os.environ.get("PREFIX", ""))))
Line 22236: TERMUX_MODE = False
Line 22516: thr_eff, _minc_eff, _szm, _resc, _tag = _termux_adaptive_phoenix_gate(self.cfg, now=time.time())
Line 22534: idle_s = max(0.0, float(time.time()) - float(_TERMUX_LAST_ORDER_TS or _TERMUX_BOOT_TS))
Line 22537: tmin = float(_env_float("TERMUX_EXEC_MIN_SEC", 0.35) or 0.35)
Line 22538: tmax = float(_env_float("TERMUX_EXEC_MAX_SEC", 1.05) or 1.05)
Line 22539: hot_mult = float(_env_float("TERMUX_EXEC_HOT_MULT", 0.70) or 0.70)
Line 22540: near_mult = float(_env_float("TERMUX_EXEC_NEAR_MULT", 0.80) or 0.80)
Line 22541: ultra = float(_env_float("TERMUX_EXEC_ULTRA_SEC", 0.5) or 0.5)
Line 22549: target = min(tmax, base * float(_env_float("TERMUX_EXEC_IDLE_MULT_60M", 1.45) or 1.45))
Line 22551: target = min(tmax, base * float(_env_float("TERMUX_EXEC_IDLE_MULT_30M", 1.35) or 1.35))
Line 22553: target = min(tmax, base * float(_env_float("TERMUX_EXEC_IDLE_MULT_10M", 1.25) or 1.25))
Line 22956: if bool(_env_bool("TERMUX_MODE", False)) and not (bool(_env_bool("HEALTH_WD_TOP8_ALLOW_STRICT", False)) and bool(_env_bool("HEALTH_WD_TOP8_ALLOW_STRICT_CONFIRM", False))):
Line 22957: top8_warn = max(float(top8_warn), float(_env_float("TERMUX_TOP8_WARN_MIN_SEC", 20.0) or 20.0))
Line 22958: top8_crit = max(float(top8_crit), float(_env_float("TERMUX_TOP8_CRIT_MIN_SEC", 45.0) or 45.0))
Line 22962: if bool(_env_bool("TERMUX_MODE", False)) and not (bool(_env_bool("HEALTH_WD_ALLOW_STRICT", False)) and bool(_env_bool("HEALTH_WD_ALLOW_STRICT_CONFIRM", False))):
Line 22963: mkt_warn = max(float(mkt_warn), float(_env_float("TERMUX_MKT_WARN_MIN_SEC", 10.0) or 10.0))
Line 22964: mkt_crit = max(float(mkt_crit), float(_env_float("TERMUX_MKT_CRIT_MIN_SEC", 40.0) or 40.0), float(mkt_warn) + 3.0)
Line 22965: radar_warn = max(float(radar_warn), float(_env_float("TERMUX_RADAR_WARN_MIN_SEC", 30.0) or 30.0))
Line 22966: radar_crit = max(float(radar_crit), float(_env_float("TERMUX_RADAR_CRIT_MIN_SEC", 120.0) or 120.0), float(radar_warn) + 8.0)
Line 22967: api_warn = max(float(api_warn), float(_env_float("TERMUX_API_WARN_MIN_SEC", 6.0) or 6.0))
Line 22968: api_crit = max(float(api_crit), float(_env_float("TERMUX_API_CRIT_MIN_SEC", 25.0) or 25.0), float(api_warn) + 3.0)
Line 22969: top8_warn = max(float(top8_warn), float(_env_float("TERMUX_TOP8_WARN_MIN_SEC", 90.0) or 90.0))
Line 22970: top8_crit = max(float(top8_crit), float(_env_float("TERMUX_TOP8_CRIT_MIN_SEC", 300.0) or 300.0), float(top8_warn) + 10.0)
Line 23336: if bool(_env_bool("TERMUX_MODE", False)) and not bool(_env_bool("HEALTH_WD_TOP8_FORCE_EXEC", False)):
Line 23947: base = os.path.dirname(os.path.abspath(__file__))
Line 24373: Native replacement for the old subprocess '-c' embedded script.
Line 24535: os.environ["PP110_WATCHDOG"] = "1"
Line 24795: os.environ.setdefault("TERM", os.environ.get("TERM", "xterm-256color"))
Line 24927: _DASH_ASCII = bool(_env_bool("DASH_ASCII", True) or _env_bool("TERMUX_MODE", False))
Line 24944: with open(path, "rb") as f:
Line 27803: dc_thr = float(_env_float("DEPTH_DISK_CACHE_MAX_AGE_SEC", (8.0 if _env_bool("TERMUX_MODE", False) else 4.0)) or 0.0)
Line 28170: if bool(br.is_open()):
Line 28755: if bool(_env_bool("TERMUX_MODE", False)) and bool(_env_bool("TERMUX_ALLOW_ENTRY_DEGRADED", True)):
Line 28763: entry_reason = "DEG_TERMUX"
Line 30163: os.environ.pop("PHOENIX_ALLOW_SPOT_READY", None)
Line 30166: os.environ["PHOENIX_ALLOW_SPOT_READY"] = "1"
Line 30199: """Read float from environment safely."""
Line 30217: """Read string from environment safely."""
Line 30245: """Read integer from environment safely."""
Line 30335: value = os.environ.get(name)
Line 30346: os.environ.get("S43_WALLET_REGISTRY_PATH")
Line 30347: or os.environ.get("S43_WALLET_REGISTRY_JSON")
Line 30354: with open(path, "r", encoding="utf-8") as f:
Line 30514: directory = os.path.dirname(os.path.abspath(path)) or "."
Line 30521: with open(tmp_path, "w", encoding="utf-8") as f:
