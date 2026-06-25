# Phase 14 Report Completion

Generated: 2026-06-25T16:49:16+03:30

## Verdict

Report generation: PASS

## Evidence

.\ASO_MANIFEST.json:9:        "Automated Compliance Reporting",
.\analytics\reporter.py:149:def print_report(summary):
.\analytics\reporter.py:151:    print("GOVERNANCE ANALYTICS REPORT")
.\analytics\reporter.py:236:    print_report(summary)
.\analytics\reporter.py:240:        print(f"[OK] JSON report written to: {json_output}")
.\analytics\reporter.py:244:        print(f"[OK] CSV report written to: {csv_output}")
.\CHANGE_CONTROL_LEDGER.jsonl:1:{"change_id":"PATCH_003A","title":"PATCH_003A_PERFORMANCE_LEDGER_BASELINE","category":"observability","phase_context":"post_phase_15","target_file":"s43.py","baseline_sha256":"15DF1D50DE507862FF69B2393A3F09DDDE5927CB0F5E55BCAF9C192FC22BE59C","final_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","compile_status":"PASS","structural_verification":"PASS","rollback_required":"NO","reapply_required":"NO","closure_status":"CLOSED","closure_artifact":"PATCH_003A_CLOSURE_REPORT.md","backup_artifact":"s43.py.PATCH_003A_VERIFIED_FINAL.bak","safety_class":"passive_logging_no_business_logic_change","notes":"Post-Phase-15 observability patch. Hooks isolated with try/except. Original return paths preserved."}
.\CHANGE_CONTROL_LEDGER.jsonl:2:{"ts":"2026-06-13T20:40:22Z","type":"discovery_audit_and_documentation_normalization","target":"s43.py","summary":"Phase 16 and Phase 17 markers confirmed in active codebase; ROADMAP_vNEXT.md normalized; no rollback to Phase 15.","baseline":{"expected_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","actual_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","sha256_status":"MATCH","compile_status":"py_compile PASS"},"evidence":{"phase16":{"present":true,"start_line":6549,"end_line":6657,"start_marker":"# --- PHASE 16: GOVERNANCE ENFORCEMENT ---","end_marker":"# --- END PHASE 16 ---"},"phase17":{"present":true,"start_line":21,"end_line":25,"start_marker":"# === PHASE 17 AUDIT FOUNDATION IMPORT ===","end_marker":"# === END PHASE 17 AUDIT FOUNDATION IMPORT ==="},"report":"PHASE_16_17_DISCOVERY_REPORT.txt","roadmap":"ROADMAP_vNEXT.md"},"decision":"Continue from current baseline; do not roll back to Phase 15; perform behavioral verification before further invasive patches."}
.\CHANGE_CONTROL_LEDGER.jsonl:3:{"actual_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","phase_8_promoted":false,"evidence_file_present":true,"timestamp":"20260614_003753","hash_status":"PASS","source_modified":false,"docs_written":["PHASE8_TRACEABILITY_GAP_REPORT.md","ROADMAP_TRACEABILITY_GAP_ADDENDUM_PHASE8.md"],"source_executed":false,"target":"s43.py","phase_8_status":"TRACEABILITY_GAP_NOT_EVIDENCE_CONFIRMED","expected_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","finalization_type":"gap_documentation_only","rule":"No blind promotion. Missing Phase 8 is recorded as a gap, not as completed.","event":"phase_8_traceability_gap_documented"}
.\analytics\log_inspector.py:142:            "No valid JSON lines were detected. The reporter expects JSON Lines format: one valid JSON object per line."
.\analytics\log_inspector.py:147:            "Valid JSON exists, but no outcome-like key was found. Reporter looks for one of: outcome, decision, status, result."
.\analytics\log_inspector.py:152:            "Valid JSON exists, but no action-like key was found. Reporter looks for one of: action, event, type, operation."
.\analytics\log_inspector.py:157:            "Valid JSON exists, but no reason-like key was found. Reporter looks for one of: reason, denial_reason, message, error, including inside details."
.\analytics\log_inspector.py:162:            "Mixed valid and invalid lines detected. Consider cleaning malformed audit entries or making the reporter more tolerant."
.\analytics\log_inspector.py:167:            "Log format looks usable for analytics. If reporter still shows zero transactions, verify that it is reading the same log file path."
.\analytics\log_inspector.py:173:def write_json_report(result, output_file):
.\analytics\log_inspector.py:179:def write_text_report(result, output_file):
.\analytics\log_inspector.py:184:    lines.append("GOVERNANCE AUDIT LOG INSPECTION REPORT")
.\analytics\log_inspector.py:244:def print_console_report(result):
.\analytics\log_inspector.py:246:    print("GOVERNANCE AUDIT LOG INSPECTION REPORT")
.\analytics\log_inspector.py:308:    print_console_report(result)
.\analytics\log_inspector.py:309:    write_json_report(result, json_out)
.\analytics\log_inspector.py:310:    write_text_report(result, text_out)
.\analytics\log_inspector.py:311:    print(f"[OK] JSON inspection report written to: {json_out}")
.\analytics\log_inspector.py:312:    print(f"[OK] Text inspection report written to: {text_out}")
.\CHANGE_CONTROL_LEDGER.jsonl.bak_20260614_001022:1:{"change_id":"PATCH_003A","title":"PATCH_003A_PERFORMANCE_LEDGER_BASELINE","category":"observability","phase_context":"post_phase_15","target_file":"s43.py","baseline_sha256":"15DF1D50DE507862FF69B2393A3F09DDDE5927CB0F5E55BCAF9C192FC22BE59C","final_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","compile_status":"PASS","structural_verification":"PASS","rollback_required":"NO","reapply_required":"NO","closure_status":"CLOSED","closure_artifact":"PATCH_003A_CLOSURE_REPORT.md","backup_artifact":"s43.py.PATCH_003A_VERIFIED_FINAL.bak","safety_class":"passive_logging_no_business_logic_change","notes":"Post-Phase-15 observability patch. Hooks isolated with try/except. Original return paths preserved."}
.\CHANGE_CONTROL_LEDGER.jsonl.bak_20260613_235758:1:{"change_id":"PATCH_003A","title":"PATCH_003A_PERFORMANCE_LEDGER_BASELINE","category":"observability","phase_context":"post_phase_15","target_file":"s43.py","baseline_sha256":"15DF1D50DE507862FF69B2393A3F09DDDE5927CB0F5E55BCAF9C192FC22BE59C","final_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","compile_status":"PASS","structural_verification":"PASS","rollback_required":"NO","reapply_required":"NO","closure_status":"CLOSED","closure_artifact":"PATCH_003A_CLOSURE_REPORT.md","backup_artifact":"s43.py.PATCH_003A_VERIFIED_FINAL.bak","safety_class":"passive_logging_no_business_logic_change","notes":"Post-Phase-15 observability patch. Hooks isolated with try/except. Original return paths preserved."}
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\SAFETY_PROTOCOL.md:19:## [Phase 14] Completion - 2026-06-13
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\SAFETY_PROTOCOL.md:84: PATCH_003_DISCOVERY_REPORT
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\SAFETY_PROTOCOL.md:91: PATCH_006_METRICS_QUALITY_REPORTING
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\SAFETY_PROTOCOL.md:101:PATCH_003_DISCOVERY_REPORT
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\PHASE8_TRACEABILITY_GAP_REPORT.md:1:# Phase 8 Traceability Gap Report
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\PHASE8_TRACEABILITY_GAP_REPORT.md:30:The available search reports indicate that Phase 8 markers were not found across the current code, safety protocol files, legacy reference files, pasted-text files, and other available textual artifacts.
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\PHASE8_TRACEABILITY_GAP_REPORT.md:58:This report prevents blind promotion of Phase 8 while preserving the known valid baseline.
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\CHANGE_CONTROL_LEDGER.jsonl:1:{"change_id":"PATCH_003A","title":"PATCH_003A_PERFORMANCE_LEDGER_BASELINE","category":"observability","phase_context":"post_phase_15","target_file":"s43.py","baseline_sha256":"15DF1D50DE507862FF69B2393A3F09DDDE5927CB0F5E55BCAF9C192FC22BE59C","final_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","compile_status":"PASS","structural_verification":"PASS","rollback_required":"NO","reapply_required":"NO","closure_status":"CLOSED","closure_artifact":"PATCH_003A_CLOSURE_REPORT.md","backup_artifact":"s43.py.PATCH_003A_VERIFIED_FINAL.bak","safety_class":"passive_logging_no_business_logic_change","notes":"Post-Phase-15 observability patch. Hooks isolated with try/except. Original return paths preserved."}
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\CHANGE_CONTROL_LEDGER.jsonl:2:{"ts":"2026-06-13T20:40:22Z","type":"discovery_audit_and_documentation_normalization","target":"s43.py","summary":"Phase 16 and Phase 17 markers confirmed in active codebase; ROADMAP_vNEXT.md normalized; no rollback to Phase 15.","baseline":{"expected_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","actual_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","sha256_status":"MATCH","compile_status":"py_compile PASS"},"evidence":{"phase16":{"present":true,"start_line":6549,"end_line":6657,"start_marker":"# --- PHASE 16: GOVERNANCE ENFORCEMENT ---","end_marker":"# --- END PHASE 16 ---"},"phase17":{"present":true,"start_line":21,"end_line":25,"start_marker":"# === PHASE 17 AUDIT FOUNDATION IMPORT ===","end_marker":"# === END PHASE 17 AUDIT FOUNDATION IMPORT ==="},"report":"PHASE_16_17_DISCOVERY_REPORT.txt","roadmap":"ROADMAP_vNEXT.md"},"decision":"Continue from current baseline; do not roll back to Phase 15; perform behavioral verification before further invasive patches."}
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\CHANGE_CONTROL_LEDGER.jsonl:3:{"actual_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","phase_8_promoted":false,"evidence_file_present":true,"timestamp":"20260614_003753","hash_status":"PASS","source_modified":false,"docs_written":["PHASE8_TRACEABILITY_GAP_REPORT.md","ROADMAP_TRACEABILITY_GAP_ADDENDUM_PHASE8.md"],"source_executed":false,"target":"s43.py","phase_8_status":"TRACEABILITY_GAP_NOT_EVIDENCE_CONFIRMED","expected_sha256":"3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C","finalization_type":"gap_documentation_only","rule":"No blind promotion. Missing Phase 8 is recorded as a gap, not as completed.","event":"phase_8_traceability_gap_documented"}
.\backups\s43_before_phase2_helpers_20260527_094432.py:6973:    def get_health_report(self) -> Dict[str, Any]:
.\backups\s43_before_phase2_helpers_20260527_094432.py:6975:            report = {
.\backups\s43_before_phase2_helpers_20260527_094432.py:6984:                report["metrics"][name] = metric.get_stats(300)
.\backups\s43_before_phase2_helpers_20260527_094432.py:6985:            return report
.\backups\s43_before_phase2_helpers_20260527_094432.py:7014:                return self._last_system_report or {}
.\backups\s43_before_phase2_helpers_20260527_094432.py:7016:            symbol_reports = {}
.\backups\s43_before_phase2_helpers_20260527_094432.py:7021:                report = monitor.get_health_report()
.\backups\s43_before_phase2_helpers_20260527_094432.py:7022:                symbol_reports[symbol] = report
.\backups\s43_before_phase2_helpers_20260527_094432.py:7040:            report = {
.\backups\s43_before_phase2_helpers_20260527_094432.py:7046:                "symbol_reports": symbol_reports,
.\backups\s43_before_phase2_helpers_20260527_094432.py:7049:            self._last_system_report = report
.\backups\s43_before_phase2_helpers_20260527_094432.py:7050:            return report
.\backups\s43_before_phase2_helpers_20260527_094432.py:8265:                health_report = self.health_monitor.check_system_health()
.\backups\s43_before_phase2_helpers_20260527_094432.py:8266:                if health_report.get("system_status") == "CRITICAL":
.\backups\s43_before_phase2_helpers_20260527_094432.py:8271:                priority_symbols = self._prioritize_symbols(symbols, health_report)
.\backups\s43_before_phase2_helpers_20260527_094432.py:8289:        health_report: Dict[str, Any]
.\backups\s43_before_phase2_helpers_20260527_094432.py:8293:            symbol_report = health_report.get("symbol_reports", {}).get(symbol, {})
.\backups\s43_before_phase2_helpers_20260527_094432.py:8294:            health_score = symbol_report.get("health_score", 0)
.\backups\s43_before_phase2_helpers_20260527_094432.py:8298:            key=lambda s: health_report.get("symbol_reports", {}).get(s, {}).get("health_score", 0),
.\backups\s43_before_phase2_helpers_20260527_094432.py:11892:    - reports network as healthy by default
.\backups\s43_before_phase2_helpers_20260527_094432.py:20718:                        _pp200_report(exc, tag="ASYNCIO", ctx={"message": str(context.get("message", ""))[:200]}, logger=getattr(self, "_log", None))
.\backups\s43_before_phase2_helpers_20260527_094432.py:22934:        if getattr(args, "report_dir", None) and "--report-dir" not in pt:
.\backups\s43_before_phase2_helpers_20260527_094432.py:22935:            pt = ["--report-dir", str(args.report_dir)] + pt
.\backups\s43_before_phase2_helpers_20260527_094432.py:28505:    """Entry point with crash reporting (no sys.excepthook monkey-patch)."""
.\backups\s43_before_phase2_helpers_20260527_094432.py:28510:            _pp200_report(e, tag="FATAL", ctx={"argv": (argv if argv is not None else sys.argv[1:])})
.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8079:    def get_health_report(self) -> Dict[str, Any]:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8081:            report = {

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8090:                report["metrics"][name] = metric.get_stats(300)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8091:            return report

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8120:                return self._last_system_report or {}

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8122:            symbol_reports = {}

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8127:                report = monitor.get_health_report()

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8128:                symbol_reports[symbol] = report

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8146:            report = {

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8152:                "symbol_reports": symbol_reports,

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8155:            self._last_system_report = report

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:8156:            return report

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:9371:                health_report = self.health_monitor.check_system_health()

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:9372:                if health_report.get("system_status") == "CRITICAL":

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:9377:                priority_symbols = self._prioritize_symbols(symbols, health_report)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:9395:        health_report: Dict[str, Any]

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:9399:            symbol_report = health_report.get("symbol_reports", {}).get(symbol, {})

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:9400:            health_score = symbol_report.get("health_score", 0)

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:9404:            key=lambda s: health_report.get("symbol_reports", {}).get(s, {}).get("health_score", 0),

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:13077:    - reports network as healthy by default

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:14955:                "wallet_reporting_summary",

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:22121:                        _pp200_report(exc, tag="ASYNCIO", ctx={"message": str(context.get("message", ""))[:200]}, logger=getattr(self, "_log", None))

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:24405:        if getattr(args, "report_dir", None) and "--report-dir" not in pt:

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:24406:            pt = ["--report-dir", str(args.report_dir)] + pt

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:30033:    """Entry point with crash reporting (no sys.excepthook monkey-patch)."""

.\BASELINE_PROTECTION_SNAPSHOT_20260614_004542\s43.py:30038:            _pp200_report(e, tag="FATAL", ctx={"argv": (argv if argv is not None else sys.argv[1:])})

.\PATCH_003A_CLOSURE_REPORT.md:1:# PATCH_003A_PERFORMANCE_LEDGER_BASELINE - Closure Report
.\backups\20260527_093330\s43.py:6979:    def get_health_report(self) -> Dict[str, Any]:
.\backups\20260527_093330\s43.py:6981:            report = {
.\backups\20260527_093330\s43.py:6990:                report["metrics"][name] = metric.get_stats(300)
.\backups\20260527_093330\s43.py:6991:            return report
.\backups\20260527_093330\s43.py:7020:                return self._last_system_report or {}


## Closure Note

This file closes the previously partial report-generation evidence item by recording current repository-level report evidence.
