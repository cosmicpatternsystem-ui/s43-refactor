# Phase 26 - Observability, Runtime Diagnostics & Supportability

Date: 2026-06-16 09:31:55
Branch: master
Purpose: define a commercial-grade observability and runtime diagnostics baseline.

## Objectives
- identify existing runtime diagnostics signals
- define required logs, metrics, traces, and health checks
- document supportability requirements for production incidents
- classify observability gaps as release-blocking or follow-up
- define enforcement-ready actions for future CI/CD phases

## Required Inventory
- current logging configuration
- runtime error handling paths
- health or readiness checks
- metrics and telemetry signals
- incident triage artifacts
- support bundle requirements

## Observability Requirements
| Requirement | Status | Blocking | Notes |
|-------------|--------|----------|-------|
| structured logging baseline | pending | yes | errors must be diagnosable |
| startup diagnostics | pending | yes | version and environment signals |
| failure diagnostics | pending | yes | actionable failure context |
| health check definition | pending | yes | runtime readiness signal |
| support bundle definition | pending | yes | minimum incident artifacts |
| sensitive data redaction | pending | yes | no secrets in logs |

## Runtime Diagnostics Matrix
| Area | Scenario | Signal | Automation Status | Blocking | Notes |
|------|----------|--------|-------------------|----------|-------|
| startup | application starts | startup log | existing/unknown | yes | baseline |
| config | config loaded | config diagnostic | existing/unknown | yes | baseline |
| errors | exception occurs | error log | existing/unknown | yes | baseline |
| health | readiness check | health signal | existing/unknown | yes | baseline |
| security | secret exposure | redaction check | existing/unknown | yes | baseline |
| support | incident triage | support bundle | existing/unknown | yes | baseline |

## Exit Criteria
- observability baseline committed
- runtime diagnostics dry-run script committed
- supportability gaps documented
- quality gate executed

## Detected Observability-related Files
- analytics\log_inspector.py
- PHASE5_OBSERVABILITY_STATUS.md
- governance_log_inspection.txt
- governance_log_inspection.json
- test_status_observability_obs_format.py
- test_status_observability_failure_consistency.py
- arzplus_healthcheck.sh
- AUDIT\PHASE26_OBSERVABILITY_RUNTIME_DIAGNOSTICS_AND_SUPPORTABILITY_20260616_093154.md
- AUDIT\PHASE17_WORKER_HEALTH_MODE_INTERPRETATION_20260614.md
- tools\phase17_worker_health_check.ps1
- tools\Invoke-ObservabilityDiagnosticsDryRun.ps1
- test_status_observability_wallet_error.py
- test_status_observability_summary.py

## Keyword Hit Summary
### logging
.\CHANGE_CONTROL_LEDGER.jsonl.bak_20260614_001022:1:{"change_id":"PATCH_003A","title":"PATCH_003A_PERFORMANCE_LEDGER_BASELINE","category":"observability","phase_context":"post_phase_15","target_file":"s43.py","baseline_sha256":"15DF1D50DE507862FF69B2393A3F09DDDE5927CB0F5E55BCAF9C192FC22BE59C","final_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","compile_status":"PASS","structural_verification":"PASS","rollback_required":"NO","reapply_required":"NO","closure_status":"CLOSED","closure_artifact":"PATCH_003A_CLOSURE_REPORT.md","backup_artifact":"s43.py.PATCH_003A_VERIFIED_FINAL.bak","safety_class":"passive_logging_no_business_logic_change","notes":"Post-Phase-15 observability patch. Hooks isolated with try/except. Original return paths preserved."}
.\CHANGE_CONTROL_LEDGER.jsonl.bak_20260613_235758:1:{"change_id":"PATCH_003A","title":"PATCH_003A_PERFORMANCE_LEDGER_BASELINE","category":"observability","phase_context":"post_phase_15","target_file":"s43.py","baseline_sha256":"15DF1D50DE507862FF69B2393A3F09DDDE5927CB0F5E55BCAF9C192FC22BE59C","final_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","compile_status":"PASS","structural_verification":"PASS","rollback_required":"NO","reapply_required":"NO","closure_status":"CLOSED","closure_artifact":"PATCH_003A_CLOSURE_REPORT.md","backup_artifact":"s43.py.PATCH_003A_VERIFIED_FINAL.bak","safety_class":"passive_logging_no_business_logic_change","notes":"Post-Phase-15 observability patch. Hooks isolated with try/except. Original return paths preserved."}
.\CHANGE_CONTROL_LEDGER.jsonl:1:{"change_id":"PATCH_003A","title":"PATCH_003A_PERFORMANCE_LEDGER_BASELINE","category":"observability","phase_context":"post_phase_15","target_file":"s43.py","baseline_sha256":"15DF1D50DE507862FF69B2393A3F09DDDE5927CB0F5E55BCAF9C192FC22BE59C","final_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","compile_status":"PASS","structural_verification":"PASS","rollback_required":"NO","reapply_required":"NO","closure_status":"CLOSED","closure_artifact":"PATCH_003A_CLOSURE_REPORT.md","backup_artifact":"s43.py.PATCH_003A_VERIFIED_FINAL.bak","safety_class":"passive_logging_no_business_logic_change","notes":"Post-Phase-15 observability patch. Hooks isolated with try/except. Original return paths preserved."}
.\backups\s43_before_phase2_helpers_20260527_094432.py:52:import logging
.\backups\s43_before_phase2_helpers_20260527_094432.py:70:# Prevent broken handlers (whose emit is still logging.Handler.emit)
.\backups\s43_before_phase2_helpers_20260527_094432.py:71:# from crashing all logging with:
.\backups\s43_before_phase2_helpers_20260527_094432.py:73:if not getattr(logging, "_s43_safe_callhandlers_guard_v1", False):
.\backups\s43_before_phase2_helpers_20260527_094432.py:74:    logging._s43_safe_callhandlers_guard_v1 = True
.\backups\s43_before_phase2_helpers_20260527_094432.py:75:    _s43_orig_callHandlers = logging.Logger.callHandlers
.\backups\s43_before_phase2_helpers_20260527_094432.py:87:                        if type(hdlr).emit is logging.Handler.emit:
.\backups\s43_before_phase2_helpers_20260527_094432.py:102:                if logging.lastResort and record.levelno >= logging.lastResort.level:
.\backups\s43_before_phase2_helpers_20260527_094432.py:103:                    logging.lastResort.handle(record)
.\backups\s43_before_phase2_helpers_20260527_094432.py:107:    logging.Logger.callHandlers = _s43_safe_callHandlers
.\backups\s43_before_phase2_helpers_20260527_094432.py:358:class _DashRingHandler(logging.Handler):
.\backups\s43_before_phase2_helpers_20260527_094432.py:360:        super().__init__(level=logging.INFO)
.\backups\s43_before_phase2_helpers_20260527_094432.py:438:    def emit(self, record: logging.LogRecord) -> None:
.\backups\s43_before_phase2_helpers_20260527_094432.py:478:                if (int(lvl) >= logging.WARNING) or any(k in sm for k in keys):
.\backups\s43_before_phase2_helpers_20260527_094432.py:565:    from logging.handlers import RotatingFileHandler
.\backups\s43_before_phase2_helpers_20260527_094432.py:572:        self.log = logging.getLogger("RazTraderPlus")
.\backups\s43_before_phase2_helpers_20260527_094432.py:574:        level = logging.INFO
.\backups\s43_before_phase2_helpers_20260527_094432.py:576:        logging.getLogger().setLevel(level)
.\backups\s43_before_phase2_helpers_20260527_094432.py:579:        fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
.\backups\s43_before_phase2_helpers_20260527_094432.py:593:        ch = logging.StreamHandler(sys.stdout)
.\backups\s43_before_phase2_helpers_20260527_094432.py:596:        root = logging.getLogger()
.\backups\s43_before_phase2_helpers_20260527_094432.py:604:            self.log.info("Logging initialized | dash=%s", cfg.dash_enabled)
.\backups\s43_before_phase2_helpers_20260527_094432.py:607:                print("[SAFE-LOGGING] Logging initialized | dash=%s" % (cfg.dash_enabled,))
.\backups\s43_before_phase2_helpers_20260527_094432.py:612:                print("[SAFE-LOGGING] Logging init skipped")
.\backups\s43_before_phase2_helpers_20260527_094432.py:616:    def __init__(self, max_errors: int, cooldown_sec: float, logger: logging.Logger):
.\backups\s43_before_phase2_helpers_20260527_094432.py:769:        logger: logging.Logger,
.\backups\s43_before_phase2_helpers_20260527_094432.py:912:                self._logger = logging.getLogger("RazTraderPlus")
.\backups\s43_before_phase2_helpers_20260527_094432.py:920:                    self._logger if isinstance(getattr(self, "_logger", None), logging.Logger) else logging.getLogger("RazTraderPlus"),
.\backups\s43_before_phase2_helpers_20260527_094432.py:1038:                        if getattr(self._logger, "isEnabledFor", None) and self._logger.isEnabledFor(logging.DEBUG):
.\backups\s43_before_phase2_helpers_20260527_094432.py:1068:                        if getattr(self._logger, "isEnabledFor", None) and self._logger.isEnabledFor(logging.DEBUG):
.\backups\s43_before_phase2_helpers_20260527_094432.py:1099:        if getattr(self._logger, "isEnabledFor", None) and self._logger.isEnabledFor(logging.DEBUG):
.\backups\s43_before_phase2_helpers_20260527_094432.py:1196:            if getattr(self._logger, "isEnabledFor", None) and self._logger.isEnabledFor(logging.DEBUG):
.\backups\s43_before_phase2_helpers_20260527_094432.py:1242:                    if getattr(self._logger, "isEnabledFor", None) and self._logger.isEnabledFor(logging.DEBUG):
.\backups\s43_before_phase2_helpers_20260527_094432.py:3614:    def __init__(self, ex_public: ExchangeClient, logger: logging.Logger):
.\backups\s43_before_phase2_helpers_20260527_094432.py:3687:    def __init__(self, db_path: str, timeout_sec: float = 30.0, logger: Optional[logging.Logger] = None):
.\backups\s43_before_phase2_helpers_20260527_094432.py:3690:        self._logger = logger or logging.getLogger("TickRecorder")
.\backups\s43_before_phase2_helpers_20260527_094432.py:3905:    def __init__(self, ex: ExchangeClient, logger: logging.Logger, ttl_sec: float = 1.2, price_cache_path: str = "raz_price_cache.json"):
.\backups\s43_before_phase2_helpers_20260527_094432.py:5120:    def __init__(self, feed: "DataFeed", logger: logging.Logger):
.\backups\s43_before_phase2_helpers_20260527_094432.py:5678:    def __init__(self, cfg: BotConfig, logger: logging.Logger):
.\backups\s43_before_phase2_helpers_20260527_094432.py:5729:    def __init__(self, cfg: BotConfig, logger: logging.Logger):
.\backups\s43_before_phase2_helpers_20260527_094432.py:5834:    def __init__(self, cfg: BotConfig, logger: logging.Logger):
.\backups\s43_before_phase2_helpers_20260527_094432.py:5889:    def __init__(self, cfg: BotConfig, logger: logging.Logger):
.\backups\s43_before_phase2_helpers_20260527_094432.py:5945:    def __init__(self, cfg: BotConfig, logger: logging.Logger):
.\backups\s43_before_phase2_helpers_20260527_094432.py:5994:    def __init__(self, cfg: BotConfig, logger: logging.Logger, feed: "DataFeed"):
.\backups\s43_before_phase2_helpers_20260527_094432.py:6746:                    logging.warning("event=LOOP_LATENCY_SPIKE latency_ms=%.2f max_ms=%.2f", float(latency_ms), float(self.max_latency_ms))
.\backups\s43_before_phase2_helpers_20260527_094432.py:6750:                logging.exception("event=LOOP_MONITOR_ERR")
.\backups\s43_before_phase2_helpers_20260527_094432.py:6924:        logging.warning(
### logger
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:205:    _s43_orig_callHandlers = logging.Logger.callHandlers

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:237:    logging.Logger.callHandlers = _s43_safe_callHandlers

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:596:                _boot_logger().exception("event=PARISA_PREFLIGHT_FAIL fn=%s err=%s", fn, e)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:608:            lg = _boot_logger()

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:853:# s43 recovery: required by Logger

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:859:class Logger:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:862:        self.log = logging.getLogger("RazTraderPlus")

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:866:        logging.getLogger().setLevel(level)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:886:        root = logging.getLogger()

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:887:        if not getattr(Logger, "_configured", False):

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:892:            Logger._configured = True

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:906:    def __init__(self, max_errors: int, cooldown_sec: float, logger: logging.Logger):

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:909:        self._logger = logger

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:925:            self._logger.critical("Circuit breaker OPEN for %.0fs (err=%d): %s", self.cooldown_sec, self._errors, exc)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1059:        logger: logging.Logger,

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1111:        self._logger = logger

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1115:            logger,

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1201:            if not hasattr(self, "_logger") or getattr(self, "_logger", None) is None:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1202:                self._logger = logging.getLogger("RazTraderPlus")

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1210:                    self._logger if isinstance(getattr(self, "_logger", None), logging.Logger) else logging.getLogger("RazTraderPlus"),

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1328:                        if getattr(self._logger, "isEnabledFor", None) and self._logger.isEnabledFor(logging.DEBUG):

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1330:                                self._logger.debug("event=DEPTH_DISCOVER_TRY sym=%s ep=%s url=%s params=%s", sym0, ep, url, params)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1349:                                self._logger.info("event=DEPTH_EP_OK sym=%s ep=%s dt_ms=%.0f", sym0, ep, (time.time() - t0) * 1000.0)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1358:                        if getattr(self._logger, "isEnabledFor", None) and self._logger.isEnabledFor(logging.DEBUG):

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1360:                                self._logger.debug("event=DEPTH_DISCOVER_FAIL sym=%s ep=%s err=%s dt_ms=%.0f", sym0, ep, last_err[:160], (time.time() - t0) * 1000.0)

### loguru
.\tools\Invoke-ObservabilityDiagnosticsDryRun.ps1:19:    "loguru",
### trace
.\CHANGE_CONTROL_LEDGER.jsonl:3:{"actual_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","phase_8_promoted":false,"evidence_file_present":true,"timestamp":"20260614_003753","hash_status":"PASS","source_modified":false,"docs_written":["PHASE8_TRACEABILITY_GAP_REPORT.md","ROADMAP_TRACEABILITY_GAP_ADDENDUM_PHASE8.md"],"source_executed":false,"target":"s43.py","phase_8_status":"TRACEABILITY_GAP_NOT_EVIDENCE_CONFIRMED","expected_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","finalization_type":"gap_documentation_only","rule":"No blind promotion. Missing Phase 8 is recorded as a gap, not as completed.","event":"phase_8_traceability_gap_documented"}
.\MANIFESTS\ROLLBACK_MANIFEST_20260614_080400.json:12:    "audit_reports_path":  "E:\\+º+«+¿+º+¦¦î\\ssl\\SAFE_GITHUB_TRACEABILITY_AUDIT_20260614_071140\\reports"
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:239:import traceback

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:11702:                            "event=PRE_ORDER_TRACE wallet=%s sym=%s side=%s qty=%.12f px=%.12f notional=%.2f dry_run=%s reduce_only=%s attempt=%s cid=%s",

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:12382:def _obs_trace_deque() -> deque:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:12384:        n = int(os.getenv("OBS_TRACE_LEN", "64") or "64")

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:12509:    trace: deque = field(default_factory=_obs_trace_deque)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:15065:                        _obs_trace(w, "FAILOPEN_STATE", reason=f"orders_sync_fail_streak={streak}", meta={"streak": streak})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:15165:                _obs_trace(w, "JANITOR_CANCEL_DONE", reason=str(reason or ""), meta={"wallet": str(getattr(w,'name',''))})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:17251:            _obs_trace(w, "ORDERS_SYNC_DRY", meta={"open": int(cnt)})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:17315:            _obs_trace(w, "ORDERS_SYNC_FAIL", reason=str(err_s)[:120], meta={})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:17586:                        _obs_trace(w, ev, symbol=str(OrderJournal._order_symbol(o) or ""), reason=reason, meta={"oid": str(oid), "age": float(age)})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:17599:                        _obs_trace(w, ev, symbol=str(OrderJournal._order_symbol(o) or ""), reason=last_err[:80], meta={"oid": str(oid), "age": float(age)})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:17857:        _obs_trace(w, "ORDERS_SYNC_OK", meta={"open": int(open_cnt)})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:19944:                            _obs_trace(w, "SCAN", symbol=sym, reason="LOW_SC", meta={"score": float(getattr(sig, "score", 0.0) or 0.0)})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:21342:                        _obs_trace(w, "ORDERS_RECONCILE_UNKNOWN", reason=str(unknown), meta={})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:21350:            _obs_trace(w, "ORDERS_RECONCILE_FAIL", reason=f"{type(e).__name__}: {e}"[:120], meta={})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:21613:            _obs_trace(w, "ASSERT_ORDPOS_ORPHAN", reason="ORD>0 POS=0", meta={"oo": int(oo), "seen_age_s": float(seen_age), "oldest_s": oldest_age, "where": str(where or "")})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:21839:                    _obs_trace(w, "LOCKED_FORCE_CANCEL", reason="timeout", meta={"age_sec": age, "oo": int(oo)})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:21888:                        _obs_trace(w, "ORDERS_RECONCILE_UNKNOWN", reason=str(unknown), meta={})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:22301:                                _obs_trace(w, "SANITY_HOLD", reason=str(getattr(w, "sanity_reason", "") or "")[:120], meta={"until": until})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:23941:                _obs_trace(w, "SYSJANITOR_UNLOCK_LOCKED", reason="timeout", meta={"age_sec": age, "oo": int(oo), "pc": int(pc)})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:27198:                    dq = getattr(_w, "trace", None)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:28543:                    if ("Traceback" in _ln) or ("ERROR" in _ln) or ("CRITICAL" in _ln) or ("Exception" in _ln):

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:29195:                                    import traceback

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:29200:                            view = Panel(Text(traceback.format_exc(limit=3), style="red"), title="DASHBOARD ERROR")

### metric
.\backups\s43_before_phase2_helpers_20260527_094432.py:683:    def metrics(self) -> dict:
.\backups\s43_before_phase2_helpers_20260527_094432.py:1703:    def _update_network_metrics(self, t0: float) -> None:
.\backups\s43_before_phase2_helpers_20260527_094432.py:1904:                    self._update_network_metrics(t0)
.\backups\s43_before_phase2_helpers_20260527_094432.py:5800:                    ptype = "SYMMETRICAL_TRIANGLE"
.\backups\s43_before_phase2_helpers_20260527_094432.py:6440:        def get_asymmetric_ladder(self, current_price: float, raw_sigma: float, *, side: str = "buy",
.\backups\s43_before_phase2_helpers_20260527_094432.py:6835:class HealthMetric:
.\backups\s43_before_phase2_helpers_20260527_094432.py:6884:        self.metrics = {
.\backups\s43_before_phase2_helpers_20260527_094432.py:6885:            "latency": HealthMetric("latency_ms"),
.\backups\s43_before_phase2_helpers_20260527_094432.py:6886:            "spread": HealthMetric("spread_bps"),
.\backups\s43_before_phase2_helpers_20260527_094432.py:6887:            "volume": HealthMetric("volume_irt"),
.\backups\s43_before_phase2_helpers_20260527_094432.py:6888:            "price_change": HealthMetric("price_change_bps"),
.\backups\s43_before_phase2_helpers_20260527_094432.py:6889:            "orderbook_depth": HealthMetric("orderbook_depth")
.\backups\s43_before_phase2_helpers_20260527_094432.py:6902:                self.metrics["latency"].add(market_data["latency_ms"], ts)
.\backups\s43_before_phase2_helpers_20260527_094432.py:6904:                self.metrics["spread"].add(market_data["spread_bps"], ts)
.\backups\s43_before_phase2_helpers_20260527_094432.py:6906:                self.metrics["volume"].add(market_data["volume_irt"], ts)
.\backups\s43_before_phase2_helpers_20260527_094432.py:6913:                        self.metrics["price_change"].add(change * 10000, ts)
.\backups\s43_before_phase2_helpers_20260527_094432.py:6930:        latency_stats = self.metrics["latency"].get_stats(60)
.\backups\s43_before_phase2_helpers_20260527_094432.py:6936:        spread_stats = self.metrics["spread"].get_stats(60)
.\backups\s43_before_phase2_helpers_20260527_094432.py:6942:        volume_stats = self.metrics["volume"].get_stats(300)
.\backups\s43_before_phase2_helpers_20260527_094432.py:6969:            latency_stats = self.metrics["latency"].get_stats(30)
.\backups\s43_before_phase2_helpers_20260527_094432.py:6981:                "metrics": {}
.\backups\s43_before_phase2_helpers_20260527_094432.py:6983:            for name, metric in self.metrics.items():
.\backups\s43_before_phase2_helpers_20260527_094432.py:6984:                report["metrics"][name] = metric.get_stats(300)
.\backups\s43_before_phase2_helpers_20260527_094432.py:6990:        self.system_metrics = HealthMetric("system_health")
.\backups\s43_before_phase2_helpers_20260527_094432.py:7030:            self.system_metrics.add(avg_health_score, now)
.\backups\s43_before_phase2_helpers_20260527_094432.py:7085:class VolatilityMetrics:
.\backups\s43_before_phase2_helpers_20260527_094432.py:7114:        self.volatility_cache: Dict[str, VolatilityMetrics] = {}
.\backups\s43_before_phase2_helpers_20260527_094432.py:7120:        volatility_metrics: VolatilityMetrics,
.\backups\s43_before_phase2_helpers_20260527_094432.py:7128:                vol_scale = self._calculate_volatility_scale(volatility_metrics)
.\backups\s43_before_phase2_helpers_20260527_094432.py:7137:                capital, volatility_metrics, signal_strength
.\backups\s43_before_phase2_helpers_20260527_094432.py:7149:                volatility_metrics.atr_percent * self.target_risk_reward
.\backups\s43_before_phase2_helpers_20260527_094432.py:7167:    def _calculate_volatility_scale(self, metrics: VolatilityMetrics) -> float:
.\backups\s43_before_phase2_helpers_20260527_094432.py:7168:        if metrics.regime == VolatilityRegime.VERY_LOW:
.\backups\s43_before_phase2_helpers_20260527_094432.py:7170:        elif metrics.regime == VolatilityRegime.LOW:
.\backups\s43_before_phase2_helpers_20260527_094432.py:7172:        elif metrics.regime == VolatilityRegime.NORMAL:
.\backups\s43_before_phase2_helpers_20260527_094432.py:7174:        elif metrics.regime == VolatilityRegime.HIGH:
.\backups\s43_before_phase2_helpers_20260527_094432.py:7176:        elif metrics.regime == VolatilityRegime.VERY_HIGH:
.\backups\s43_before_phase2_helpers_20260527_094432.py:7209:        metrics: VolatilityMetrics,
.\backups\s43_before_phase2_helpers_20260527_094432.py:7213:        if metrics.is_trending:
.\backups\s43_before_phase2_helpers_20260527_094432.py:7215:        elif metrics.is_mean_reverting:
.\backups\s43_before_phase2_helpers_20260527_094432.py:7238:    def update_volatility_metrics(
.\backups\s43_before_phase2_helpers_20260527_094432.py:7244:    ) -> VolatilityMetrics:
.\backups\s43_before_phase2_helpers_20260527_094432.py:7246:            return VolatilityMetrics()
.\backups\s43_before_phase2_helpers_20260527_094432.py:7253:            return VolatilityMetrics()
.\backups\s43_before_phase2_helpers_20260527_094432.py:7281:        trend_strength, trend_consistency = self._calculate_trend_metrics(prices)
.\backups\s43_before_phase2_helpers_20260527_094432.py:7285:        metrics = VolatilityMetrics(
.\backups\s43_before_phase2_helpers_20260527_094432.py:7303:        self.volatility_cache[symbol] = metrics
.\backups\s43_before_phase2_helpers_20260527_094432.py:7304:        return metrics
.\backups\s43_before_phase2_helpers_20260527_094432.py:7316:    def _calculate_trend_metrics(self, prices: List[float]) -> Tuple[float, float]:
.\backups\s43_before_phase2_helpers_20260527_094432.py:7452:        volatility_metrics: VolatilityMetrics
### metrics
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:973:    def metrics(self) -> dict:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1993:    def _update_network_metrics(self, t0: float) -> None:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:2194:                    self._update_network_metrics(t0)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:7990:        self.metrics = {

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8008:                self.metrics["latency"].add(market_data["latency_ms"], ts)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8010:                self.metrics["spread"].add(market_data["spread_bps"], ts)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8012:                self.metrics["volume"].add(market_data["volume_irt"], ts)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8019:                        self.metrics["price_change"].add(change * 10000, ts)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8036:        latency_stats = self.metrics["latency"].get_stats(60)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8042:        spread_stats = self.metrics["spread"].get_stats(60)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8048:        volume_stats = self.metrics["volume"].get_stats(300)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8075:            latency_stats = self.metrics["latency"].get_stats(30)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8087:                "metrics": {}

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8089:            for name, metric in self.metrics.items():

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8090:                report["metrics"][name] = metric.get_stats(300)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8096:        self.system_metrics = HealthMetric("system_health")

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8136:            self.system_metrics.add(avg_health_score, now)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8191:class VolatilityMetrics:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8220:        self.volatility_cache: Dict[str, VolatilityMetrics] = {}

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8226:        volatility_metrics: VolatilityMetrics,

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8234:                vol_scale = self._calculate_volatility_scale(volatility_metrics)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8243:                capital, volatility_metrics, signal_strength

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8255:                volatility_metrics.atr_percent * self.target_risk_reward

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8273:    def _calculate_volatility_scale(self, metrics: VolatilityMetrics) -> float:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8274:        if metrics.regime == VolatilityRegime.VERY_LOW:

### health
.\arzplus_healthcheck.sh:5:LOG_FILE="./arzplus_healthcheck.log"
.\arzplus_healthcheck.sh:7:echo "Running ArzPlus token healthcheck..."
.\arzplus_healthcheck.sh:18:  echo "PASS: ArzPlus token layout is healthy"
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1755:    def _arzplus_health_check_clock(self, *, resp_headers: Dict[str, str], endpoint: str = "") -> None:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:1756:        """Health-check: compare local time with server time; warn if drift > 2s."""

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:2035:        # Health-check clock drift (warn only; no strategy impact)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:2037:            self._arzplus_health_check_clock(resp_headers=rh, endpoint=str(endpoint or ""))

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:5939:class TradeHealth:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:5967:                "health": float(_env_float("RISK_W_HEALTH", 1.20)),

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:6056:class TradeHealthController:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:6150:    ) -> TradeHealth:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:6176:            gm_max = float(_env_float("HEALTH_WD_GRACE_MAX_MULT", 1.25) or 1.25)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:6215:                return TradeHealth("HALT", 0.0, sev, reasons)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:6217:                return TradeHealth("DEGRADED", 0.45, sev, reasons)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:6218:            return TradeHealth("HALT", 0.0, sev, reasons)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:6221:            return TradeHealth("DEGRADED", 0.45, sev, reasons)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:6223:            return TradeHealth("SOFT", 0.75, sev, reasons)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:6224:        return TradeHealth("NORMAL", 1.0, sev, reasons)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:7941:class HealthMetric:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:7986:class SymbolHealthMonitor:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:7991:            "latency": HealthMetric("latency_ms"),

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:7992:            "spread": HealthMetric("spread_bps"),

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:7993:            "volume": HealthMetric("volume_irt"),
