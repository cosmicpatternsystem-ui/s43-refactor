from .logger import Logger
from .__volatility_analyzer import _VolatilityAnalyzer
from .dashboard_manager import DashboardManager
from .wallet_runtime import WalletRuntime

class WallStreetDashboardManager(DashboardManager):
    _RE_EVENT_TAG = re.compile(r"\bevent=([A-Za-z0-9_\-]+)")
    def _format_dashboard_events(self, recent_events):
        """Last events filter: dedupe noisy repeats, but DO NOT freeze dynamic health lines.

        NOTE: We intentionally *do not* digit-normalize some events (health/top8/ages/scores),
        otherwise the dashboard will show a constant score/age forever.
        """
        try:
            max_lines = int(os.getenv("DASH_LAST_EVENTS_MAX_LINES", "12") or "12")
        except Exception:
            max_lines = 12
        max_lines = max(1, min(50, int(max_lines)))
        seen_norm = set()
        filtered = []
        dynamic_markers = (
            "HEALTH_SYS_", "HEALTH_WD_", "TOP8_", "WHY_NO_TRADE", "ENTRY:", "radar=", "mkt=", "api=", "top8=", "score="
        )
        for ev in (recent_events or []):
            try:
                s_ev = str(ev)
            except Exception:
                s_ev = repr(ev)
            try:
                if any((mk in s_ev) for mk in dynamic_markers):
                    norm = s_ev
                else:
                    norm = re.sub(r"\d+", "N", s_ev)
            except Exception:
                norm = s_ev
            if norm in seen_norm:
                continue
            seen_norm.add(norm)
            filtered.append(s_ev)
            if len(filtered) >= max_lines:
                break
        return filtered
    async def _run(self) -> None:
        try:
            try:
                try:
                    from rich.console import Console
                except:
                    pass
            except:
                pass
            try:
                try:
                    from rich.live import Live
                except:
                    pass
            except:
                pass
            try:
                try:
                    from rich.table import Table
                except:
                    pass
            except:
                pass
            try:
                try:
                    from rich import box
                except:
                    pass
            except:
                pass
            try:
                try:
                    from rich.layout import Layout
                except:
                    pass
            except:
                pass
            try:
                try:
                    from rich.panel import Panel
                except:
                    pass
            except:
                pass
            try:
                try:
                    from rich.columns import Columns
                except:
                    pass
            except:
                pass
            try:
                try:
                    from rich.console import Group
                except:
                    pass
            except:
                pass
            try:
                try:
                    from rich.text import Text
                except:
                    pass
            except:
                pass
        except Exception:
            await self._run_fallback()
            return
        console = Console(force_terminal=True)
        if not self.screen:
            os.environ.setdefault("TERM", os.environ.get("TERM", "xterm-256color"))
        try:
            try:
                try:
                    import logging
                except:
                    pass
            except:
                pass
            root = logging.getLogger()
            for h in list(root.handlers):
                if isinstance(h, logging.StreamHandler):
                    root.removeHandler(h)
        except Exception:
            pass
        _start_mid = {}
        _hist_max = int(_env_int("DASH_HIST_POINTS", 240))
        try:
            _ana = getattr(self.bot, "analyzer", None)
            if _ana is None or not hasattr(_ana, "_hist"):
                try:
                    _ana = _VolatilityAnalyzer(maxlen=_hist_max)
                    setattr(self.bot, "analyzer", _ana)
                except Exception:
                    _ana = None
            _hist = getattr(_ana, "_hist", None) if _ana is not None else None
            if not isinstance(_hist, dict):
                _hist = {}
        except Exception:
            _hist = {}
        try:
            try:
                from collections import defaultdict, deque
            except:
                pass
        except:
            pass
        _eq_hist = defaultdict(lambda: __import__("collections").deque(maxlen=int(_env_int("DASH_EQ_POINTS", 1600) or 1600)))
        _eq_sample_sec = float(_env_float("DASH_EQ_SAMPLE_SEC", 60.0) or 60.0)
        def _eq_track(wname: str, equity_irt: float) -> None:
            try:
                now = time.time()
                dq = _eq_hist[str(wname)]
                if (not dq) or (now - float(dq[-1][0])) >= _eq_sample_sec:
                    dq.append((now, float(equity_irt or 0.0)))
                else:
                    dq[-1] = (float(dq[-1][0]), float(equity_irt or 0.0))
            except Exception:
                return
        def _eq_delta_24h(wname: str, equity_irt: float):
            try:
                now = time.time()
                dq = _eq_hist.get(str(wname)) or []
                if not dq:
                    return 0.0, 0.0, None
                cutoff = now - 86400.0
                base = None
                base_ts = None
                for ts, v in dq:
                    if float(ts) >= cutoff:
                        base = float(v)
                        base_ts = float(ts)
                        break
                if base is None:
                    ts, v = dq[0]
                    base = float(v)
                    base_ts = float(ts)
                cur = float(equity_irt or 0.0)
                d = cur - float(base or 0.0)
                pct = (d / base) * 100.0 if base and abs(base) > 1e-9 else 0.0
                return float(d), float(pct), base_ts
            except TradingHalt:
                raise
            except Exception:
                return 0.0, 0.0, None
        def _canon(sym: str) -> str:
            try:
                return _canon_symbol(sym)
            except Exception:
                return str(sym or "").strip().upper()
        def fmt_num(x: float, digits: int = 0) -> str:
            try:
                return f"{float(x):,.{int(digits)}f}"
            except Exception:
                return "N/A"
        def fmt_toman_from_irt(x) -> str:
            try:
                v = float(x or 0.0)
                div = 1.0
                try:
                    _, _, _umid, _, _ = _feed_snapshot("USDTIRT")
                    if _umid is not None and float(_umid or 0.0) >= 1_000_000.0:
                        div = 10.0
                except Exception:
                    div = 1.0
                return f"{(v / div):,.0f}"
            except Exception:
                return "N/A"
        def fmt_pct(x) -> str:
            try:
                return f"{float(x):+.3f}%"
            except Exception:
                return "N/A"
        def fmt_age_s(sec) -> str:
            try:
                if sec is None:
                    return "N/A"
                sec = float(sec)
                if (not math.isfinite(sec)) or sec < 0.0:
                    return "N/A"
                max_age = float(_env_float("DASH_MAX_AGE_SEC", 60.0 * 60.0 * 24.0 * 365.0) or (60.0 * 60.0 * 24.0 * 365.0))
                if sec > max(1.0, max_age):
                    return "N/A"
                if sec < 1.0:
                    return f"{sec*1000.0:,.0f}ms"
                if sec < 60.0:
                    return f"{sec:,.1f}s"
                if sec < 3600.0:
                    return f"{sec/60.0:,.1f}m"
                if sec < 86400.0:
                    return f"{sec/3600.0:,.1f}h"
                return f"{sec/86400.0:,.1f}d"
            except Exception:
                return "N/A"
        _DASH_ASCII = bool(_env_bool("DASH_ASCII", True) or _env_bool("TERMUX_MODE", False))
        def _icon(emoji: str, ascii_fallback: str) -> str:
            try:
                return ascii_fallback if _DASH_ASCII else str(emoji)
            except Exception:
                return ascii_fallback
        def _tail_lines(path: str, max_lines: int = 25, max_bytes: int = 65536) -> List[str]:
            try:
                path = str(path or "").strip()
                if not path:
                    return []
                if not os.path.isfile(path):
                    return []
                size = os.path.getsize(path)
                if size <= 0:
                    return []
                to_read = min(int(max_bytes or 65536), size)
                with open(path, "rb") as f:
                    try:
                        f.seek(-to_read, os.SEEK_END)
                    except Exception:
                        f.seek(0, os.SEEK_SET)
                    raw = f.read(to_read)
                txt = raw.decode("utf-8", errors="replace")
                lines = [ln.rstrip("\n") for ln in txt.splitlines() if ln.strip()]
                return lines[-int(max_lines or 25):]
            except Exception:
                return []
        def _feed_snapshot(sym: str):
            """Truthful snapshot feed for dashboard.
            Uses the single source of truth: get_best_snapshot().
            Returns dict with real ts/age and NEVER fabricates dp%.
            """
            now = time.time()
            try:
                stale_after = float(_env_float("TOP8_STALE_AFTER_SEC", 90.0) or 90.0)
            except Exception:
                stale_after = 90.0
            snap0 = get_best_snapshot(sym, bot=self.bot, now=now, stale_after_sec=stale_after)
            ts = snap0.get("ts")
            age_s = None
            try:
                if ts is not None:
                    age_s = max(0.0, float(now) - float(ts))
            except Exception:
                age_s = None
            return {
                "bid": snap0.get("bid"),
                "ask": snap0.get("ask"),
                "mid": snap0.get("mid"),
                "spr_bps": snap0.get("spr_bps"),
                "dp_pct": snap0.get("dp_pct"),
                "ts": ts,
                "age_s": age_s,
                "source": snap0.get("source"),
                "stale_reason": snap0.get("stale_reason") or "",
            }
        def rsi_from_hist(sym: str, period: int = 14):
            sym = _canon(sym)
            h = _hist.get(sym)
            if not h or len(h) < 3:
                return None
            try:
                p = int(period or 14)
                p = max(2, min(p, len(h) - 1))
                gains = 0.0
                losses = 0.0
                vals = list(h)[-(p + 1):]
                for i in range(1, len(vals)):
                    d = float(vals[i]) - float(vals[i - 1])
                    if d > 0:
                        gains += d
                    elif d < 0:
                        losses += (-d)
                if gains <= 0 and losses <= 0:
                    return 50.0
                if losses <= 0:
                    return 100.0
                rs = (gains / p) / (losses / p)
                return 100.0 - (100.0 / (1.0 + rs))
            except Exception:
                return None
        def shadow_from_hist(sym: str):
            try:
                sym0 = _canon(sym)
                h = _hist.get(sym0)
                if not h:
                    return None, ""
                vals = list(h)
                win = int(_env_int("PHOENIX_SHADOW_WIN", 10) or 10)
                if len(vals) < 6:
                    return None, ""
                win = max(6, min(win, len(vals)))
                vals = vals[-win:]
                pho0 = getattr(self.bot, "phoenix", None)
                if pho0 is not None and hasattr(pho0, "_shadow"):
                    try:
                        sh_v, sh_lbl = pho0._shadow(list(vals))
                        return sh_v, str(sh_lbl or "")
                    except Exception:
                        pass
                try:
                    med = float(sorted(vals)[len(vals)//2])
                    last = float(vals[-1])
                    if med <= 0:
                        return None, ""
                    v = (last - med) / med
                    v = max(-1.0, min(1.0, float(v) * 5.0))
                    return v, "H"
                except Exception:
                    return None, ""
            except Exception:
                return None, ""
        def _prediction_from(sig):
            if not sig:
                return "FLAT", 0.0, 0.0, 0.0, {}
            try:
                raw_score = float(getattr(sig, "score", 0.0) or 0.0)
                raw_conf = float(getattr(sig, "confidence", 0.0) or 0.0)
                meta = getattr(sig, "meta", None) or {}
            except Exception:
                raw_score, raw_conf, meta = 0.0, 0.0, {}
            try:
                meta = dict(meta or {})
                sym0 = str(getattr(sig, "symbol", "") or getattr(sig, "sym", "") or getattr(sig, "pair", "") or "")
                if sym0:
                    pho0 = getattr(self.bot, "phoenix", None)
                    if pho0 is not None and hasattr(pho0, "get_last_decision"):
                        d0 = pho0.get_last_decision(sym0)
                        if d0 is not None:
                            meta["phoenix_state"] = str(getattr(d0, "state", "FLAT") or "FLAT")
                            meta["phoenix_conf"] = float(getattr(d0, "confidence", 0.0) or 0.0)
                            meta["phoenix_score"] = float(getattr(d0, "composite", 0.0) or 0.0)
                            meta["phoenix_rsi"] = (float(getattr(d0, "rsi")) if getattr(d0, "rsi", None) is not None else None)
                            meta["phoenix_shadow_score"] = float(getattr(d0, "shadow_score", 0.0) or 0.0)
                            meta["phoenix_shadow_lbl"] = str(getattr(d0, "shadow_label", "") or "")
                            meta["phoenix_ready"] = bool(getattr(d0, "ready", False))
            except Exception:
                try:
                    meta = dict(meta or {})
                except Exception:
                    meta = {}
            st = str(meta.get("phoenix_state") or "").strip().upper()
            p_conf = float(meta.get("phoenix_conf", 0.0) or 0.0)
            p_score = float(meta.get("phoenix_score", raw_score) or raw_score)
            ready = bool(meta.get("phoenix_ready", False))
            if st in ("LONG", "SHORT", "FLAT"):
                state = st
                conf = p_conf
                score = p_score
            else:
                reg = str(meta.get("parisa_regime") or meta.get("regime") or "").strip().upper()
                if reg in ("BULL", "LONG"):
                    state = "LONG"
                elif reg in ("BEAR", "SHORT"):
                    state = "SHORT"
                else:
                    state = "FLAT"
                conf = raw_conf
                score = raw_score
            delta_pct = float(score) * 100.0
            return state, float(conf), float(delta_pct), float(score), meta
        def _wallet_ws(wname: str) -> dict:
            ws: dict = {}
            try:
                snap = self.bot.snapshot() if getattr(self, "bot", None) is not None else {}
                if isinstance(snap, dict):
                    wm = snap.get("wallets") or {}
                    if isinstance(wm, dict):
                        ws0 = wm.get(str(wname))
                        if isinstance(ws0, dict):
                            ws = ws0
            except Exception:
                ws = {}
            return ws or {}
        def _run_short(s: str, n: int = 42) -> str:
            try:
                s = str(s or "").strip()
            except Exception:
                s = ""
            if not s:
                return "-"
            s = re.sub(r"\s+", " ", s)
            if len(s) <= n:
                return s
            return s[: max(0, n - 3)] + "..."
        def _cancel_reason_lines(ws: dict, limit: int = 2) -> List[str]:
            raw = ""
            try:
                raw = str(ws.get("cancel_reasons", "") or "").strip()
            except Exception:
                raw = ""
            if not raw:
                return []
            raw = raw.replace(";", ",")
            parts = []
            for p in raw.split(","):
                p = p.strip()
                if not p:
                    continue
                parts.append(p)
            out = []
            for p in parts[: max(0, int(limit or 0))]:
                out.append(_run_short(p, 64))
            return out
        try:
            quote = str(getattr(getattr(self.bot, "cfg", None), "quote", "IRT") or "IRT").upper()
        except Exception:
            quote = "IRT"
        fiat_aliases = {quote, "IRT", "TMN", "TOMAN", "IRR", "RIAL", "RIALS"}
        def _run_assets_detail(w, max_items: int = 5, compact: bool = False):
            snap_assets = (getattr(w, "assets_total_snapshot", None) or getattr(w, "assets_snapshot", None) or {})
            items = []
            assets_value_irt = 0.0
            priced_ok = 0
            total = 0
            try:
                for a, amt in list(snap_assets.items()):
                    a0 = str(a or "").strip().upper()
                    try:
                        _q = str(quote or "").strip().upper()
                    except Exception:
                        _q = ""
                    try:
                        if _q and a0 and (a0 != _q) and a0.endswith(_q) and (len(a0) > len(_q)):
                            a0 = a0[:-len(_q)]
                    except Exception:
                        pass
                    if not a0 or a0 in fiat_aliases:
                        continue
                    try:
                        fv = float(amt or 0.0)
                    except Exception:
                        continue
                    if fv <= 0.0:
                        continue
                    total += 1
                    sym_a = _canon(a0) if (a0.endswith(quote) and (len(a0) > len(quote))) else _canon(f"{a0}{quote}")
                    _b, _a2, mid_a, _spr, age_s = _feed_snapshot(sym_a)
                    if (mid_a is None) and (not a0.endswith(quote)):
                        try:
                            _b, _a2, mid_a, _spr, age_s = _feed_snapshot(_canon(a0))
                        except Exception:
                            pass
                    if (mid_a is None) and (str(quote).upper() in ("IRT", "IRR", "TMN")):
                        try:
                            _b, _a2, mid_usdt, _spr, _age2 = _feed_snapshot(_canon(f"{a0}USDT"))
                            _b, _a2, mid_u2i, _spr, _age3 = _feed_snapshot(_canon("USDTIRT"))
                            if (mid_usdt is not None) and (mid_u2i is not None) and float(mid_usdt or 0.0) > 0.0 and float(mid_u2i or 0.0) > 0.0:
                                mid_a = float(mid_usdt) * float(mid_u2i)
                        except Exception:
                            pass
                    try:
                        _k = _canon(sym_a)
                        if mid_a is not None and float(mid_a or 0.0) > 0.0:
                            WalletRuntime.set_last_known_price(_k, float(mid_a))
                        else:
                            mid2 = float((WalletRuntime._LAST_KNOWN_VALID_PRICES.get(_k, 0.0)) or 0.0)
                            if mid2 > 0.0:
                                mid_a = mid2
                    except Exception:
                        pass
                    val = None
                    if mid_a is not None and float(mid_a or 0.0) > 0.0:
                        val = fv * float(mid_a)
                        assets_value_irt += float(val)
                        priced_ok += 1
                    sort_key = (float(val) if val is not None else 0.0)
                    items.append((sort_key, a0, fv, val, age_s))
                items.sort(key=lambda x: x[0], reverse=True)
            except Exception:
                items = []
            lines = []
            more = 0
            for i, (_k, a0, fv, val, age_s) in enumerate(items):
                if i >= int(max_items or 0):
                    more += 1
                    continue
                if val is None:
                    lines.append(f"{a0}: {fv:.6g}")
                else:
                    if compact:
                        lines.append(f"{a0}: {fv:.6g}~{fmt_toman_from_irt(val)}")
                    else:
                        lines.append(f"{a0}: {fv:.6g}  ~ {fmt_toman_from_irt(val)} (age {fmt_age_s(age_s)})")
            if more > 0:
                lines.append(f"+{more} more")
            return float(assets_value_irt), lines, int(priced_ok), int(total)
        def _equity_from_wallet(w, assets_value_irt=None, cash_irt=None) -> float:
            try:
                if cash_irt is None:
                    cash_irt = float(getattr(w, "cash_irt", 0.0) or 0.0)
            except Exception:
                cash_irt = 0.0
            try:
                if assets_value_irt is None:
                    assets_value_irt, _x, _y, _z = _run_assets_detail(w, max_items=0, compact=True)
            except Exception:
                assets_value_irt = 0.0
            try:
                ctot = float(getattr(w, "cash_total_irt", 0.0) or 0.0)
                if ctot > 0.0:
                    cash_irt = float(ctot)
            except Exception:
                pass
            equity_irt = float(float(getattr(w, "cash_total_irt", 0.0) or cash_irt) + float(assets_value_irt))
            try:
                w_eq = float(getattr(w, "equity_irt", 0.0) or 0.0)
                if w_eq > 0.0 and w_eq > (0.85 * equity_irt):
                    equity_irt = max(equity_irt, w_eq)
            except Exception:
                pass
            return float(equity_irt)
        def _wallet_age_status(w) -> Tuple[str, str]:
            ok = bool(getattr(w, "last_balance_ok", False))
            last_ts = float(getattr(w, "last_balance_ts", 0.0) or 0.0)
            age = "N/A"
            try:
                ts = float(last_ts or 0.0)
                ts = ts / 1000.0 if ts and ts > 1e11 else ts
                age = fmt_age_s(time.time() - ts) if ts > 0 else "N/A"
            except Exception:
                age = "N/A"
            st = "OK" if ok else ("STALE" if last_ts > 0 else "N/A")
            try:
                if bool(getattr(w, "sanity_halt", False)):
                    st = "HALT"
            except Exception:
                pass
            return str(age), str(st)
        def wallet_full_panel(wname: str, w):
            if w is None:
                return Panel("NO WALLET", title=str(wname), box=box.SQUARE, padding=(0, 1))
            ws = _wallet_ws(wname)
            cash_irt = float(getattr(w, "cash_irt", 0.0) or 0.0)
            ord_open_exch = int(getattr(w, "open_orders_exch", 0) or 0)
            pos_n = int(len(getattr(w, "positions", {}) or {}))
            assets_value_irt, lines_compact, priced_ok, total_assets = _run_assets_detail(w, max_items=9, compact=True)
            equity_irt = _equity_from_wallet(w, assets_value_irt, cash_irt)
            try:
                _eq_track(str(wname), float(equity_irt or 0.0))
            except Exception:
                pass
            d_24h, pct_24h, base_ts = _eq_delta_24h(str(wname), float(equity_irt or 0.0))
            win = "24h"
            try:
                if base_ts is None:
                    win = "-"
                else:
                    ts = float(base_ts or 0.0)
                    ts = ts / 1000.0 if ts and ts > 1e11 else ts
                    age0 = max(0.0, time.time() - ts)
                    if age0 < 23.0 * 3600.0:
                        win = fmt_age_s(age0)
            except Exception:
                win = "24h"
            ord_done = int(ws.get("done_trades", 0) or 0)
            ord_cxl = int(ws.get("canceled_trades", 0) or 0)
            done_24h = int(ws.get("done_24h", 0) or 0)
            cxl_24h = int(ws.get("canceled_24h", 0) or 0)
            ord_open = ord_open_exch
            try:
                ord_open = max(ord_open, int(ws.get("open_trades", 0) or 0))
            except Exception:
                pass
            last_trd_age = ws.get("last_resolved_age_sec", None)
            last_trd_s = fmt_age_s(last_trd_age) if last_trd_age is not None else "-"
            canc = _cancel_reason_lines(ws, limit=1)
            why = canc[0] if canc else "-"
            age, st = _wallet_age_status(w)
            gate = "OK"
            try:
                if bool(getattr(w, "sanity_halt", False)):
                    gate = "SANITY"
                else:
                    risk = getattr(self.bot, "risk", None)
                    if bool(getattr(risk, "safe_mode", False)):
                        gate = "SAFE"
                    elif not bool(getattr(w, "last_balance_ok", False)):
                        gate = "STALE"
            except Exception:
                gate = "OK"
            try:
                rr = str(getattr(w, "last_reject_reason", "") or "").strip()
            except Exception:
                rr = ""
            if not rr:
                rr = "-"
            hold_lines = []
            try:
                for ln in (lines_compact or [])[:8]:
                    s = str(ln or "").strip()
                    if not s:
                        continue
                    s = s.replace(":", " ", 1)
                    s = re.sub(r"\s+", " ", s).strip()
                    hold_lines.append(s)
            except Exception:
                hold_lines = []
            if not hold_lines:
                hold_lines = ["-"]
            av = fmt_toman_from_irt(assets_value_irt)
            if total_assets > 0:
                av = f"{av} ({priced_ok}/{total_assets})"
            try:
                sign = "+" if float(d_24h) >= 0 else "-"
                pnl_abs = abs(float(d_24h))
                pnl_s = f"{sign}{fmt_toman_from_irt(pnl_abs)}"
                pnl_pct = f"{float(pct_24h):+.2f}%"
            except Exception:
                pnl_s, pnl_pct = "N/A", "N/A"
            t = Table.grid(padding=(0, 0), expand=True)
            t.add_column(justify="left", overflow="fold")
            t.add_row(f"EQ {fmt_toman_from_irt(equity_irt)}   Δ{win} {pnl_s} ({pnl_pct})")
            try:
                eng_st0 = str(getattr(w, "last_engine_status", "") or "").strip()
            except Exception:
                eng_st0 = ""
            if not eng_st0:
                eng_st0 = "Hold"
            try:
                eng_rs0 = str(getattr(w, "last_engine_reason", "") or "").strip()
            except Exception:
                eng_rs0 = ""
            if not eng_rs0:
                try:
                    eng_rs0 = str(getattr(w, "sanity_reason", "") or "").strip()
                except Exception:
                    eng_rs0 = ""
            if (not eng_rs0) and rr and rr != "-":
                eng_rs0 = rr
            if not eng_rs0:
                eng_rs0 = "-"
            t.add_row(f"ST {eng_st0} | {_run_short(eng_rs0, 72)}")
            t.add_row(f"CA {fmt_toman_from_irt(cash_irt)}   AV {av}   POS {pos_n}   ORD {ord_open_exch}")
            try:
                if not bool(getattr(w, "last_balance_ok", False)):
                    berr = str(getattr(w, "last_balance_err", "") or "").strip()
                    if berr:
                        t.add_row(f"BAL ! {_run_short(berr, 72)}")
            except Exception:
                pass
            try:
                oerr = str(getattr(w, "last_orders_err", "") or "").strip()
                if oerr and int(getattr(w, "open_orders_exch", 0) or 0) == 0:
                    t.add_row(f"ORD ! {_run_short(oerr, 72)}")
            except Exception:
                pass
            try:
                h = [x for x in (hold_lines or []) if str(x).strip() and str(x).strip() != "-"]
            except Exception:
                h = []
            if not h:
                h = hold_lines or ["-"]
            try:
                h1 = " | ".join([str(x).strip() for x in h[:3] if str(x).strip()])
                if h1:
                    t.add_row(f"H {h1}")
                h2 = " | ".join([str(x).strip() for x in h[3:6] if str(x).strip()])
                if h2:
                    t.add_row(f"H {h2}")
            except Exception:
                pass
            t.add_row(f"T24 ✅{done_24h} ❌{cxl_24h}   O/D/C {ord_open}/{ord_done}/{ord_cxl}   LAST {last_trd_s}   BAL {age} {st} {gate}")
            def _age_s(sec: Optional[float]) -> str:
                try:
                    if sec is None:
                        return "-"
                    s0 = float(sec)
                    if s0 < 60:
                        return f"{int(round(s0))}s"
                    if s0 < 3600:
                        return f"{s0/60:.1f}m"
                    return f"{s0/3600:.1f}h"
                except Exception:
                    return "-"
            try:
                ttl0 = float(_env_float("ORDER_TTL_SEC", 300.0) or 300.0)
            except Exception:
                ttl0 = 300.0
            ttl0 = max(30.0, float(ttl0))
            oldest0 = getattr(w, "open_orders_oldest_age_sec", None)
            ttl_ok = int(getattr(w, "ttl_canceled", 0) or 0)
            ttl_fail = int(getattr(w, "ttl_cancel_failed", 0) or 0)
            ttl_err = str(getattr(w, "ttl_last_cancel_err", "") or "")
            if int(ord_open_exch or 0) > 0 or ttl_fail > 0:
                status_icon = "[green]●[/]" if ttl_fail == 0 else "[red]●[/]"
                t.add_row(f"ORD {status_icon}  ⏳{_age_s(oldest0)}  TTL{int(ttl0)}s  ✔{ttl_ok} ✖{ttl_fail}  {_run_short(ttl_err, 26)}")
            try:
                eng_st = str(getattr(w, "last_engine_status", "") or "").strip()
            except Exception:
                eng_st = ""
            if not eng_st:
                try:
                    evu = str(getattr(w, "last_event", "") or "").upper()
                except Exception:
                    evu = ""
                if "BUY" in evu:
                    eng_st = "Buy"
                elif "SELL" in evu:
                    eng_st = "Sell"
                else:
                    eng_st = "Hold"
            try:
                eng_reason = str(getattr(w, "last_engine_reason", "") or "").strip()
            except Exception:
                eng_reason = ""
            if not eng_reason:
                try:
                    eng_reason = str(getattr(w, "sanity_reason", "") or "").strip()
                except Exception:
                    eng_reason = ""
            if not eng_reason and rr and rr != "-":
                eng_reason = rr
            blockers = []
            try:
                if int(getattr(w, "open_orders_exch", 0) or 0) > 0:
                    blockers.append(f"ORD={int(getattr(w, 'open_orders_exch', 0) or 0)}")
            except Exception:
                pass
            try:
                if bool(getattr(w, "sanity_halt", False)):
                    blockers.append("SANITY")
            except Exception:
                pass
            try:
                if not bool(getattr(w, "last_balance_ok", False)):
                    blockers.append("BAL_STALE")
            except Exception:
                pass
            try:
                risk = getattr(self.bot, "risk", None)
                if bool(getattr(risk, "safe_mode", False)):
                    blockers.append("SAFE")
                    if not eng_reason:
                        eng_reason = str(getattr(risk, "safe_reason", "") or "").strip()
            except Exception:
                pass
            blk = " | ".join(blockers) if blockers else "OK"
            if rr and rr != "-":
                t.add_row(f"🚫 {_run_short(rr, 120)}")
            if why and why != "-":
                t.add_row(f"✖ {_run_short(why, 120)}")
            return Panel(t, title=str(wname), box=box.SQUARE, padding=(0, 1))
        def wallet_panel(wname: str, w):
            return wallet_full_panel(wname, w)
        def wallet_overview_panel(wallets_kv, narrow: bool = False):
            wstats_map = {}
            try:
                snap = self.bot.snapshot() if getattr(self, "bot", None) is not None else {}
                if isinstance(snap, dict):
                    wstats_map = snap.get("wallets") or {}
            except Exception:
                wstats_map = {}
            try:
                quote = str(getattr(getattr(self.bot, "cfg", None), "quote", "IRT") or "IRT").upper()
            except Exception:
                quote = "IRT"
            fiat_aliases = {quote, "IRT", "TMN", "TOMAN", "IRR", "RIAL", "RIALS"}
            def _overview_short(s: str, n: int = 28) -> str:
                try:
                    s = str(s or "").strip()
                except Exception:
                    pass
                if not s:
                    return "-"
                s = re.sub(r"\s+", " ", s)
                if len(s) <= n:
                    return s
                return s[: max(0, n - 3)] + "..."
            def _overview_assets_detail(w, max_items: int = 6):
                snap_assets = getattr(w, "assets_snapshot", None) or {}
                items = []
                assets_value_irt = 0.0
                priced_ok = 0
                total = 0
                try:
                    for a, amt in list(snap_assets.items()):
                        a0 = str(a or "").strip().upper()
                        try:
                            _q = str(quote or "").strip().upper()
                        except Exception:
                            _q = ""
                        try:
                            if _q and a0 and (a0 != _q) and a0.endswith(_q) and (len(a0) > len(_q)):
                                a0 = a0[:-len(_q)]
                        except Exception:
                            pass
                        if not a0 or a0 in fiat_aliases:
                            continue
                        try:
                            fv = float(amt or 0.0)
                        except Exception:
                            continue
                        if fv <= 0.0:
                            continue
                        total += 1
                        sym_a = _canon(f"{a0}{quote}")
                        _b, _a2, mid_a, _spr, age_s = _feed_snapshot(sym_a)
                        try:
                            _k = _canon(sym_a)
                            if mid_a is not None and float(mid_a or 0.0) > 0.0:
                                WalletRuntime.set_last_known_price(_k, float(mid_a))
                            else:
                                mid2 = float((WalletRuntime._LAST_KNOWN_VALID_PRICES.get(_k, 0.0)) or 0.0)
                                if mid2 > 0.0:
                                    mid_a = mid2
                        except Exception:
                            pass
                        val = None
                        if mid_a is not None and float(mid_a or 0.0) > 0.0:
                            val = fv * float(mid_a)
                            assets_value_irt += float(val)
                            priced_ok += 1
                        sort_key = (float(val) if val is not None else 0.0)
                        items.append((sort_key, a0, fv, val, age_s))
                    items.sort(key=lambda x: x[0], reverse=True)
                except Exception:
                    items = []
                lines = []
                more = 0
                try:
                    for i, (_k, a0, fv, val, age_s) in enumerate(items):
                        if i >= max_items:
                            more += 1
                            continue
                        if val is None:
                            lines.append(f"{a0}: {fv:.6g}  (price N/A)")
                        else:
                            lines.append(f"{a0}: {fv:.6g}  ~ {fmt_toman_from_irt(val)}  (age {fmt_age_s(age_s)})")
                except Exception:
                    pass
                if more > 0:
                    lines.append(f"+{more} more")
                return float(assets_value_irt), lines, int(priced_ok), int(total)
            def _compact_assets(lines, max_len: int = 46) -> str:
                if not lines:
                    return "-"
                out = []
                for ln in lines:
                    s = str(ln)
                    s = s.replace(":", " ").replace("  ~ ", "~").replace(" (age ", " age").replace(")", "")
                    s = re.sub(r"\s+", " ", s).strip()
                    out.append(s)
                    if len(out) >= 4:
                        break
                joined = " | ".join(out)
                if len(joined) <= max_len:
                    return joined
                return _overview_short(joined, max_len)
            def _top_cancel_reasons(ws: dict, n: int = 2) -> str:
                try:
                    raw = str(ws.get("cancel_reasons", "") or "").strip()
                except Exception:
                    raw = ""
                if not raw:
                    return "-"
                raw = raw.replace(";", ",").replace("=", ":")
                raw = re.sub(r"\s+", " ", raw)
                parts = []
                for p in raw.split(","):
                    p = p.strip()
                    if not p:
                        continue
                    parts.append(p)
                if not parts:
                    return _overview_short(raw, 44)
                return _overview_short(", ".join(parts[:n]), 44)
            rows = []
            for wname, w in wallets_kv:
                ws = (wstats_map.get(str(wname), {}) if isinstance(wstats_map, dict) else {}) or {}
                ot = int(ws.get("open_trades", 0) or 0)
                dt = int(ws.get("done_trades", 0) or 0)
                ct = int(ws.get("canceled_trades", 0) or 0)
                why = _top_cancel_reasons(ws, n=2)
                if w is None:
                    rows.append(
                        dict(
                            w=str(wname),
                            eq="N/A",
                            cash="N/A",
                            assetv="N/A",
                            ord="0",
                            trades=f"{ot}/{dt}/{ct}",
                            why=why,
                            assets="-",
                            age="N/A",
                            status="N/A",
                            pos="0",
                        )
                    )
                    continue
                cash_irt = float(getattr(w, "cash_irt", 0.0) or 0.0)
                ord_open = int(getattr(w, "open_orders_exch", 0) or 0)
                pos = getattr(w, "positions", {}) or {}
                assets_value_irt, asset_lines, priced_ok, total_assets = _overview_assets_detail(w, max_items=8)
                if (assets_value_irt <= 0.0) and (not (getattr(w, "assets_snapshot", None) or {})) and len(pos) > 0:
                    try:
                        pos_value_irt = 0.0
                        for sym, p in list(pos.items()):
                            sym = _canon(sym)
                            qty = float(getattr(p, "qty", 0.0) or 0.0)
                            _bid, _ask, mid, _spr, _age_s = _feed_snapshot(sym)
                            if mid is None or float(mid or 0.0) <= 0.0:
                                continue
                            pos_value_irt += qty * float(mid)
                        if pos_value_irt > 0.0:
                            assets_value_irt = float(pos_value_irt)
                    except Exception:
                        pass
                equity_irt = float(float(getattr(w, "cash_total_irt", 0.0) or cash_irt) + float(assets_value_irt))
                try:
                    w_eq = float(getattr(w, "equity_irt", 0.0) or 0.0)
                    if w_eq > 0.0 and w_eq > (0.85 * equity_irt):
                        equity_irt = max(equity_irt, w_eq)
                except Exception:
                    pass
                ok = bool(getattr(w, "last_balance_ok", False))
                last_ts = float(getattr(w, "last_balance_ts", 0.0) or 0.0)
                age = "N/A"
                try:
                    ts = float(last_ts or 0.0)
                    ts = ts / 1000.0 if ts and ts > 1e11 else ts
                    age = fmt_age_s(time.time() - ts) if ts > 0 else "N/A"
                except Exception:
                    age = "N/A"
                if ok:
                    s = "[green]OK[/]"
                elif last_ts > 0:
                    s = "[yellow]STALE[/]"
                else:
                    s = "N/A"
                try:
                    if bool(getattr(w, "sanity_halt", False)):
                        s = "[bold red]HALT[/]"
                except Exception:
                    pass
                assetv_label = fmt_toman_from_irt(assets_value_irt)
                if total_assets > 0:
                    assetv_label = f"{assetv_label} ({priced_ok}/{total_assets})"
                rows.append(
                    dict(
                        w=str(wname),
                        eq=fmt_toman_from_irt(equity_irt),
                        cash=fmt_toman_from_irt(cash_irt),
                        assetv=assetv_label,
                        ord=str(ord_open),
                        trades=f"{ot}/{dt}/{ct}",
                        why=why,
                        assets=_compact_assets(asset_lines, max_len=(52 if not narrow else 46)),
                        age=str(age),
                        status=s,
                        pos=str(len(pos)),
                    )
                )
            if narrow:
                t = Table.grid(padding=(0, 1), expand=True)
                t.add_column(justify="left", overflow="fold")
                for r in rows:
                    line = (
                        f"{r['w']} | EQ {r['eq']} | CA {r['cash']} | AV {r['assetv']} | "
                        f"ORD {r['ord']} | T {r['trades']}"
                    )
                    try:
                        if str(r.get("why", "-") or "-").strip() not in ("", "-"):
                            line += f" | WHY {r['why']}"
                    except Exception:
                        pass
                    try:
                        if str(r.get("age", "N/A") or "N/A") != "N/A":
                            line += f" | {r['age']}"
                    except Exception:
                        pass
                    try:
                        st = str(r.get("status", "") or "")
                        if st:
                            line += f" {st}"
                    except Exception:
                        pass
                    t.add_row(line)
                return Panel(t, title="Wallets - Summary", box=box.SQUARE, padding=(0, 1))
            t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold")
            t.add_column("W", justify="left", no_wrap=True)
            t.add_column("EQ(IRT)", justify="right")
            t.add_column("CASH(IRT)", justify="right")
            t.add_column("ASSETV", justify="right")
            t.add_column("HOLD", justify="left", overflow="fold")
            t.add_column("POS", justify="right")
            t.add_column("ORD", justify="right")
            t.add_column("T(O/D/C)", justify="right")
            t.add_column("WHY", justify="left", overflow="fold")
            t.add_column("AGE", justify="right")
            t.add_column("S", justify="left", no_wrap=True)
            for wname, w in wallets_kv:
                ws = (wstats_map.get(str(wname), {}) if isinstance(wstats_map, dict) else {}) or {}
                ot = int(ws.get("open_trades", 0) or 0)
                dt = int(ws.get("done_trades", 0) or 0)
                ct = int(ws.get("canceled_trades", 0) or 0)
                why = _overview_short(str(ws.get("cancel_reasons", "") or ""), 40)
                if w is None:
                    t.add_row(str(wname), "N/A", "N/A", "N/A", "-", "0", "0", f"{ot}/{dt}/{ct}", why, "N/A", "N/A")
                    continue
                cash_irt = float(getattr(w, "cash_irt", 0.0) or 0.0)
                ord_open = int(getattr(w, "open_orders_exch", 0) or 0)
                pos = getattr(w, "positions", {}) or {}
                assets_value_irt, asset_lines, priced_ok, total_assets = _overview_assets_detail(w, max_items=4)
                if (assets_value_irt <= 0.0) and (not (getattr(w, "assets_snapshot", None) or {})) and len(pos) > 0:
                    try:
                        pos_value_irt = 0.0
                        for sym, p in list(pos.items()):
                            sym = _canon(sym)
                            qty = float(getattr(p, "qty", 0.0) or 0.0)
                            _bid, _ask, mid, _spr, _age_s = _feed_snapshot(sym)
                            if mid is None or float(mid or 0.0) <= 0.0:
                                continue
                            pos_value_irt += qty * float(mid)
                        if pos_value_irt > 0.0:
                            assets_value_irt = float(pos_value_irt)
                    except Exception:
                        pass
                equity_irt = float(float(getattr(w, "cash_total_irt", 0.0) or cash_irt) + float(assets_value_irt))
                try:
                    w_eq = float(getattr(w, "equity_irt", 0.0) or 0.0)
                    if w_eq > 0.0 and w_eq > (0.85 * equity_irt):
                        equity_irt = max(equity_irt, w_eq)
                except Exception:
                    pass
                ok = bool(getattr(w, "last_balance_ok", False))
                last_ts = float(getattr(w, "last_balance_ts", 0.0) or 0.0)
                age = "N/A"
                try:
                    ts = float(last_ts or 0.0)
                    ts = ts / 1000.0 if ts and ts > 1e11 else ts
                    age = fmt_age_s(time.time() - ts) if ts > 0 else "N/A"
                except Exception:
                    age = "N/A"
                if ok:
                    s = "[green]OK[/]"
                elif last_ts > 0:
                    s = "[yellow]STALE[/]"
                else:
                    s = "N/A"
                try:
                    if bool(getattr(w, "sanity_halt", False)):
                        s = "[bold red]HALT[/]"
                except Exception:
                    pass
                hold = _overview_short(_compact_assets(asset_lines, max_len=80), 80)
                assetv_label = fmt_toman_from_irt(assets_value_irt)
                if total_assets > 0:
                    assetv_label = f"{assetv_label} ({priced_ok}/{total_assets})"
                t.add_row(
                    str(wname),
                    fmt_toman_from_irt(equity_irt),
                    fmt_toman_from_irt(cash_irt),
                    assetv_label,
                    hold,
                    str(len(pos)),
                    str(ord_open),
                    f"{ot}/{dt}/{ct}",
                    _overview_short(why, 56),
                    str(age),
                    s,
                )
            return Panel(t, title="Wallets", box=box.ROUNDED, padding=(0, 1))
        def phoenix_panel(sym: str):
            cand_max = int(_env_int("PHOENIX_CANDIDATE_MAX", 80) or 80)
            topn = int(_env_int("PHOENIX_TOP_N", 24) or 24)
            width0 = 0
            height0 = 0
            try:
                width0 = int(getattr(getattr(console, "size", None), "width", 0) or 0)
                height0 = int(getattr(getattr(console, "size", None), "height", 0) or 0)
            except Exception:
                width0 = 0
                height0 = 0
            try:
                if height0 > 0:
                    top_sz = max(9, min(14, int(round(height0 * 0.38))))
                    content_lines = max(3, int(top_sz) - 2)
                    reserve = 4
                    max_fit = max(4, content_lines - reserve)
                    topn = max(4, min(int(topn), int(max_fit)))
            except Exception:
                pass
            _hist = {}
            try:
                ana = getattr(self.bot, "analyzer", None)
                _hist = getattr(ana, "_hist", {}) or {}
            except Exception:
                _hist = {}
            try:
                health_thr = float(os.getenv("HEALTH_MKT_MAX_AGE_SEC", 20.0) or 20.0)
            except Exception:
                health_thr = 20.0
            try:
                px_hist = getattr(self.bot, "_phoenix_px_hist", None)
                if not isinstance(px_hist, dict):
                    px_hist = {}
            except Exception:
                px_hist = {}
            mkt_age_global = None
            mkt_state_global = ""
            try:
                snap0 = self.bot.snapshot() if getattr(self, "bot", None) is not None else {}
                focus0 = (snap0.get("focus") or {}) if isinstance(snap0, dict) else {}
                mkt_age_global = focus0.get("market_age_sec", focus0.get("mkt_age_sec", focus0.get("market_age", None)))
                if mkt_age_global is not None:
                    mkt_age_global = float(mkt_age_global)
                mkt_state_global = str(focus0.get("market_state", "") or "")
            except Exception:
                mkt_age_global = None
                mkt_state_global = ""
            def _canon_local(x: str) -> str:
                try:
                    return _canon_symbol(x)
                except Exception:
                    return str(x or "").strip().upper()
            cash_free_total = 0.0
            eq_total = 0.0
            try:
                for _w in (getattr(self.bot, "wallets", {}) or {}).values():
                    ca = float(getattr(_w, "cash_irt", 0.0) or 0.0)
                    try:
                        ca2 = float(getattr(_w, "cash_free_irt", 0.0) or 0.0)
                        if ca2 > 0.0 and (ca <= 0.0 or ca2 < ca * 1.2):
                            ca = ca2
                    except Exception:
                        pass
                    cash_free_total += max(0.0, float(ca))
                    eq_total += float(getattr(_w, "equity_irt", 0.0) or 0.0)
            except Exception:
                pass
            flat_pct = 0.0
            try:
                if float(eq_total) > 0.0:
                    flat_pct = 100.0 * float(cash_free_total) / float(eq_total)
            except Exception:
                flat_pct = 0.0
            cand: List[str] = []
            t8_map: Dict[str, Optional[float]] = {}
            try:
                snap = list(self.bot.get_top8_snapshot() or [])
                def _t8_get_pct(_row):
                    if not isinstance(_row, dict):
                        return None
                    for _k in PCT_KEYS:
                        if _row.get(_k) is not None:
                            return _row.get(_k)
                    return None
                def _t8_to_float(_x):
                    try:
                        if _x is None:
                            return None
                        if isinstance(_x, (int, float)):
                            v = float(_x)
                        else:
                            s = str(_x).replace(",", "").replace("%", "%").strip()
                            if not s or s.upper() in ("N/A", "NA", "NONE", "NULL", "-", "--"):
                                return None
                            if "%" in s:
                                s = s.replace("%", "")
                            v = float(s.strip())
                        if not math.isfinite(v):
                            return None
                        return float(v)
                    except Exception:
                        return None
                for r in snap:
                    if isinstance(r, dict) and r.get("symbol"):
                        s0 = _canon_symbol(str(r.get("symbol")))
                        if s0:
                            cand.append(s0)
                            dpv = None
                            try:
                                dpv = _t8_get_pct(r)
                            except Exception:
                                dpv = None
                            if dpv is not None:
                                try:
                                    dpvf = _t8_to_float(dpv)
                                    t8_map[s0] = (dpvf if math.isfinite(dpvf) else None)
                                except Exception:
                                    t8_map[s0] = None
                            else:
                                try:
                                    dq0 = px_hist.get(s0) if isinstance(px_hist, dict) else None
                                    if dq0 is None and isinstance(px_hist, dict):
                                        dq0 = px_hist.get(_canon_symbol(s0))
                                    if dq0 is not None and len(dq0) >= 2:
                                        _p0 = float(dq0[-2][1] or 0.0)
                                        _p1 = float(dq0[-1][1] or 0.0)
                                        if _p0 > 0.0:
                                            t8_map[s0] = float((_p1 - _p0) / _p0 * 100.0)
                                        else:
                                            t8_map[s0] = None
                                    else:
                                        t8_map[s0] = None
                                except Exception:
                                    t8_map[s0] = None
            except Exception:
                pass
            if sym:
                cand.append(_canon_symbol(sym))
            try:
                uni = list(getattr(self.bot, "_universe_symbols", []) or [])
                cand.extend(uni[: max(20, min(cand_max, 80))])
            except Exception:
                pass
            try:
                focus_syms = list((getattr(self.bot, "supported_symbols", {}) or {}).keys())
                cand.extend(focus_syms[:80])
            except Exception:
                pass
            seen: set = set()
            cand2: List[str] = []
            for s in cand:
                s0 = _canon_symbol(s)
                if not s0 or s0 in seen or (not s0.endswith("IRT")):
                    continue
                seen.add(s0)
                cand2.append(s0)
                if len(cand2) >= cand_max:
                    break
            def _rsi_pct_for(sym0: str) -> Optional[float]:
                try:
                    sig0 = best_signal_for(sym0)
                    _st, _conf, _dp, _sc, _meta = _prediction_from(sig0)
                    r = _meta.get("phoenix_rsi", None) if isinstance(_meta, dict) else None
                    if r is not None:
                        return float(r)
                except Exception:
                    pass
                try:
                    v = rsi_from_hist(sym0, period=int(_env_int("PHOENIX_RSI_PERIOD", 14) or 14))
                    if v is not None:
                        return float(v)
                except Exception:
                    pass
                try:
                    phx0 = getattr(self.bot, "phoenix", None)
                    if phx0 is not None:
                        last = phx0.get_last_decision(sym0)
                        rv = getattr(last, "rsi", None) if last is not None else None
                        if rv is not None:
                            return float(rv)
                except Exception:
                    pass
                return None
            def _mom_pct_for(sym0: str, win: int = 30) -> Optional[float]:
                try:
                    h = _hist.get(_canon_local(sym0))
                    if not h or len(h) < (win + 1):
                        return None
                    vals = list(h)[-(win + 1):]
                    a = float(vals[0])
                    b = float(vals[-1])
                    if a <= 0:
                        return None
                    return (b - a) / a * 100.0
                except Exception:
                    return None
            rows: List[Tuple[float, str, str, float, float, float, Optional[float], dict]] = []
            have_rows: set = set()
            for s0 in cand2:
                if s0 in have_rows:
                    continue
                try:
                    sig = best_signal_for(s0)
                    state, conf, dp, sc, meta = _prediction_from(sig)
                    rsi_v = _rsi_pct_for(s0)
                    try:
                        if s0 in t8_map:
                            dp_mkt = float(t8_map.get(s0) or 0.0)
                            conf_lim = float(_env_float("DASH_DP_USE_MKT_CHG_CONF_MAX", 0.12) or 0.12)
                            if (abs(float(conf or 0.0)) <= conf_lim) or (abs(float(dp_mkt or 0.0)) < 1e-6):
                                dp = dp_mkt
                                try:
                                    if isinstance(meta, dict):
                                        meta = dict(meta)
                                        meta["dp_src"] = "mkt_chg"
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    rank = abs(float(dp)) * (0.25 + 0.75 * max(0.0, min(1.0, float(conf)))) + abs(float(sc)) * 5.0
                    rows.append((rank, s0, str(state or "FLAT").upper(), float(dp), float(conf), float(sc), rsi_v, meta if isinstance(meta, dict) else {}))
                    have_rows.add(s0)
                    continue
                except Exception:
                    pass
                dp_fb = None
                try:
                    if s0 in t8_map:
                        dp_fb = float(t8_map.get(s0) or 0.0)
                except Exception:
                    dp_fb = None
                if dp_fb is None:
                    dp_fb = _mom_pct_for(s0, win=int(_env_int("PHOENIX_MOM_WIN", 30) or 30))
                if dp_fb is None:
                    continue
                rsi_v = _rsi_pct_for(s0)
                st = "LONG" if float(dp_fb) > 0.25 else ("SHORT" if float(dp_fb) < -0.25 else "FLAT")
                rows.append((abs(float(dp_fb)) * 0.20, s0, st, float(dp_fb), 0.25, 0.0, rsi_v, {"fallback": True}))
                have_rows.add(s0)
            if len(rows) < max(4, topn):
                for s0, dp0 in (t8_map or {}).items():
                    if s0 in have_rows:
                        continue
                    rsi_v = _rsi_pct_for(s0)
                    st = "LONG" if float(dp0) > 0.25 else ("SHORT" if float(dp0) < -0.25 else "FLAT")
                    rows.append((abs(float(dp0)) * 0.15, s0, st, float(dp0), 0.20, 0.0, rsi_v, {"top8_fill": True}))
                    have_rows.add(s0)
                    if len(rows) >= max(4, topn):
                        break
            if len(rows) < max(4, topn):
                majors = ["BTCIRT", "ETHIRT", "USDTIRT", "BNBIRT", "SOLIRT", "XRPIRT", "TONIRT", "PAXGIRT", "DOGEIRT"]
                for s0 in majors:
                    if s0 in have_rows:
                        continue
                    dp0 = None
                    try:
                        if s0 in t8_map:
                            dp0 = float(t8_map.get(s0) or 0.0)
                    except Exception:
                        dp0 = None
                    if dp0 is None:
                        dp0 = _mom_pct_for(s0, win=int(_env_int("PHOENIX_MOM_WIN", 30) or 30))
                    if dp0 is None:
                        continue
                    rsi_v = _rsi_pct_for(s0)
                    st = "LONG" if float(dp0) > 0.25 else ("SHORT" if float(dp0) < -0.25 else "FLAT")
                    rows.append((abs(float(dp0)) * 0.10, s0, st, float(dp0), 0.15, 0.0, rsi_v, {"major_fill": True}))
                    have_rows.add(s0)
                    if len(rows) >= max(4, topn):
                        break
            rows.sort(key=lambda r: float(r[0]), reverse=True)
            top_rsi_sym = ""
            top_rsi_val = None
            try:
                for _rk, _s0, _st, _dp, _cf, _sc, _rsi_v, _m0 in rows:
                    if _rsi_v is None:
                        continue
                    if (top_rsi_val is None) or (float(_rsi_v) > float(top_rsi_val)):
                        top_rsi_val = float(_rsi_v)
                        top_rsi_sym = str(_s0)
            except Exception:
                top_rsi_sym, top_rsi_val = "", None
            focus_hint = ""
            try:
                focus_hint = _canon_symbol(sym) if sym else (rows[0][1] if rows else "")
            except Exception:
                focus_hint = ""
            def _pick_best_focus(hint: str, rows0, t8m) -> Tuple[str, str, Optional[float], Optional[float]]:
                try:
                    hint = _canon_symbol(hint) if hint else ""
                except Exception:
                    hint = str(hint or "").strip().upper()
                max_ok = float(_env_float("DASH_FOCUS_MAX_AGE_SEC", 120.0) or 120.0)
                cand_syms: List[str] = []
                if hint:
                    cand_syms.append(hint)
                try:
                    for _rk, _s0, *_rest in (rows0 or [])[:8]:
                        s1 = _canon_symbol(_s0)
                        if s1 and s1 not in cand_syms:
                            cand_syms.append(s1)
                except Exception:
                    pass
                try:
                    for s1 in list((t8m or {}).keys())[:8]:
                        s1 = _canon_symbol(s1)
                        if s1 and s1 not in cand_syms:
                            cand_syms.append(s1)
                except Exception:
                    pass
                for s1 in ("BTCIRT", "ETHIRT", "USDTIRT", "BNBIRT", "SOLIRT", "XRPIRT", "TONIRT", "PAXGIRT"):
                    if s1 not in cand_syms:
                        cand_syms.append(s1)
                best = ("", "", None, None)
                best_score = float("inf")
                for s1 in cand_syms:
                    try:
                        _b, _a, _m, _spr, _age = _feed_snapshot(s1)
                        mid = float(_m) if (_m is not None and float(_m) > 0.0) else None
                        age = float(_age) if (_age is not None) else None
                    except Exception:
                        mid = None
                        age = None
                    if mid is None:
                        continue
                    score = float(age if age is not None else 1e9)
                    if score < best_score:
                        best_score = score
                        best = (s1, "OK", age, mid)
                if best[0]:
                    try:
                        _b, _a, _m, _spr, _age = _feed_snapshot(hint) if hint else (None, None, None, None, None)
                        hint_mid_ok = (_m is not None and float(_m or 0.0) > 0.0)
                        hint_age = float(_age) if _age is not None else None
                    except Exception:
                        hint_mid_ok = False
                        hint_age = None
                    if (not hint) or (not hint_mid_ok) or (hint_age is not None and float(hint_age) > max_ok):
                        why = "AUTO_FALLBACK"
                        if not hint:
                            why = "AUTO_FALLBACK:NO_HINT"
                        elif not hint_mid_ok:
                            why = "AUTO_FALLBACK:INVALID_HINT"
                        else:
                            why = "AUTO_FALLBACK:STALE_HINT"
                        return best[0], why, best[2], best[3]
                    if hint and best[0] != hint and best[2] is not None and hint_age is not None:
                        try:
                            if float(hint_age) - float(best[2]) > 15.0:
                                return best[0], "AUTO_FALLBACK:BETTER_FRESH", best[2], best[3]
                        except Exception:
                            pass
                    return hint or best[0], "OK", hint_age, (float(_m) if _m is not None else best[3])
                return hint, "INVALID", None, None
            focus_sym, focus_pick_reason, focus_age, focus_mid = _pick_best_focus(focus_hint, rows, t8_map)
            t = Table.grid(padding=(0, 0), expand=True)
            t.add_column(justify="left", overflow="crop")
            try:
                if width0 > 0 and width0 < 80:
                    t.add_row(f"FLAT {flat_pct:.1f}%")
                else:
                    t.add_row(f"FLAT {flat_pct:.1f}%   CA {_mid_short(cash_free_total)}   EQ {_mid_short(eq_total)}")
            except Exception:
                t.add_row(f"FLAT {flat_pct:.1f}%")
            try:
                sym_combo = ""
                try:
                    sym_combo = _canon_symbol(focus_sym) if focus_sym else ""
                except Exception:
                    sym_combo = str(focus_sym or "").strip().upper()
                if not sym_combo:
                    sym_combo = str(top_rsi_sym or "")
                rsi_combo = None
                try:
                    rsi_combo = _rsi_pct_for(sym_combo) if sym_combo else None
                except Exception:
                    rsi_combo = None
                if rsi_combo is None and top_rsi_val is not None and sym_combo == str(top_rsi_sym or ""):
                    try:
                        rsi_combo = float(top_rsi_val)
                    except Exception:
                        rsi_combo = None
                if (rsi_combo is not None) and sym_combo:
                    sh_v = None
                    sh_lbl = ""
                    try:
                        sigT = best_signal_for(sym_combo)
                        _stT, _cfT, _dpT, _scT, _mT = _prediction_from(sigT)
                        if isinstance(_mT, dict):
                            sh_v = _mT.get("phoenix_shadow_score")
                            if sh_v is None:
                                sh_v = _mT.get("phoenix_shadow")
                            sh_lbl = str(_mT.get("phoenix_shadow_lbl") or "")
                    except Exception:
                        sh_v, sh_lbl = None, ""
                    if sh_v is None:
                        try:
                            phx0 = getattr(self.bot, "phoenix", None)
                            last = phx0.get_last_decision(sym_combo) if phx0 is not None else None
                            if last is not None:
                                sh_v = getattr(last, "shadow_score", None)
                                sh_lbl = str(getattr(last, "shadow_label", sh_lbl) or sh_lbl)
                        except Exception:
                            pass
                    if sh_v is None:
                        try:
                            sh_v1, sh_lbl1 = shadow_from_hist(str(sym_combo or ""))
                            if sh_v1 is not None:
                                sh_v = sh_v1
                                sh_lbl = str(sh_lbl1 or sh_lbl or "")
                        except Exception:
                            pass
                    sh_txt = ""
                    sigma_txt = ""
                    try:
                        if sh_v is not None:
                            sh_txt = f"  SH{sh_lbl}{float(sh_v):+.2f}"
                    except Exception:
                        sh_txt = ""
                    try:
                        if sh_v is not None and rsi_combo is not None:
                            sigma = ((float(rsi_combo) - 50.0) / 50.0) + float(sh_v)
                            sigma_txt = f"  Σ{sigma:+.2f}"
                    except Exception:
                        sigma_txt = ""
                    t.add_row(f"RSI+SH  {sym_combo}  {float(rsi_combo):.0f}%{sh_txt}{sigma_txt}")
                else:
                    t.add_row("RSI+SH  -")
            except Exception:
                pass
            try:
                parts = []
                try:
                    rows0 = list(snap or [])
                except Exception:
                    rows0 = []
                try:
                    max_items = 8
                    if width0 > 0 and width0 < 80:
                        max_items = 5
                    elif width0 > 0 and width0 < 110:
                        max_items = 6
                except Exception:
                    max_items = 6
                for r in (rows0 or [])[:8]:
                    if not isinstance(r, dict):
                        continue
                    try:
                        ss = str(r.get("symbol") or r.get("market") or r.get("pair") or "").strip()
                        ss = _canon_symbol(ss) if ss else ""
                    except Exception:
                        ss = ""
                    ss2 = ss
                    try:
                        if ss2.endswith("IRT") and len(ss2) > 3:
                            ss2 = ss2[:-3]
                        if (ss.upper().startswith("USDT") and ss.upper().endswith("IRT")):
                            ss2 = "USDT"
                    except Exception:
                        pass
                    ss2 = _run_short(ss2, 5)
                    chg = None
                    try:
                        chg = _t8_get_pct(r)
                    except Exception:
                        chg = None
                    try:
                        chgv = _t8_to_float(chg)
                        c = f"{chgv:+.3f}%"
                        c = f"[green]{c}[/]" if chgv >= 0 else f"[red]{c}[/]"
                    except Exception:
                        c = ""
                    parts.append(f"{ss2}{c}")
                    if len(parts) >= max_items:
                        break
                line = "TOP8 " + (" ".join(parts) if parts else "-")
                max_len = 76
                try:
                    if width0 and int(width0) > 0:
                        max_len = max(32, min(140, int(width0) - 4))
                except Exception:
                    max_len = 76
                t.add_row(_run_short(line, int(max_len)))
            except Exception:
                pass
            try:
                if focus_sym:
                    bid, ask, mid, spr_bps, age = _feed_snapshot(focus_sym)
                    sig0 = best_signal_for(focus_sym)
                    st0, cf0, dp0, sc0, meta0 = _prediction_from(sig0)
                    st_u = str(st0 or "FLAT").upper()
                    if st_u.startswith("LONG"):
                        st_icon = "[green]▲[/]"
                    elif st_u.startswith("SHORT"):
                        st_icon = "[red]▼[/]"
                    else:
                        st_icon = "[grey37]●[/]"
                    age_txt = fmt_age_s(age) if age is not None else "?"
                    pred_dp = dp0
                    mkt_dp = None
                    try:
                        if focus_sym and focus_sym in t8_map:
                            _v = t8_map.get(focus_sym)
                            mkt_dp = (float(_v) if _v is not None else None)
                    except Exception:
                        mkt_dp = None
                    if mkt_dp is None:
                        try:
                            for al in _symbol_aliases(focus_sym):
                                k0 = _canon_symbol(al)
                                if k0 in t8_map:
                                    _v = t8_map.get(k0)
                                    mkt_dp = (float(_v) if _v is not None else None)
                                    break
                        except Exception:
                            pass
                    if mkt_dp is None:
                        try:
                            ms = getattr(self.bot, "_market_snapshot", None)
                            row = None
                            if isinstance(ms, dict) and ms:
                                for al in [focus_sym] + _symbol_aliases(focus_sym):
                                    k0 = _canon_symbol(al)
                                    row = ms.get(k0) or ms.get(al)
                                    if isinstance(row, dict):
                                        break
                                    row = None
                            if isinstance(row, dict):
                                for _k in ("chg_1h", "chg_pct", "change_pct", "priceChangePercent", "changePercent", "dayChangePercent", "pct", "percentChange", "change24h", "pct24h"):
                                    if row.get(_k) is not None:
                                        mkt_dp = float(row.get(_k))
                                        break
                        except Exception:
                            pass
                    if mkt_dp is None:
                        try:
                            dq1 = None
                            if isinstance(px_hist, dict):
                                dq1 = px_hist.get(focus_sym) or px_hist.get(_canon_symbol(focus_sym))
                                if dq1 is None:
                                    for al in _symbol_aliases(focus_sym):
                                        dq1 = px_hist.get(_canon_symbol(al))
                                        if dq1 is not None:
                                            break
                            if dq1 is not None and len(dq1) >= 2:
                                _t1, _p1 = dq1[-1]
                                _t0, _p0 = dq1[-2]
                                _p1 = float(_p1 or 0.0); _p0 = float(_p0 or 0.0)
                                if _p0 > 0.0 and _p1 > 0.0:
                                    mkt_dp = float((_p1 - _p0) / _p0 * 100.0)
                        except Exception:
                            pass
                    hist_ready = False
                    try:
                        dq0 = None
                        if isinstance(px_hist, dict):
                            dq0 = px_hist.get(focus_sym) or px_hist.get(_canon_symbol(focus_sym))
                            if dq0 is None:
                                for al in _symbol_aliases(focus_sym):
                                    dq0 = px_hist.get(_canon_symbol(al))
                                    if dq0 is not None:
                                        break
                        try:
                            if dq0 is not None and len(dq0) >= 1:
                                _t_last, _p_last = dq0[-1]
                                _p_last = float(_p_last or 0.0)
                                hist_ready = math.isfinite(_p_last) and _p_last > 0.0
                            else:
                                hist_ready = False
                        except Exception:
                            hist_ready = False
                    except Exception:
                        hist_ready = False
                    is_stale = False
                    try:
                        age_eff = age if age is not None else mkt_age_global
                        try:
                            if age_eff is None and str(mkt_state_global or '').upper().find('STALE') >= 0:
                                age_eff = float(health_thr) + 1.0
                        except Exception:
                            pass
                        is_stale = (age_eff is not None) and math.isfinite(float(age_eff)) and (float(age_eff) > float(health_thr))
                    except Exception:
                        is_stale = False
                    dp_disp = mkt_dp if (mkt_dp is not None and (not is_stale)) else None
                    if is_stale:
                        dp_txt = "[yellow]STALE[/]"
                    elif (mkt_dp is None):
                        dp_txt = "[grey50]WAIT[/]"
                    else:
                        dp_txt = f"{float(mkt_dp):+.3f}%"
                        dp_txt = f"[green]{dp_txt}[/]" if float(mkt_dp) >= 0 else f"[red]{dp_txt}[/]"
                    pred_txt = ""
                    try:
                        if width0 and int(width0) >= 85 and isinstance(pred_dp, (int, float)) and (dp_disp is not None):
                            if math.isfinite(float(pred_dp)) and math.isfinite(float(dp_disp)) and abs(float(pred_dp) - float(dp_disp)) >= 0.001:
                                pred_txt = f" P:{float(pred_dp):+.3f}%"
                    except Exception:
                        pred_txt = ""
                    tag = ""
                    try:
                        ok_age = float(_env_float("DASH_FOCUS_OK_AGE_SEC", 25.0) or 25.0)
                        if mid is None or float(mid or 0.0) <= 0.0:
                            tag = "[red]INVALID[/]"
                        elif age is None:
                            tag = "[yellow]AGE?[/]"
                        elif float(age) > ok_age:
                            tag = "[yellow]STALE[/]"
                        else:
                            dp_s = str(dp_txt or "")
                            if ("WAIT" in dp_s) and ("STALE" not in dp_s):
                                tag = "[grey50]WARMUP[/]"
                            else:
                                dec = None
                                try:
                                    phx = getattr(self.bot, "phoenix", None)
                                    if phx is not None and hasattr(phx, "get_last_decision"):
                                        dec = phx.get_last_decision(focus_sym)
                                except Exception:
                                    dec = None
                                ready = False
                                reason = ""
                                cf0 = None
                                conf_eff = 0.0
                                shlbl_eff = ""
                                try:
                                    if dec is not None:
                                        ready = bool(getattr(dec, "ready", False))
                                        reason = str(getattr(dec, "reason", "") or "")
                                        cf0 = getattr(dec, "confidence", None)
                                        _cfv = _parse_float_maybe(cf0)
                                        if _cfv is not None:
                                            conf_eff = float(_cfv)
                                        shlbl_eff = str(getattr(dec, "shadow_label", "") or "")
                                except Exception:
                                    pass
                                try:
                                    minc = float(getattr(getattr(self.bot, "cfg", None), "phoenix_min_conf", 0.20) or 0.20)
                                except Exception:
                                    minc = 0.20
                                ru = (reason or "").upper()
                                su = (shlbl_eff or "").upper()
                                if ("NO_DATA" in ru) or ("NODATA" in ru) or ("NOBOOK" in ru) or ("NO_DATA" in su) or ("NODATA" in su):
                                    tag = "[yellow]NO_DATA[/]"
                                elif conf_eff < max(0.01, float(minc) * 0.5):
                                    tag = "[yellow]LOW_CONF[/]"
                                elif not bool(ready):
                                    tag = "[grey50]WAIT[/]"
                                else:
                                    tag = "[green]READY[/]"
                    except Exception:
                        tag = ""
                    fb = ""
                    try:
                        if str(focus_pick_reason or "") and str(focus_pick_reason) != "OK":
                            fb = f" {str(focus_pick_reason)[:18]}"
                    except Exception:
                        fb = ""
                    t.add_row(
                        f"FOCUS {_run_short(focus_sym, 10):<10} {st_icon} "
                        + f"{dp_txt}{pred_txt} "
                        + (f"Age:{age_txt} " if age_txt else "")
                        + f"C:{int(max(0.0, min(1.0, float(cf0))) * 100)}%"
                        + (f" {tag}{fb}" if tag or fb else "")
                    )
                else:
                    t.add_row("FOCUS [red]INVALID[/] (no symbol)")
            except Exception:
                try:
                    t.add_row("FOCUS [red]INVALID[/] (render_err)")
                except Exception:
                    pass
            shown = 0
            for _, s0, state, dp, conf, sc, rsi_v, _m0 in rows:
                if shown >= topn:
                    break
                st_u = str(state or "FLAT").upper()
                if st_u.startswith("LONG"):
                    st_icon = "[green]▲[/]"
                elif st_u.startswith("SHORT"):
                    st_icon = "[red]▼[/]"
                else:
                    st_icon = "[grey37]●[/]"
                pho_last = None
                try:
                    phx0 = getattr(self.bot, "phoenix", None)
                    if phx0 is not None:
                        pho_last = phx0.get_last_decision(str(s0 or ""))
                except Exception:
                    pho_last = None
                if pho_last is not None:
                    try:
                        if (not isinstance(_m0, dict)) or bool(_m0.get("fallback") or _m0.get("top8_fill") or _m0.get("major_fill")) or float(conf or 0.0) <= 0.0001:
                            conf = float(getattr(pho_last, "confidence", conf) or conf)
                        if rsi_v is None:
                            rv = getattr(pho_last, "rsi", None)
                            if rv is not None:
                                rsi_v = float(rv)
                    except Exception:
                        pass
                mkt_dp = None
                try:
                    if s0 and s0 in t8_map:
                        _v = t8_map.get(s0)
                        mkt_dp = (float(_v) if _v is not None else None)
                except Exception:
                    mkt_dp = None
                if mkt_dp is None:
                    try:
                        if isinstance(_m0, dict):
                            for _k in ("chg_1h", "chg_pct", "change_pct", "priceChangePercent", "changePercent", "dayChangePercent", "pct", "percentChange", "change24h", "pct24h"):
                                if _m0.get(_k) is not None:
                                    mkt_dp = float(_m0.get(_k))
                                    break
                    except Exception:
                        mkt_dp = None
                age = None
                try:
                    if isinstance(_m0, dict):
                        if _m0.get("age_sec") is not None:
                            age = float(_m0.get("age_sec") or 0.0)
                        elif _m0.get("age_s") is not None:
                            age = float(_m0.get("age_s") or 0.0)
                        elif _m0.get("age") is not None:
                            age = float(_m0.get("age") or 0.0)
                        elif _m0.get("ts") is not None:
                            ts1 = float(_epoch_to_sec(_m0.get("ts") or 0.0) or 0.0)
                            if ts1 > 0.0:
                                age = max(0.0, float(time.time()) - ts1)
                except Exception:
                    age = None
                hist_ready = False
                try:
                    dq0 = None
                    if isinstance(px_hist, dict):
                        dq0 = px_hist.get(s0) or px_hist.get(_canon_symbol(s0))
                        if dq0 is None:
                            for al in _symbol_aliases(s0):
                                dq0 = px_hist.get(_canon_symbol(al))
                                if dq0 is not None:
                                    break
                    if dq0 is not None and len(dq0) >= 1:
                        _t_last, _p_last = dq0[-1]
                        _p_last = float(_p_last or 0.0)
                        hist_ready = math.isfinite(_p_last) and _p_last > 0.0
                    else:
                        hist_ready = False
                except Exception:
                    hist_ready = False
                is_stale = False
                try:
                    age_eff = age if age is not None else mkt_age_global
                    try:
                        if age_eff is None and str(mkt_state_global or '').upper().find('STALE') >= 0:
                            age_eff = float(health_thr) + 1.0
                    except Exception:
                        pass
                    is_stale = (age_eff is not None) and math.isfinite(float(age_eff)) and (float(age_eff) > float(health_thr))
                except Exception:
                    is_stale = False
                disp_dp = mkt_dp
                if is_stale:
                    dp_txt = "[yellow]STALE[/]"
                elif (disp_dp is None):
                    dp_txt = "[grey50]WAIT[/]"
                else:
                    try:
                        if not math.isfinite(float(disp_dp)):
                            disp_dp = None
                        elif abs(float(disp_dp)) > 50.0:
                            disp_dp = max(-50.0, min(50.0, float(disp_dp)))
                    except Exception:
                        disp_dp = None
                    if disp_dp is None:
                        dp_txt = "[grey50]WAIT[/]"
                    else:
                        dp_txt = f"{float(disp_dp):+.3f}%"
                        dp_txt = f"[green]{dp_txt}[/]" if float(disp_dp) >= 0 else f"[red]{dp_txt}[/]"
                conf_txt = f"{int(max(0.0, min(1.0, float(conf))) * 100)}%"
                conf_txt = f"[cyan]{conf_txt}[/]"
                sc_txt = f"{sc:+.3f}"
                sc_txt = f"[green]{sc_txt}[/]" if float(sc) >= 0 else f"[red]{sc_txt}[/]"
                rsi_txt = "--"
                try:
                    if rsi_v is not None:
                        rsi_txt = f"{float(rsi_v):.0f}%"
                except Exception:
                    rsi_txt = "--"
                sh_txt = "--"
                sh_lbl = ""
                try:
                    if isinstance(_m0, dict):
                        sh_v0 = _m0.get("phoenix_shadow_score")
                        if sh_v0 is None:
                            sh_v0 = _m0.get("phoenix_shadow")
                        sh_lbl = str(_m0.get("phoenix_shadow_lbl") or "")
                    else:
                        sh_v0 = None
                        sh_lbl = ""
                    if sh_v0 is None:
                        try:
                            sh_v1, sh_lbl1 = shadow_from_hist(str(s0 or ""))
                            if sh_v1 is not None:
                                sh_v0 = sh_v1
                                sh_lbl = str(sh_lbl1 or sh_lbl or "")
                        except Exception:
                            pass
                    if sh_v0 is None and pho_last is not None:
                        try:
                            sh_v0 = getattr(pho_last, "shadow_score", None)
                            sh_lbl = str(getattr(pho_last, "shadow_label", sh_lbl) or sh_lbl)
                        except Exception:
                            pass
                    if sh_v0 is not None:
                        sh_txt = f"{sh_lbl}{float(sh_v0):+.2f}"
                except Exception:
                    sh_txt, sh_lbl = "--", ""
                sym_s = str(s0 or "")
                try:
                    for _q in ("IRT", "USDT", "BTC", "ETH", "IRR", "USD", "USDC"):
                        if sym_s.endswith(_q) and len(sym_s) > len(_q):
                            sym_s = sym_s[:-len(_q)]
                            break
                except Exception:
                    pass
                sym_s = _run_short(sym_s, 7)
                if width0 > 0 and width0 < 80:
                    try:
                        cplain = int(max(0.0, min(1.0, float(conf))) * 100)
                    except Exception:
                        cplain = 0
                    c_tag = ""
                    try:
                        _st = getattr(self.bot, "_mkt_store", None)
                        if _st is not None:
                            _symk = str(s0 or "").strip()
                            _symq = _symk
                            try:
                                dq = str(getattr(getattr(self.bot, "cfg", None), "quote", "IRT") or "IRT").upper()
                            except Exception:
                                dq = "IRT"
                            try:
                                cs0 = _canon_symbol(_symk)
                            except Exception:
                                cs0 = _symk.upper()
                            try:
                                if cs0 and dq and (not cs0.endswith(dq)):
                                    rm = getattr(self.bot, "_resolved_symbol_map", None)
                                    if isinstance(rm, dict) and rm.get(cs0):
                                        cs0 = _canon_symbol(str(rm.get(cs0)))
                                    else:
                                        cs0 = _canon_pair(cs0, dq)
                            except Exception:
                                pass
                            _symq = cs0 or _symk
                            _ss = _st.get(str(_symq)) or _st.get(str(_symk))
                            _stt = str(getattr(_ss, "status", "") or "").upper()
                            if _stt and _stt not in ("OK",):
                                _rr = str(getattr(_ss, "reason", "") or _stt or "")
                                _ru = _rr.upper()
                                if ("UNSUP" in _ru) or ("UNRES" in _ru):
                                    c_tag = "U"
                                elif ("SPOT" in _ru) or ("FETCH_FAIL" in _ru):
                                    c_tag = "F"
                                elif ("RATE" in _ru) or ("LIMIT" in _ru):
                                    c_tag = "L"
                                elif "TIMEOUT" in _ru:
                                    c_tag = "T"
                                elif "ERROR" in _ru:
                                    c_tag = "E"
                                elif ("NO_TICK" in _ru) or ("MISSING" in _ru):
                                    c_tag = "N"
                                else:
                                    c_tag = "M"
                    except Exception:
                        c_tag = ""
                    try:
                        sh_s = _run_short(str(sh_txt or "--"), 6)
                    except Exception:
                        sh_s = str(sh_txt or "--")[:6]
                    if width0 >= 74:
                        t.add_row(f"{sym_s:<5} {st_icon} {dp_txt:<8} C{cplain:02d}{c_tag} R{rsi_txt:<3} SH{sh_s:<6} {sc_txt}")
                    else:
                        t.add_row(f"{sym_s:<5} {st_icon} {dp_txt:<8} C{cplain:02d}{c_tag} R{rsi_txt:<3} SH{sh_s:<6}")
                else:
                    t.add_row(
                        f"{_run_short(s0, 10):<10} {st_icon} {dp_txt:<10} C:{conf_txt:<5} "
                        f"R:{rsi_txt:<4} SH:{sh_txt:<7} S:{sc_txt}"
                    )
                shown += 1
            age_ok = None
            try:
                now = float(time.time())
                ts = float(getattr(self.bot, "_top8_ok_ts", 0.0) or 0.0)
                ts = ts / 1000.0 if ts and ts > 1e11 else ts
                if ts > 0.0 and ts <= (now + 5.0):
                    age = now - ts
                    max_age = float(_env_float("DASH_MAX_AGE_SEC", 60.0 * 60.0 * 24.0 * 365.0) or (60.0 * 60.0 * 24.0 * 365.0))
                    if math.isfinite(age) and 0.0 <= age <= max(1.0, max_age):
                        age_ok = age
            except Exception:
                age_ok = None
            age_s = fmt_age_s(age_ok) if age_ok is not None else "N/A"
            try:
                thr = dict(getattr(self.bot, "_hw_thresholds", {}) or {})
                top8_warn = float(thr.get("top8_warn") or _env_float("HEALTH_WD_TOP8_WARN_SEC", 3.0) or 3.0)
                top8_crit = float(thr.get("top8_crit") or _env_float("HEALTH_WD_TOP8_CRIT_SEC", 12.0) or 12.0)
                badge = "TOP8_OK"
                if age_ok is None:
                    badge = "TOP8_NA"
                else:
                    try:
                        if float(age_ok) >= float(top8_crit):
                            badge = "TOP8_CRIT"
                        elif float(age_ok) >= float(top8_warn):
                            badge = "TOP8_WARN"
                    except Exception:
                        pass
                title = f"PHOENIX TOP  {time.strftime('%H:%M:%S')}  {badge} {age_s}"
            except Exception:
                title = "PHOENIX TOP"
            return Panel(t, title=title, box=box.ROUNDED, padding=(0, 1))
        def dzh_panel():
            t = Table.grid(padding=(0, 1), expand=True)
            t.add_column(justify="left", overflow="fold")
            now = time.time()
            scan_age = market_age = api_age = mkt_skew = mkt_state = mkt_conf = None
            focus = {}
            try:
                snap = self.bot.snapshot() if getattr(self, "bot", None) is not None else {}
                focus = (snap.get("focus") or {}) if isinstance(snap, dict) else {}
                scan_age = focus.get("scan_age_sec", focus.get("radar_age_sec", None))
                market_age = focus.get("market_age_sec", None)
                mkt_state = focus.get("market_state", None)
                mkt_conf = focus.get("market_confidence", None)
                api_age = focus.get("api_age_sec", None)
                mkt_skew = focus.get("mkt_clock_skew_sec", None)
            except Exception:
                focus = {}
            safe_mode = False
            safe_reason = ""
            try:
                risk = getattr(self.bot, "risk", None)
                safe_mode = bool(getattr(risk, "safe_mode", False))
                safe_reason = str(getattr(risk, "safe_reason", "") or "").strip()
            except Exception:
                safe_mode = False
                safe_reason = ""
            net_soft_safe = False
            net_safe_scope = ""
            net_safe_reason = ""
            try:
                net = getattr(self, "net", None)
                if net is not None:
                    try:
                        if hasattr(net, "is_soft_safe"):
                            net_soft_safe = bool(net.is_soft_safe())
                        else:
                            net_soft_safe = bool(getattr(net, "_safe", False))
                    except Exception:
                        net_soft_safe = False
                    try:
                        if hasattr(net, "safe_scope"):
                            net_safe_scope = str(net.safe_scope() or "")
                    except Exception:
                        net_safe_scope = ""
                    try:
                        if hasattr(net, "safe_reason"):
                            net_safe_reason = str(net.safe_reason() or "").strip()
                    except Exception:
                        net_safe_reason = ""
            except Exception:
                net_soft_safe = False
                net_safe_scope = ""
                net_safe_reason = ""
            wallets_map = {}
            try:
                wallets_map = getattr(self.bot, "wallets", {}) or {}
            except Exception:
                wallets_map = {}
            open_orders = 0
            integrity_ok = True
            issues: List[str] = []
            locked: List[str] = []
            try:
                for wname, w in (wallets_map or {}).items():
                    if w is None:
                        integrity_ok = False
                        issues.append(f"{wname}: NO_WALLET")
                        continue
                    try:
                        open_orders += int(getattr(w, "open_orders_exch", 0) or 0)
                    except Exception:
                        pass
                    try:
                        if not bool(getattr(w, "last_orders_sync_ok", True)):
                            integrity_ok = False
                            err = str(getattr(w, "last_orders_sync_err", "") or "").strip()
                            issues.append(f"{wname}: ORD_SYNC {err[:52]}")
                    except Exception:
                        pass
                    try:
                        if bool(getattr(w, "sanity_halt", False)):
                            integrity_ok = False
                            rs = str(getattr(w, "sanity_reason", "") or "").strip()
                            issues.append(f"{wname}: SANITY {rs[:52]}")
                    except Exception:
                        pass
                    try:
                        if str(getattr(w, "last_engine_status", "") or "").upper().startswith("LOCKED"):
                            locked.append(f"{wname}:{_run_short(str(getattr(w,'last_engine_reason','') or ''), 28)}")
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                up_sec = float(time.time() - float(globals().get("_BOOT_TS", time.time()) or time.time()))
            except Exception:
                up_sec = 0.0
            try:
                radar_stale = float(_env_float("DASH_RADAR_STALE_SEC", 90.0) or 75.0)
            except Exception:
                radar_stale = 75.0
            try:
                api_stale = float(_env_float("DASH_API_STALE_SEC", 25.0) or 25.0)
            except Exception:
                api_stale = 25.0
            try:
                mkt_stale = float(_env_float("DASH_MKT_STALE_SEC", 12.0) or 12.0)
            except Exception:
                mkt_stale = 12.0
            hw_thr = {}
            try:
                _t0 = getattr(self.bot, "_hw_thr", None)
                if isinstance(_t0, dict):
                    for _k in ("mkt", "top8", "radar", "api"):
                        try:
                            _d = _t0.get(_k) if isinstance(_t0, dict) else None
                            if isinstance(_d, dict):
                                if "warn" in _d:
                                    hw_thr[f"{_k}_warn"] = float(_d.get("warn"))
                                if "crit" in _d:
                                    hw_thr[f"{_k}_crit"] = float(_d.get("crit"))
                        except Exception:
                            continue
            except Exception:
                hw_thr = {}
            def _thr(name: str, default: float) -> float:
                try:
                    v = hw_thr.get(str(name))
                    if v is None:
                        return float(default)
                    return float(v)
                except Exception:
                    return float(default)
            radar_warn = _thr("radar_warn", float(radar_stale))
            radar_crit = _thr("radar_crit", max(float(radar_warn) * 2.0, float(radar_warn) + 10.0))
            mkt_warn = _thr("mkt_warn", float(mkt_stale))
            mkt_crit = _thr("mkt_crit", max(float(mkt_warn) * 2.0, float(mkt_warn) + 5.0))
            api_warn = _thr("api_warn", float(api_stale))
            api_crit = _thr("api_crit", max(float(api_warn) * 2.0, float(api_warn) + 5.0))
            try:
                top8_stale = float(_env_float("DASH_TOP8_STALE_SEC", 120.0) or 120.0)
            except Exception:
                top8_stale = 120.0
            top8_warn = _thr("top8_warn", float(top8_stale))
            top8_crit = _thr("top8_crit", max(float(top8_warn) * 2.0, float(top8_warn) + 30.0))
            stale_flags = []
            try:
                if scan_age is None or (not math.isfinite(float(scan_age))):
                    stale_flags.append("RADAR:MISSING")
                elif float(scan_age) > float(radar_crit):
                    stale_flags.append(f"RADAR:CRIT({fmt_age_s(scan_age)})")
                elif float(scan_age) > float(radar_warn):
                    stale_flags.append(f"RADAR:WARN({fmt_age_s(scan_age)})")
            except Exception:
                stale_flags.append("RADAR:?")
            try:
                ms0 = str(mkt_state or "").upper().strip()
                if ms0 in ("CRITICAL", "DEGRADED"):
                    c0 = None
                    try:
                        if mkt_conf is not None:
                            c0 = int(float(mkt_conf))
                    except Exception:
                        c0 = None
                    if ms0 == "CRITICAL":
                        stale_flags.append(f"MKT:CRIT({c0}%)" if c0 is not None else "MKT:CRIT")
                    else:
                        stale_flags.append(f"MKT:DEG({c0}%)" if c0 is not None else "MKT:DEG")
                else:
                    if market_age is None or (not math.isfinite(float(market_age))):
                        stale_flags.append("MKT:MISSING")
                    elif float(market_age) > float(mkt_crit):
                        stale_flags.append(f"MKT:CRIT({fmt_age_s(market_age)})")
                    elif float(market_age) > float(mkt_warn):
                        stale_flags.append(f"MKT:WARN({fmt_age_s(market_age)})")
            except Exception:
                stale_flags.append("MKT:?")
            try:
                if api_age is None or (not math.isfinite(float(api_age))):
                    stale_flags.append("API:MISSING")
                elif float(api_age) > float(api_crit):
                    stale_flags.append(f"API:CRIT({fmt_age_s(api_age)})")
                elif float(api_age) > float(api_warn):
                    stale_flags.append(f"API:WARN({fmt_age_s(api_age)})")
            except Exception:
                stale_flags.append("API:?")
            veto_active_win = float(_env_float("DASH_VETO_ACTIVE_SEC", 45.0) or 45.0)
            vetoes_all = _VETO_REG.snapshot(now=now, include_stale=True)
            vetoes_active = []
            try:
                vetoes_active = [v for v in vetoes_all if v.age_sec(now) <= veto_active_win]
            except Exception:
                vetoes_active = []
            _default_hard_sources = {"SANITY", "LOCKED", "DZH", "PARISA", "SAFE", "SYMBOL", "PHOENIX", "ENGINE"}
            hard_sources, hard_sources_env_set, hard_all_sources, strict_unknown_hard = _parse_hard_veto_sources_env(_default_hard_sources)
            hard_vetoes_active = []
            soft_vetoes_active = []
            try:
                for v in (vetoes_active or []):
                    src = str(getattr(v, "source", "") or "").upper().strip()
                    is_hard = False
                    if src in ("DATA", "NET"):
                        if hard_sources_env_set and (hard_all_sources or src in hard_sources):
                            is_hard = True
                        else:
                            is_hard = False
                    else:
                        if hard_all_sources:
                            is_hard = True
                        elif src in hard_sources:
                            is_hard = True
                        else:
                            is_hard = (not hard_sources_env_set) or bool(strict_unknown_hard)
                    if is_hard:
                        hard_vetoes_active.append(v)
                    else:
                        soft_vetoes_active.append(v)
            except Exception:
                hard_vetoes_active = []
                soft_vetoes_active = list(vetoes_active or [])
            state = "LIVE"
            state_badge = "[green]LIVE[/]"
            if up_sec < float(_env_float("DASH_INIT_SEC", 15.0) or 15.0):
                state = "INIT"
                state_badge = "[cyan]INIT[/]"
            if stale_flags or soft_vetoes_active:
                if stale_flags and (any("STALE" in s for s in stale_flags) or any("INVALID" in s for s in stale_flags)):
                    state = "DEGRADED"
                    state_badge = "[yellow]DEGRADED[/]"
                elif soft_vetoes_active and not stale_flags:
                    state = "DEGRADED"
                    state_badge = "[yellow]DEGRADED[/]"
            if hard_vetoes_active:
                state = "VETOED"
                state_badge = "[magenta]VETOED[/]"
            if safe_mode:
                state = "SAFE"
                state_badge = "[red]SAFE[/]"
            t.add_row("STATE")
            st_line = f"{state_badge} | UP {fmt_age_s(up_sec)}"
            if safe_mode and safe_reason:
                try:
                    if str(safe_reason or "").startswith("HEALTH_SYS_"):
                        hs = str(getattr(self.bot, "_hw_state", "") or "").upper().strip()
                        if not hs:
                            hs = "SAFE"
                        try:
                            sc = float(getattr(self.bot, "_hw_score", 0.0) or 0.0)
                        except Exception:
                            sc = 0.0
                        try:
                            _sr = str(safe_reason or "")
                            _m = re.search(r"\bscore=([0-9]+(?:\.[0-9]+)?)", _sr)
                            if _m:
                                _sc2 = float(_m.group(1))
                                if math.isfinite(_sc2):
                                    sc = _sc2
                        except Exception:
                            pass
                        top8_age = None
                        try:
                            ts2 = float(getattr(self.bot, "_top8_ok_ts", 0.0) or 0.0)
                            ts2 = ts2 / 1000.0 if ts2 and ts2 > 1e11 else ts2
                            top8_age = (now - ts2) if ts2 > 0 else None
                        except Exception:
                            top8_age = None
                        safe_reason = (
                            f"HEALTH_SYS_{hs} score={sc:.1f} "
                            f"mkt={fmt_age_s(market_age)} top8={fmt_age_s(top8_age)} "
                            f"radar={fmt_age_s(scan_age)} api={fmt_age_s(api_age)}"
                        )
                except Exception:
                    pass
                st_line += f" | REASON {_run_short(safe_reason, 52)}"
            elif (not safe_mode) and bool(net_soft_safe) and str(net_safe_scope).upper() == "SYMBOL":
                st_line += f" | NET_SYM_SAFE {_run_short(net_safe_reason or 'SYMBOL', 40)}"
            elif hard_vetoes_active:
                st_line += f" | VETO {len(hard_vetoes_active)}"
            elif soft_vetoes_active and not stale_flags:
                st_line += f" | DEG {len(soft_vetoes_active)}"
            elif stale_flags:
                st_line += f" | {_run_short(','.join(stale_flags[:3]), 62)}"
            t.add_row(_run_short(st_line, 110))
            now_entry = None
            try:
                now_entry = float(time.time())
            except Exception:
                now_entry = 0.0
            allow_now, why_now = True, "ALLOW"
            try:
                pol = getattr(self.bot, "trade_policy", None)
                if pol is not None and hasattr(pol, "allow"):
                    allow_now, why_now = pol.allow("ENTRY")
            except Exception:
                allow_now, why_now = True, "ALLOW"
            try:
                if bool(safe_on) or bool(getattr(self.bot, "_engine_halted", False)):
                    allow_now = False
                    why_now = "DENY_SAFE_OR_HALTED"
            except Exception:
                pass
            try:
                if bool(hard_vetoes_active):
                    allow_now = False
                    why_now = "DENY_VETO_ACTIVE"
            except Exception:
                pass
            le = None
            try:
                le = getattr(self.bot, "_last_entry_attempt", None)
            except Exception:
                le = None
            le_recent = False
            le_age = None
            allow_last, why_last = None, None
            ctx_last = ""
            try:
                ttl_last = float(_env_float("DASH_ENTRY_LAST_TTL_SEC", 35.0) or 35.0)
            except Exception:
                ttl_last = 35.0
            try:
                if isinstance(le, dict) and le:
                    ts0 = float(le.get("ts", 0.0) or 0.0)
                    if ts0 > 0.0 and now_entry > 0.0:
                        le_age = max(0.0, now_entry - ts0)
                        if le_age <= float(ttl_last):
                            le_recent = True
                            w0 = str(le.get("wallet") or "").strip()
                            s0 = str(le.get("sym") or "").strip()
                            if w0 or s0:
                                ctx_last = f"{w0}/{s0}".strip("/")
                            try:
                                meta = le.get("meta")
                                if isinstance(meta, dict) and ("allow" in meta):
                                    allow_last = bool(meta.get("allow"))
                            except Exception:
                                allow_last = None
                            if allow_last is None:
                                try:
                                    st0 = str(le.get("status") or "").upper().strip()
                                    allow_last = st0.endswith("ALLOW")
                                except Exception:
                                    allow_last = None
                            try:
                                why_last = str(le.get("reason") or le.get("policy") or le.get("status") or ("ALLOW" if allow_last else "DENY"))
                            except Exception:
                                why_last = why_last
            except Exception:
                pass
            last_rej = ""
            last_rej_age = None
            try:
                now2 = float(time.time())
                best_ts = 0.0
                w_iter = []
                try:
                    if isinstance(wallets, dict):
                        w_iter = list(wallets.items())
                    else:
                        w_iter = list(wallets or [])
                except Exception:
                    w_iter = []
                for it in (w_iter or []):
                    try:
                        _wn, _w = it
                    except Exception:
                        continue
                    dq = getattr(_w, "trace", None)
                    if dq is None:
                        continue
                    try:
                        it2 = list(dq)
                    except Exception:
                        it2 = []
                    for row in reversed(it2):
                        if isinstance(row, dict) and str(row.get("event", "")) == "REJECT":
                            tsr = float(row.get("ts", 0.0) or 0.0)
                            if tsr > best_ts:
                                best_ts = tsr
                                last_rej = str(row.get("reason", "") or "")
                            break
                if best_ts > 0.0:
                    last_rej_age = max(0.0, now2 - best_ts)
            except Exception:
                pass
            try:
                b_now = "[green]OK[/]" if bool(allow_now) else "[red]BLOCK[/]"
                msg = f"NOW {b_now} {_run_short(str(why_now or ''), 48)}"
                if le_recent and (allow_last is not None or why_last):
                    b_last = "[green]ALLOW[/]" if bool(allow_last) else "[red]BLOCK[/]"
                    extra = f"LAST {b_last} {_run_short(str(why_last or ''), 48)}"
                    if ctx_last:
                        extra += f" ({_run_short(ctx_last, 18)})"
                    if le_age is not None:
                        extra += f" {fmt_age_s(le_age)} ago"
                    msg += " | " + extra
                if last_rej:
                    msg += f" | LAST_REJ {_run_short(last_rej, 46)} ({fmt_age_s(last_rej_age)})"
                t.add_row("ENTRY_POLICY")
                def _pol_reason(_allow: bool, _why: str) -> str:
                    w = str(_why or "").strip()
                    if not w:
                        return "OK" if bool(_allow) else "BLOCK"
                    wu = w.upper()
                    if bool(_allow) and (wu == "ALLOW" or wu.startswith("ALLOW_") or wu.startswith("ALLOW ")):
                        w = w[len("ALLOW"):].lstrip(" _:-")
                    if (not bool(_allow)) and (wu == "DENY" or wu.startswith("DENY_") or wu.startswith("DENY ")):
                        w = w[len("DENY"):].lstrip(" _:-")
                    if (not bool(_allow)) and (wu == "BLOCK" or wu.startswith("BLOCK_") or wu.startswith("BLOCK ")):
                        w = w[len("BLOCK"):].lstrip(" _:-")
                    return w if w else ("OK" if bool(_allow) else "BLOCK")
                now_icon = "[green]●[/]" if bool(allow_now) else "[red]●[/]"
                t.add_row(_run_short(f"NOW {now_icon} {_run_short(_pol_reason(bool(allow_now), str(why_now or '')), 52)}", 110))
                if le_recent and (allow_last is not None or why_last):
                    last_icon = "[green]●[/]" if bool(allow_last) else "[red]●[/]"
                    t.add_row(_run_short(f"LAST {last_icon} {_run_short(_pol_reason(bool(allow_last), str(why_last or '')), 52)} ({fmt_age_s(le_age)})", 110))
                if last_rej:
                    t.add_row(_run_short(f"LAST_REJ {_run_short(last_rej, 46)} ({fmt_age_s(last_rej_age)})", 110))
                try:
                    fs = str(getattr(self.bot, "focus_symbol", "") or getattr(self.bot, "_focus_symbol", "") or "")
                except Exception:
                    fs = ""
                try:
                    if not fs:
                        fs = str(getattr(getattr(self.bot, "health", None), "focus_symbol", "") or "")
                except Exception:
                    pass
                dec = None
                try:
                    pho = getattr(self.bot, "phoenix", None)
                    if pho is not None and fs:
                        dec = getattr(pho, "_state")(fs).last_decision
                except Exception:
                    dec = None
                t.add_row("SIGNAL_STATE")
                if dec is None:
                    t.add_row("NO_SIGNAL")
                else:
                    try:
                        t.add_row(_run_short(f"{fs} {str(getattr(dec, 'state', ''))} C{float(getattr(dec, 'confidence', 0.0) or 0.0)*100.0:.0f}% READY={bool(getattr(dec, 'ready', False))} REASON={_run_short(str(getattr(dec, 'reason', '')), 36)}", 110))
                    except Exception:
                        t.add_row(_run_short(f"{fs} SIGNAL_ERR", 110))
                t.add_row("EXEC_STATE")
                try:
                    t.add_row(_run_short(f"Exec:{str(hw_exec)} | MKT:{str(hw_mkt)} | API:{str(hw_api)} | RADAR:{str(hw_radar)}", 110))
                except Exception:
                    t.add_row("Exec:- | MKT:- | API:- | RADAR:-")
            except Exception:
                pass
            def _age_cell_wc(name: str, v: Optional[float], warn: float, crit: float) -> str:
                try:
                    if v is None:
                        return f"{name} [red]MISSING[/]"
                    v = float(v)
                    if not math.isfinite(v) or v < 0.0:
                        return f"{name} [red]MISSING[/]"
                    if v > float(crit):
                        return f"{name} [red]CRIT {fmt_age_s(v)}[/]"
                    if v > float(warn):
                        return f"{name} [yellow]WARN {fmt_age_s(v)}[/]"
                    return f"{name} [green]OK {fmt_age_s(v)}[/]"
                except Exception:
                    return f"{name} [red]ERR[/]"
            t.add_row("DATA AGE (GATE/RAW)")
            ages_raw = None
            try:
                ages_raw = getattr(self.bot, "_hw_ages_raw", None)
            except Exception:
                ages_raw = None
            if not (isinstance(ages_raw, dict) and ages_raw):
                ages_raw = {}
            t.add_row(_run_short(
                f"{_age_cell_wc('RADAR', ages_raw.get('radar', None), radar_warn, radar_crit)} | "
                f"{_age_cell_wc('MKT', ages_raw.get('mkt', None), mkt_warn, mkt_crit)} | "
                f"{_age_cell_wc('API', ages_raw.get('api', None), api_warn, api_crit)} | "
                f"{_age_cell_wc('TOP8', ages_raw.get('top8', None), top8_warn, top8_crit)}",
                120
            ))
            t.add_row("DATA AGE (UI/SNAPSHOT)")
            t.add_row(_run_short(
                f"{_age_cell_wc('RADAR', scan_age, radar_warn, radar_crit)} | "
                f"{_age_cell_wc('MKT', market_age, mkt_warn, mkt_crit)} | "
                f"{_age_cell_wc('API', api_age, api_warn, api_crit)} | "
                f"SKEW {fmt_age_s(mkt_skew)}",
                120
            ))
            try:
                st = getattr(self.bot, "_mkt_store", None)
                if st is not None and hasattr(st, "stale_symbols"):
                    try:
                        stale_after = float(_env_float("DASH_SYMBOL_STALE_SEC", 15.0) or 15.0)
                    except Exception:
                        stale_after = 15.0
                    items = st.stale_symbols(now=now, stale_after_sec=float(stale_after), limit=8)
                    if items:
                        t.add_row("STALE SYMS")
                        parts = []
                        for it in (items or [])[:8]:
                            try:
                                sym = str(it.get("symbol") or "")
                                stt = str(it.get("status") or "")
                                rs = str(it.get("reason") or "")
                                age = it.get("age_sec", None)
                                a_s = fmt_age_s(age) if age is not None else "N/A"
                                tag = f"{sym}:{stt[:3]}:{a_s}"
                                if rs:
                                    tag += f":{_run_short(rs, 18)}"
                                parts.append(tag)
                            except Exception:
                                continue
                        if parts:
                            t.add_row(_run_short(", ".join(parts), 120))
            except Exception:
                pass
            t.add_row("ORDERS")
            ord_line = f"OPEN {int(open_orders)}"
            if locked:
                ord_line += f" | LOCK {len(locked)}"
            t.add_row(_run_short(ord_line, 110))
            t.add_row("VETOES")
            if vetoes_active:
                for v in vetoes_active[:3]:
                    try:
                        dur = fmt_age_s(v.duration_sec(now))
                        line = f"{_run_short(v.wallet, 3)}/{_run_short(v.symbol, 10)} {v.source} { _run_short(v.reason, 24)} | dur {dur} | hits {int(v.hits)}"
                        t.add_row(_run_short(line, 110))
                        if v.release_hint:
                            t.add_row(_run_short(f"  rel: {v.release_hint}", 110))
                    except Exception:
                        continue
            else:
                if vetoes_all:
                    try:
                        v = vetoes_all[0]
                        dur = fmt_age_s(v.duration_sec(now))
                        ago = fmt_age_s(v.age_sec(now))
                        t.add_row(_run_short(f"None (last: {v.source} {_run_short(v.reason, 26)} dur {dur} ago {ago})", 110))
                    except Exception:
                        t.add_row("None")
                else:
                    t.add_row("None")
            t.add_row("EVENT FAILS")
            try:
                feed = getattr(self.bot, "feed", None)
                df = feed.depth_fail_snapshot() if hasattr(feed, "depth_fail_snapshot") else (getattr(feed, "_depth_fail", {}) if feed else {})
                items = []
                for sym, rec in (df or {}).items():
                    try:
                        streak = int((rec or {}).get("streak", 0) or 0)
                        last_fail = float((rec or {}).get("last_fail_ts", 0.0) or 0.0)
                        last_ok = float((rec or {}).get("last_ok_ts", 0.0) or 0.0)
                        err = str((rec or {}).get("last_err", "") or "")
                        if streak <= 0 and (now - last_fail) > 120.0:
                            continue
                        items.append((streak, last_fail, last_ok, sym, err))
                    except Exception:
                        continue
                items.sort(key=lambda x: (int(x[0]), float(x[1])), reverse=True)
                if items:
                    for streak, last_fail, last_ok, sym, err in items[:2]:
                        ts_age = fmt_age_s(now - float(last_fail or now)) if last_fail else "?"
                        t.add_row(_run_short(f"DEPTH_FAIL sym={_run_short(sym, 10)} retry={int(streak)} last={ts_age} err={_run_short(err, 44)}", 120))
                else:
                    t.add_row("None")
            except Exception:
                t.add_row("[red]INVALID[/] (depth telemetry)")
            try:
                rs = int(getattr(self.bot, "_hw_recover_streak", 0) or 0)
                nxt = float(getattr(self.bot, "_hw_next_recover_ts", 0.0) or 0.0)
                lok = float(getattr(self.bot, "_hw_last_recover_ok_ts", 0.0) or 0.0)
                lfail = float(getattr(self.bot, "_hw_last_recover_fail_ts", 0.0) or 0.0)
                rr = str(getattr(self.bot, "_hw_last_recover_reason", "") or "").strip()
                if rs > 0 or nxt > 0.0 or lfail > 0.0:
                    nxt_txt = "now" if (nxt <= 0.0 or nxt <= now) else fmt_age_s(float(nxt) - float(now))
                    lok_txt = ("-" if lok <= 0.0 else fmt_age_s(float(now) - float(lok)))
                    lfail_txt = ("-" if lfail <= 0.0 else fmt_age_s(float(now) - float(lfail)))
                    t.add_row(_run_short(f"HEALTH_RECOVER streak={rs} next={nxt_txt} ok={lok_txt} fail={lfail_txt} {_run_short(rr, 36)}", 120))
            except Exception:
                pass
            t.add_row("ACTIONS")
            if state == "LIVE":
                t.add_row("Entries: OK | Exits: OK | Cancel: AUTO")
            elif state == "DEGRADED":
                t.add_row("Entries: CAUTION (may veto) | Exits: OK | Cancel: AUTO")
            elif state == "VETOED":
                t.add_row("Entries: BLOCKED by VETO | Exits: OK | Cancel: AUTO")
            elif state == "SAFE":
                t.add_row("Entries: BLOCKED (SAFE) | Exits: OK | Cancel: AUTO")
            else:
                t.add_row("Warmup: collecting data | Entries: CAUTION | Exits: OK")
            t.add_row("INTEGRITY")
            if integrity_ok and (not safe_mode):
                t.add_row("[green]OK[/]" if not issues else "[yellow]WARN[/]")
            else:
                t.add_row("[red]WARN[/]")
            if issues:
                for it in issues[:2]:
                    t.add_row(_run_short(it, 110))
            return Panel(t, title="SYSTEM", box=box.ROUNDED, padding=(0, 1))
        def ai_status_panel():
            cfg = getattr(self.bot, "cfg", None)
            safe = bool(getattr(getattr(self.bot, "risk", None), "safe_mode", False))
            mode = "LIVE"
            try:
                if bool(getattr(cfg, "dry_run", False)):
                    mode = "DRY"
            except Exception:
                pass
            cash_total = 0.0
            equity_total = 0.0
            try:
                for w in getattr(self.bot, "wallets", {}).values():
                    cash_total += float(getattr(w, "cash_irt", 0.0) or 0.0)
                    equity_total += float(getattr(w, "equity_irt", 0.0) or 0.0)
            except Exception:
                pass
            rss = 0.0
            try:
                rss = float(_rss_mb(os.getpid()) or 0.0)
            except Exception:
                rss = 0.0
            rec = bool(getattr(self.bot, "recorder", None))
            db = str(getattr(cfg, "record_db_path", "") or "")
            autonomous = bool(getattr(cfg, "autonomous_ai", False))
            jitter = bool(getattr(cfg, "jitter_proxy", False))
            ladder = bool(getattr(cfg, "laddering", False))
            steps = int(getattr(cfg, "ladder_steps", 1) or 1)
            bps = float(getattr(cfg, "ladder_bps", 0.0) or 0.0)
            t = Table.grid(padding=(0, 1), expand=True)
            t.add_column(justify="left")
            t.add_row(f"MODE                       {mode}")
            if mode == "DRY":
                t.add_row("LIVE SWITCH                --live  (or export LIVE_TRADING=1)")
            t.add_row(f"AUTONOMOUS AI              {'ON' if autonomous else 'OFF'}")
            t.add_row(f"JITTER PROXY               {'ON' if jitter else 'OFF'}")
            t.add_row(f"LADDERING                  {'ON' if ladder else 'OFF'}")
            if ladder:
                t.add_row(f"LADDER CFG                 steps={steps} bps={bps:.2f}")
            t.add_row(f"SAFE MODE                  {'ON' if safe else 'OFF'}")
            t.add_row(f"TICK RECORDER              {'ON' if rec else 'OFF'}")
            if rec:
                t.add_row(f"DB                         {db or 'raz_ticks.sqlite'}")
            t.add_row(f"CASH TOTAL      {fmt_toman_from_irt(cash_total)} TOMAN")
            t.add_row(f"EQUITY TOTAL    {fmt_toman_from_irt(equity_total)} TOMAN")
            t.add_row(f"RSS                        {fmt_num(rss,1)} MB")
            return Panel(t, title="AI STATUS", box=box.ROUNDED, padding=(0, 1))
        def policy_panel():
            t = Table.grid(padding=(0, 0), expand=True)
            t.add_column(justify="left", overflow="fold")
            try:
                m_thr = float(getattr(getattr(self.bot, "cfg", None), "market_age_skip_sec", 4.0) or 4.0)
            except Exception:
                m_thr = 4.0
            try:
                dc_thr = float(_env_float("DEPTH_DISK_CACHE_MAX_AGE_SEC", (8.0 if _env_bool("TERMUX_MODE", False) else 4.0)) or 0.0)
            except Exception:
                dc_thr = 0.0
            try:
                man_ttl = float(_env_float("MANUAL_ORDER_TTL_SEC", 300.0) or 300.0)
            except Exception:
                man_ttl = 300.0
            try:
                any_h = float(_env_float("ORDER_MAX_AGE_HOURS", 48.0) or 48.0)
            except Exception:
                any_h = 48.0
            t.add_row("FRESHNESS")
            try:
                if dc_thr > 0:
                    t.add_row(f"MKT≤{m_thr:.1f}s   DEPTH_CACHE≤{dc_thr:.0f}s")
                else:
                    t.add_row(f"MKT≤{m_thr:.1f}s   DEPTH_CACHE≤off")
            except Exception:
                t.add_row(f"MKT≤{m_thr:.1f}s")
            t.add_row("MANUAL ORDERS")
            t.add_row(f"TTL≤{man_ttl:.0f}s   ABS≤{any_h:.0f}h")
            try:
                ok_ts = float(getattr(self.bot, "_top8_ok_ts", 0.0) or 0.0)
                age_top8 = (time.time() - ok_ts) if ok_ts > 0 else None
                if age_top8 is not None:
                    t.add_row(f"TOP8_OK {fmt_age_s(age_top8)}")
            except Exception:
                pass
            return Panel(t, title="POLICY", box=box.ROUNDED, padding=(0, 1))
        def banner_panel():
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            mode = "LIVE"
            try:
                if bool(getattr(getattr(self.bot, "cfg", None), "dry_run", False)):
                    mode = "DRY"
            except Exception:
                pass
            return Panel(Text(""), title=f"{now} {mode}", box=box.MINIMAL_DOUBLE_HEAD, padding=(0, 0))
        def _fmt_uptime(sec: Optional[float]) -> str:
            try:
                s = float(sec or 0.0)
            except Exception:
                s = 0.0
            if s < 0:
                s = 0.0
            h = int(s // 3600)
            m = int((s % 3600) // 60)
            ss = int(s % 60)
            return f"{h:02d}:{m:02d}:{ss:02d}"
        def _badge_by_threshold(val: Optional[float], warn: float, crit: float, higher_is_worse: bool = True) -> str:
            try:
                if val is None:
                    return "[❌]"
                v = float(val)
                if higher_is_worse:
                    if v >= crit:
                        return "[🔴]"
                    if v >= warn:
                        return "[🟡]"
                    return "[🟢]"
                else:
                    if v <= crit:
                        return "[🔴]"
                    if v <= warn:
                        return "[🟡]"
                    return "[🟢]"
            except Exception:
                return "[❌]"
        def _net_metrics(wallets_items) -> dict:
            lat = None
            jit = None
            try:
                pub = getattr(self.bot, "public", None)
                if pub is not None:
                    v = getattr(pub, "last_latency_ms", None)
                    if v is not None:
                        lat = float(v)
                    j = getattr(pub, "jitter_ms", None)
                    if j is not None:
                        jit = float(j)
            except Exception:
                pass
            try:
                for _n, w in (wallets_items or []):
                    if w is None:
                        continue
                    ex = getattr(w, "ex", None)
                    if ex is None:
                        continue
                    v = getattr(ex, "last_latency_ms", None)
                    if v is not None:
                        lat = max(float(v), float(lat)) if lat is not None else float(v)
                    j = getattr(ex, "jitter_ms", None)
                    if j is not None:
                        jit = max(float(j), float(jit)) if jit is not None else float(j)
            except Exception:
                pass
            lim = {}
            try:
                limiter = getattr(self.bot, "_limiter", None)
                if limiter is not None and hasattr(limiter, "metrics"):
                    lim = limiter.metrics() or {}
            except Exception:
                lim = {}
            rel = 100.0
            try:
                net = getattr(self.bot, "net", None)
                if net is not None and hasattr(net, "safe"):
                    if not bool(net.safe()):
                        rel -= 20.0
            except Exception:
                pass
            try:
                br = getattr(getattr(self.bot, "public", None), "_breaker", None)
                if br is None:
                    br = getattr(getattr(self.bot, "public", None), "breaker", None)
                if br is not None and hasattr(br, "is_open"):
                    if bool(br.is_open()):
                        rel -= 60.0
                try:
                    err = float(getattr(br, "_errors", 0.0) or 0.0)
                    mx = float(getattr(br, "max_errors", 0.0) or 0.0)
                    if mx > 0:
                        rel -= min(25.0, (err / mx) * 25.0)
                except Exception:
                    pass
            except Exception:
                pass
            rel = float(max(0.0, min(100.0, rel)))
            return {"lat_ms": lat, "jit_ms": jit, "lim": lim, "rel_pct": rel}
        def raz_core_header_panel(focus: dict, wallets_items) -> Panel:
            up = _fmt_uptime(time.time() - float(globals().get("_BOOT_TS", time.time()) or time.time()))
            pid = int(globals().get("_BOOT_PID", os.getpid()) or os.getpid())
            loop_age = None
            try:
                last_cycle = float(getattr(self.bot, "_last_cycle_ts", 0.0) or 0.0)
                loop_age = (time.time() - last_cycle) if last_cycle > 0 else None
            except Exception:
                loop_age = None
            scan_age = focus.get("scan_age_sec", None)
            stall = "OK"
            if (loop_age is not None and float(loop_age) > 20.0) or (scan_age is not None and float(scan_age) > 35.0):
                stall = "PARTIAL_STALL"
            if (loop_age is not None and float(loop_age) > 45.0) or (scan_age is not None and float(scan_age) > 90.0):
                stall = "STALL"
            integrity = 100.0
            try:
                api_age = focus.get("api_age_sec", None)
                mkt_skew = focus.get("mkt_clock_skew_sec", None)
                mkt_age = focus.get("market_age_sec", None)
                if api_age is None and mkt_age is None:
                    integrity -= 35.0
                if api_age is not None and float(api_age) > 25.0:
                    integrity -= 20.0
                if mkt_age is not None and float(mkt_age) > 10.0:
                    integrity -= 10.0
                if scan_age is not None and float(scan_age) > 35.0:
                    integrity -= 20.0
            except Exception:
                integrity -= 10.0
            try:
                for _n, w in (wallets_items or []):
                    if w is None:
                        continue
                    if not bool(getattr(w, "last_orders_sync_ok", True)):
                        integrity -= 10.0
            except Exception:
                pass
            try:
                net = getattr(self.bot, "net", None)
                if net is not None and hasattr(net, "safe") and (not bool(net.safe())):
                    integrity -= 10.0
            except Exception:
                pass
            integrity = float(max(0.0, min(100.0, integrity)))
            dry = "OFF"
            thr = "ASYNC"
            mem = f"{self._rss_mb():.0f}MB"
            title = f"RAZ-CORE [PID:{pid}]"
            line1 = f"BUILD: {PHOENIX_BUILD}  UP: {up}"
            line2 = f"STAT: {'⚠️ ' if stall!='OK' else ''}{stall} │ INTG: {integrity:.0f}% │ DRY: {dry} │ THR: {thr} │ MEM: {mem}"
            body = Text(line1 + "\n" + line2, overflow="fold")
            return Panel(body, title=title, box=box.DOUBLE, padding=(0, 1))
        def net_resilience_panel(focus: dict, wallets_items) -> Panel:
            m = _net_metrics(wallets_items)
            lat = m.get("lat_ms", None)
            jit = m.get("jit_ms", None)
            rel = float(m.get("rel_pct", 0.0) or 0.0)
            lim = m.get("lim", {}) or {}
            scan_age = focus.get("scan_age_sec", None)
            mkt_age = focus.get("market_age_sec", None)
            api_age = focus.get("api_age_sec", None)
            mkt_skew = focus.get("mkt_clock_skew_sec", None)
            loop_age = None
            try:
                last_cycle = float(getattr(self.bot, "_last_cycle_ts", 0.0) or 0.0)
                loop_age = (time.time() - last_cycle) if last_cycle > 0 else None
            except Exception:
                loop_age = None
            util = None
            try:
                util = float(lim.get("util_pct", None))
            except Exception:
                util = None
            sync = "SYNC"
            if (scan_age is not None and float(scan_age) > 35.0) or (api_age is not None and float(api_age) > 30.0):
                sync = "DESYNC"
            try:
                for _n, w in (wallets_items or []):
                    if w is None:
                        continue
                    if not bool(getattr(w, "last_orders_sync_ok", True)):
                        sync = "DESYNC"
                        break
            except Exception:
                pass
            isp = "STABLE"
            try:
                net = getattr(self.bot, "net", None)
                if net is not None and hasattr(net, "safe") and (not bool(net.safe())):
                    isp = "UNSTABLE"
            except Exception:
                pass
            lat_s = f"{lat:.0f}ms" if lat is not None else "N/A"
            jit_s = f"{jit:.0f}ms" if jit is not None else "N/A"
            rel_s = f"{rel:.0f}%"
            util_s = f"{util:.0f}%" if util is not None else "N/A"
            t = Table.grid(expand=True)
            t.add_column(ratio=1)
            t.add_column(ratio=1)
            left = (
                f"LAT: {lat_s} {_badge_by_threshold(lat, warn=250.0, crit=400.0)} │ "
                f"JIT: {jit_s} {_badge_by_threshold(jit, warn=60.0, crit=120.0)} │ "
                f"RADAR: {fmt_age_s(scan_age)} {_badge_by_threshold(scan_age, warn=25.0, crit=45.0)} │ "
                f"MKT: {fmt_age_s(mkt_age)} {_badge_by_threshold(mkt_age, warn=3.0, crit=8.0)} │ "
                f"API: {fmt_age_s(api_age)} {_badge_by_threshold(api_age, warn=10.0, crit=25.0)} │ "
                f"SYNC: {sync} {'[🛑]' if sync=='DESYNC' else '[🟢]'}"
            )
            right = (
                f"REL: {rel_s} {_badge_by_threshold(rel, warn=60.0, crit=40.0, higher_is_worse=False)}   │ "
                f"LIM: {util_s} {_badge_by_threshold(util, warn=80.0, crit=95.0)}     │ "
                f"LOOP: {fmt_age_s(loop_age)} {_badge_by_threshold(loop_age, warn=18.0, crit=27.0)}  │ "
                f"ISP: {isp} {'[🟢]' if isp=='STABLE' else '[🔴]'}"
            )
            t.add_row(left)
            t.add_row(right)
            return Panel(t, title="📡 NET-RESILIENCE (IR-ADAPTIVE)", box=box.ROUNDED, padding=(0, 1))
        def multi_core_asset_panel(wallets_items) -> Panel:
            tb = Table(show_header=True, header_style="bold", box=box.SIMPLE_HEAVY)
            tb.add_column("ID", justify="left", width=3)
            tb.add_column("EQUITY", justify="right")
            tb.add_column("CASH (CA)", justify="right")
            tb.add_column("ORD", justify="right", width=4)
            tb.add_column("Δ-24H", justify="right")
            tb.add_column("RISK_EXP", justify="left")
            tb.add_column("HEALTH", justify="left", width=8)
            tb.add_column("STATUS", justify="left", width=8)
            tot_eq = 0.0
            tot_delta = 0.0
            max_dd_limit = None
            try:
                max_dd_limit = float(getattr(getattr(self.bot, "risk", None), "max_dd", None))
            except Exception:
                max_dd_limit = None
            for wname, w in (wallets_items or []):
                if w is None:
                    tb.add_row(str(wname), "N/A", "N/A", "0", "N/A", "N/A", "❌", "NO-W")
                    continue
                eq = float(getattr(w, "equity_irt", 0.0) or 0.0)
                ca = float(getattr(w, "cash_irt", 0.0) or 0.0)
                ordc = int(getattr(w, "open_orders_exch", 0) or 0)
                dlt = float(getattr(w, "_eq_delta_24h", 0.0) or 0.0)
                tot_eq += eq
                tot_delta += dlt
                exp = 0.0
                try:
                    exp = 1.0 - (ca / eq) if eq > 0 else 0.0
                except Exception:
                    exp = 0.0
                if exp < 0.15:
                    risk_exp = "LOW"
                elif exp < 0.35:
                    risk_exp = "STABLE"
                elif exp < 0.60:
                    risk_exp = "HIGH"
                else:
                    risk_exp = "CRITICAL"
                health = "🟢 OK"
                status = "IDLE"
                try:
                    if bool(getattr(w, "sanity_halt", False)) and float(getattr(w, "sanity_until_ts", 0.0) or 0.0) > time.time():
                        status = "LOCK"
                        health = "❌ SYNC"
                    elif ordc > 0:
                        status = "HOLD"
                        if not bool(getattr(w, "last_orders_sync_ok", True)):
                            status = "LOCK"
                            health = "❌ SYNC"
                        else:
                            age0 = getattr(w, "open_orders_oldest_age_sec", None)
                            if age0 is not None and float(age0) > 45.0:
                                health = "🟡 LAG"
                    elif len(getattr(w, "positions", {}) or {}) > 0:
                        status = "RUN"
                        health = "🟢 OK"
                except Exception:
                    pass
                ca_s = f"{ca:,.0f}"
                if ca < 10_000.0:
                    ca_s += " [❗]"
                eq_s = _mid_short(eq)
                dlt_pct = (dlt / eq) if eq > 0 else 0.0
                tb.add_row(str(wname), eq_s, ca_s, str(ordc), fmt_pct(dlt_pct), risk_exp, health, status)
            pnl = (tot_delta / tot_eq) if tot_eq > 0 else 0.0
            dd_s = f"{(max_dd_limit*100):.1f}%" if (max_dd_limit is not None and max_dd_limit > 0) else "N/A"
            mode = "ADAPTIVE"
            try:
                mode = str(getattr(getattr(self.bot, "cfg", None), "mode", None) or mode)
            except Exception:
                pass
            footer = f"TOT EQ: {_mid_short(tot_eq)} │ PNL: {fmt_pct(pnl)} │ MAX_DD(limit): {dd_s} │ MODE: {mode}"
            g = Table.grid(expand=True)
            g.add_row(tb)
            g.add_row(Text(footer, overflow="fold"))
            return Panel(g, title="💳 MULTI-CORE ASSET DEPLOYMENT", box=box.ROUNDED, padding=(0, 1))
        def execution_brain_panel(wallets_items, focus: dict) -> Panel:
            lines = []
            try:
                recent = list(self.bot.logger.ring.last_important(12) or [])
            except Exception:
                recent = []
            recent_err = " | ".join([str(x) for x in recent if ("Error" in str(x) or "Exception" in str(x) or "TypeError" in str(x))][:2])
            for wname, w in (wallets_items or []):
                if w is None:
                    lines.append(f"[{wname}] NO WALLET")
                    continue
                st = str(getattr(w, "last_engine_status", "") or "").strip()
                rs = str(getattr(w, "last_engine_reason", "") or "").strip()
                rej = str(getattr(w, "last_reject_reason", "") or "").strip()
                if not st:
                    st = "∅ NULL"
                msg = rs or rej or str(getattr(w, "last_event", "") or "").strip()
                if msg:
                    msg = msg.replace("\n", " ")
                msg = (msg[:90] + "…") if len(msg) > 90 else msg
                lines.append(f"[{wname}] {st:<6} │ {msg}")
            try:
                cfg = getattr(self.bot, "cfg", None)
                max_bps = float(getattr(cfg, "dzh_spread_max_bps", 10.0) or 10.0)
                sym0 = ""
                try:
                    sym0 = (getattr(cfg, "symbols", []) or [""])[0]
                except Exception:
                    sym0 = ""
                spr = None
                if sym0 and hasattr(self.bot, "feed") and self.bot.feed is not None:
                    try:
                        ob = self.bot.feed._cache.get(_canon_symbol(sym0))
                        if ob and isinstance(ob, tuple):
                            top = ob[1]
                            spr = float(getattr(top, "spread_bps", None))
                    except Exception:
                        spr = None
                if spr is not None:
                    lines.append(f"SPREAD: {spr:.0f}bps > MAX: {max_bps:.0f}bps" if spr > max_bps else f"SPREAD: {spr:.0f}bps <= MAX: {max_bps:.0f}bps")
            except Exception:
                pass
            if recent_err:
                lines.append(f"RECENT: {recent_err}")
            body = "\n".join(lines) if lines else "N/A"
            return Panel(Text(body, overflow="fold", no_wrap=False), title="🧠 EXECUTION BRAIN (HEURISTICS)", box=box.ROUNDED, padding=(0, 1))
        def surgical_repairs_panel(wallets_items, focus: dict) -> Panel:
            repairs = []
            scan_age = focus.get("scan_age_sec", None)
            api_age = focus.get("api_age_sec", None)
            mkt_skew = focus.get("mkt_clock_skew_sec", None)
            lat = _net_metrics(wallets_items).get("lat_ms", None)
            try:
                if scan_age is not None and float(scan_age) > 35.0:
                    repairs.append(f"❌ CRIT: Radar stale ({fmt_age_s(scan_age)}). Check market feed / restart network.")
            except Exception:
                pass
            try:
                for _n, w in (wallets_items or []):
                    if w is None:
                        continue
                    ordc = int(getattr(w, "open_orders_exch", 0) or 0)
                    locked = float(getattr(w, "cash_total_irt", 0.0) or 0.0) - float(getattr(w, "cash_irt", 0.0) or 0.0)
                    if ordc > 0 and locked > 0:
                        repairs.append(f"⚠️ SYNC: Force-purge ghost orders -> {str(_n)} LOCKED ≈ {locked:,.0f} IRT")
                        break
            except Exception:
                pass
            try:
                if api_age is None:
                    repairs.append("⚠️ API: API age N/A. Ensure public snapshot endpoint is reachable.")
                elif float(api_age) > 25.0:
                    repairs.append(f"⚠️ API: Snapshot stale ({fmt_age_s(api_age)}). Raise timeouts / check connectivity.")
            except Exception:
                pass
            try:
                if lat is not None and float(lat) > 300.0:
                    repairs.append("🚀 OPTI: High latency detected. Consider raising Alpha_Threshold (e.g., +0.3% to +0.8%)")
            except Exception:
                pass
            if not repairs:
                repairs = ["✅ No critical repairs suggested (system stable)."]
            body = "\n".join([f"{i+1}. {r}" for i, r in enumerate(repairs[:6])])
            return Panel(Text(body, overflow="fold", no_wrap=False), title="🛠️ SURGICAL REPAIRS (GROWTH QUEUE)", box=box.ROUNDED, padding=(0, 1))
        def alpha_reclaim_panel(ordered_syms, wallets_items, focus: dict) -> Panel:
            alpha = Table(show_header=True, header_style="bold", box=box.SIMPLE_HEAVY)
            alpha.add_column("SYM", justify="left")
            alpha.add_column("SIGNAL", justify="left")
            alpha.add_column("BPS", justify="right", width=5)
            cfg = getattr(self.bot, "cfg", None)
            max_bps = float(getattr(cfg, "dzh_spread_max_bps", 10.0) or 10.0)
            ttl = 1.2
            try:
                ttl = float(getattr(getattr(self.bot, "feed", None), "_ttl", ttl) or ttl)
            except Exception:
                ttl = 1.2
            rows = []
            try:
                if hasattr(self.bot, "get_top8_snapshot"):
                    top8 = list(self.bot.get_top8_snapshot() or [])
                    for r in top8[:8]:
                        sym = str(r.get("symbol") or "").strip()
                        if sym:
                            rows.append(_canon_symbol(sym))
            except Exception:
                pass
            if not rows:
                rows = list(ordered_syms or [])[:8]
            for sym in rows[:8]:
                sig = "OK"
                bps = None
                try:
                    if hasattr(self.bot, "feed") and self.bot.feed is not None:
                        entry = self.bot.feed._cache.get(_canon_symbol(sym))
                        if entry and isinstance(entry, tuple):
                            ts0 = float(entry[0] or 0.0)
                            top = entry[1]
                            bps = float(getattr(top, "spread_bps", 0.0) or 0.0)
                            age = time.time() - ts0 if ts0 > 0 else None
                            if age is not None and age > max(10.0, ttl * 4.0):
                                sig = "STALE"
                except Exception:
                    pass
                if bps is None:
                    bps = 0.0
                if bps > max_bps:
                    sig = "STALE" if sig == "STALE" else "WIDE"
                alpha.add_row(sym, sig, f"{bps:.0f}")
            rec = Table(show_header=True, header_style="bold", box=box.SIMPLE_HEAVY)
            rec.add_column("ID", justify="left", width=4)
            rec.add_column("TARGET", justify="left")
            rec.add_column("STATUS", justify="left")
            rec.add_column("+EXPECT_CA", justify="right")
            gid = 1
            for wname, w in (wallets_items or []):
                if w is None:
                    continue
                ordc = int(getattr(w, "open_orders_exch", 0) or 0)
                locked = float(getattr(w, "cash_total_irt", 0.0) or 0.0) - float(getattr(w, "cash_irt", 0.0) or 0.0)
                if ordc > 0 and locked > 0:
                    rec.add_row(f"#G{gid}", f"{wname}-LOCK", "[ORPHAN_LOCK]", f"{locked:,.0f}")
                    gid += 1
            if gid == 1:
                rec.add_row("-", "-", "OK", "0")
            cols = Columns([alpha, rec], expand=True, equal=True)
            return Panel(cols, title="📊 ALPHA SCANNER   ━   ⚡ RECLAIM & RECOVERY", box=box.ROUNDED, padding=(0, 1))
        def render_raz_core(ordered_syms, wallets_items, logs_panel: Panel, narrow: bool) -> Layout:
            try:
                snap = self.bot.snapshot() if getattr(self, "bot", None) is not None else {}
                focus = (snap.get("focus") or {}) if isinstance(snap, dict) else {}
            except Exception:
                focus = {}
            layout = Layout()
            layout.split_column(
                Layout(name="hdr", size=4),
                Layout(name="net", size=5),
                Layout(name="assets", ratio=5),
                Layout(name="brain", ratio=3),
                Layout(name="repairs", ratio=3),
                Layout(name="alpha", ratio=3),
                Layout(name="logs", size=7),
            )
            layout["hdr"].update(raz_core_header_panel(focus, wallets_items))
            layout["net"].update(net_resilience_panel(focus, wallets_items))
            layout["assets"].update(multi_core_asset_panel(wallets_items))
            layout["brain"].update(execution_brain_panel(wallets_items, focus))
            layout["repairs"].update(surgical_repairs_panel(wallets_items, focus))
            layout["alpha"].update(alpha_reclaim_panel(ordered_syms, wallets_items, focus))
            layout["logs"].update(logs_panel)
            return layout
        def render() -> Layout:
            cfg = getattr(self.bot, "cfg", None)
            symbols = list(getattr(cfg, "symbols", []) or [])
            pri = list(getattr(cfg, "symbol_priority", []) or [])
            if pri:
                ordered = list(dict.fromkeys([_canon(s) for s in pri] + [_canon(s) for s in symbols]))
            else:
                ordered = [_canon(s) for s in symbols]
            wm = getattr(self.bot, "wallets", {}) or {}
            wallets = []
            for _slot in (1, 2, 3):
                _name = f"W{_slot}"
                wallets.append((_name, wm.get(_name)))
            left_items = []
            for wname, w in wallets:
                if w is None:
                    left_items.append(Panel("NO WALLET", title=str(wname), box=box.ROUNDED, padding=(0, 1)))
                else:
                    left_items.append(wallet_panel(str(wname), w))
            if not left_items:
                left_items = [Panel("N/A", title="W1", box=box.ROUNDED)]
            main_sym = ordered[0] if ordered else ""
            phoenix = phoenix_panel(main_sym) if main_sym else Panel("N/A", title="PHOENIX", box=box.ROUNDED)
            dzh = dzh_panel()
            policy = policy_panel()
            ai = ai_status_panel()
            try:
                snap = self.bot.snapshot() if getattr(self, "bot", None) is not None else {}
                focus = (snap.get("focus") or {}) if isinstance(snap, dict) else {}
                scan_age = focus.get("scan_age_sec", None)
                market_age = focus.get("market_age_sec", None)
                api_age = focus.get("api_age_sec", None)
                mkt_skew = focus.get("mkt_clock_skew_sec", None)
            except Exception:
                scan_age = market_age = api_age = None
            hs = ""
            hs_score = None
            try:
                hs = str(getattr(self.bot, "_hw_state", "") or "").upper().strip()
                if hs == "LIVE":
                    hs = "OK"
            except Exception:
                hs = ""
            try:
                hs_score = float(getattr(self.bot, "_hw_score", None))
            except Exception:
                hs_score = None
            top8_age = None
            try:
                now_e2 = float(time.time())
                now_m2 = float(time.monotonic())
                a2 = float("inf")
                try:
                    ts_m = float(getattr(self.bot, "_top8_ok_mono_ts", 0.0) or 0.0)
                    if ts_m > 0.0:
                        a2 = min(a2, max(0.0, now_m2 - ts_m))
                except Exception:
                    pass
                try:
                    ts_e = float(getattr(self.bot, "_top8_ok_ts", 0.0) or 0.0)
                    ts_e = ts_e / 1000.0 if ts_e and ts_e > 1e11 else ts_e
                    if ts_e > 0.0:
                        a2 = min(a2, max(0.0, now_e2 - ts_e))
                except Exception:
                    pass
                top8_age2 = None if (not math.isfinite(float(a2))) or a2 == float("inf") else float(a2)
            except Exception:
                top8_age2 = None
            hw_score = None
            try:
                hw_score = float(getattr(self.bot, "_hw_score", None))
            except Exception:
                hw_score = None
            hw_state = None
            try:
                hw_state = str(getattr(self.bot, "_hw_state", None) or "").upper().strip() or None
            except Exception:
                hw_state = None
            safe_on = False
            safe_reason = ""
            safe_scope = "GLOBAL"
            safe_rem = None
            try:
                net = getattr(self.bot, "net", None)
                if net is not None:
                    try:
                        if hasattr(net, "is_safe_mode"):
                            safe_on = bool(net.is_safe_mode())
                    except Exception:
                        pass
                    try:
                        safe_reason = str(net.safe_reason() if hasattr(net, "safe_reason") else getattr(net, "_safe_reason", "") or "")
                    except Exception:
                        safe_reason = str(getattr(net, "_safe_reason", "") or "")
                    try:
                        safe_scope = str(net.safe_scope() if hasattr(net, "safe_scope") else getattr(net, "_safe_scope", "GLOBAL") or "GLOBAL")
                    except Exception:
                        safe_scope = str(getattr(net, "_safe_scope", "GLOBAL") or "GLOBAL")
                    try:
                        if hasattr(net, "pause_remaining"):
                            safe_rem = float(net.pause_remaining() or 0.0)
                    except Exception:
                        safe_rem = None
            except Exception:
                pass
            try:
                risk = getattr(self.bot, "risk", None)
                if risk is not None and bool(getattr(risk, "safe_mode", False)):
                    safe_on = True
                    rr = str(getattr(risk, "safe_reason", "") or "")
                    if rr:
                        safe_reason = rr
                    rs = str(getattr(risk, "safe_scope", "") or "")
                    if rs:
                        safe_scope = rs
            except Exception:
                pass
            lines = []  # type: List[str]
            hb = "N/A"
            summary = ""
            head_max = int(_env_int("DASH_HEAD_MAX_CHARS", 260) or 260)
            warn_err: List[str] = []
            crashes: List[str] = []
            try:
                _lp = None
                try:
                    _lp = getattr(cfg, "watchdog_heartbeat_file", None)
                except Exception:
                    _lp = None
                if not _lp:
                    _lp = os.path.join("logs", "trading_bot.log")
                _tail = _tail_lines(str(_lp), max_lines=60, max_bytes=65536)
                for _ln in (_tail or []):
                    if ("Traceback" in _ln) or ("ERROR" in _ln) or ("CRITICAL" in _ln) or ("Exception" in _ln):
                        warn_err.append(str(_ln))
                warn_err = warn_err[-6:]
            except Exception:
                warn_err = []
            try:
                _cp = str(os.getenv("PP200_LOG_PATH", "") or _PP200_DEFAULT_PATH)
                _ct = _tail_lines(_cp, max_lines=12, max_bytes=65536)
                for _ln in (_ct or []):
                    _s = _pp200_redact(str(_ln))
                    if _s:
                        crashes.append(_s)
                crashes = crashes[-4:]
            except Exception:
                crashes = []
            head = f"🧠 Health:{(hw_state or 'LIVE')}"
            hw_exec = None
            try:
                hw_exec = str(getattr(self.bot, "_hw_want_exec", None) or "").upper().strip() or None
            except Exception:
                hw_exec = None
            if hw_exec and hw_exec not in ("INIT", "LIVE"):
                head += f" | Exec:{hw_exec}"
                try:
                    entry_allow = None
                    entry_reason = ""
                    entry_ctx = ""
                    try:
                        le = getattr(self.bot, "_last_entry_attempt", None)
                        if isinstance(le, dict) and le:
                            try:
                                ts_le = float(le.get("ts") or 0.0)
                            except Exception:
                                ts_le = 0.0
                            if ts_le > 0.0 and (float(time.time()) - ts_le) <= float(_env_float("DASH_ENTRY_CTX_MAX_AGE_SEC", 30.0) or 30.0):
                                try:
                                    w0 = str(le.get("wallet") or "").strip()
                                    s0 = str(le.get("sym") or "").strip()
                                    entry_ctx = f"{w0}:{s0}".strip(":")
                                except Exception:
                                    entry_ctx = ""
                                aa = None
                                try:
                                    meta = le.get("meta", None)
                                    if isinstance(meta, dict) and ("allow" in meta):
                                        aa = meta.get("allow")
                                except Exception:
                                    aa = None
                                if aa is None:
                                    try:
                                        st0 = str(le.get("status") or "").upper().strip()
                                        aa = st0.endswith("ALLOW")
                                    except Exception:
                                        aa = None
                                entry_allow = bool(aa) if aa is not None else entry_allow
                                try:
                                    entry_reason = str(le.get("reason") or le.get("policy") or le.get("status") or "")
                                except Exception:
                                    entry_reason = entry_reason
                    except Exception:
                        pass
                    if entry_allow is None:
                        entry_allow = True
                        if safe_on:
                            entry_allow = False
                            entry_reason = "SAFE"
                        else:
                            stx = str(hw_exec or "OK").upper()
                            if stx == "CRITICAL":
                                entry_allow = False
                                entry_reason = "HEALTH_CRIT"
                            elif stx == "DEGRADED":
                                allow_deg = False
                                try:
                                    if bool(_env_bool("TERMUX_MODE", False)) and bool(_env_bool("TERMUX_ALLOW_ENTRY_DEGRADED", True)):
                                        allow_deg = True
                                except Exception:
                                    allow_deg = False
                                if not allow_deg:
                                    entry_allow = False
                                    entry_reason = "HEALTH_DEG"
                                else:
                                    entry_reason = "DEG_TERMUX"
                    trig = ""
                    try:
                        eb = getattr(self.bot, "_hw_exec_block", None)
                        if isinstance(eb, dict) and eb:
                            cause = str(eb.get("cause") or "")
                            lvl = str(eb.get("level") or "")
                            age = eb.get("age_s", None)
                            warn = eb.get("warn", None)
                            crit = eb.get("crit", None)
                            if cause:
                                if age is not None and warn is not None and crit is not None:
                                    trig = f"{cause}:{(lvl[:1] or '')} age={fmt_age_s(age)} thr={float(warn):.0f}/{float(crit):.0f}"
                                elif age is not None:
                                    trig = f"{cause}:{(lvl[:1] or '')} age={fmt_age_s(age)}"
                    except Exception:
                        trig = ""
                    head += f" | ENTRY:{'ALLOW' if entry_allow else 'BLOCK'}"
                    if entry_ctx:
                        head += f"[{_run_short(entry_ctx, 18)}]"
                    if (not entry_allow) and entry_reason:
                        head += f"({_run_short(entry_reason, 36)})"
                    if trig:
                        head += " " + _run_short(trig, 72)
                except Exception:
                    pass
            try:
                if hw_score is not None and math.isfinite(float(hw_score)):
                    head += f" | SCORE:{float(hw_score):.1f}"
            except Exception:
                pass
            try:
                lv = getattr(self.bot, "_hw_levels", None)
                if isinstance(lv, dict) and lv:
                    def _abbr(x: str) -> str:
                        x = str(x or "").upper()
                        if x == "OK":
                            return "OK"
                        if x == "DEGRADED":
                            return "DEG"
                        if x == "CRITICAL":
                            return "CRT"
                        return "NA"
                    lv_ema = None
                    try:
                        lv_ema = getattr(self.bot, "_hw_levels_ema", None)
                    except Exception:
                        lv_ema = None
                    head += f" | Lraw mkt={_abbr(lv.get('mkt'))} radar={_abbr(lv.get('radar'))} api={_abbr(lv.get('api'))} top8={_abbr(lv.get('top8'))}"
                    try:
                        if isinstance(lv_ema, dict) and lv_ema:
                            if any(str(lv_ema.get(k)) != str(lv.get(k)) for k in ('mkt','radar','api','top8')):
                                head += f" | Lem mkt={_abbr(lv_ema.get('mkt'))} radar={_abbr(lv_ema.get('radar'))} api={_abbr(lv_ema.get('api'))} top8={_abbr(lv_ema.get('top8'))}"
                    except Exception:
                        pass
                    try:
                        thr = getattr(self.bot, "_hw_thr", None)
                        if isinstance(thr, dict) and thr:
                            rw = float(((thr.get("radar") or {}).get("warn", float("nan"))))
                            rc = float(((thr.get("radar") or {}).get("crit", float("nan"))))
                            aw = float(((thr.get("api") or {}).get("warn", float("nan"))))
                            ac = float(((thr.get("api") or {}).get("crit", float("nan"))))
                            if math.isfinite(rw) and math.isfinite(rc) and math.isfinite(aw) and math.isfinite(ac):
                                strict = 1 if (bool(_env_bool("HEALTH_WD_ALLOW_STRICT", False)) and bool(_env_bool("HEALTH_WD_ALLOW_STRICT_CONFIRM", False))) else 0
                                head += f" | thr r={rw:.0f}/{rc:.0f} a={aw:.0f}/{ac:.0f} strict={strict}"
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                if str(hw_state or "").upper().strip() == "CRITICAL":
                    last_crit = float(getattr(self.bot, "_hw_last_crit_ts", 0.0) or 0.0)
                    cd = float(_env_float("HEALTH_RECOVERY_COOLDOWN_SEC", 45.0) or 45.0)
                    if last_crit > 0.0 and cd > 0.0:
                        rem = max(0.0, cd - (float(time.time()) - last_crit))
                        if rem >= 1.0 and (not hw_exec or hw_exec != "CRITICAL"):
                            head += f" | CD:{int(rem)}s"
            except Exception:
                pass
            if safe_on:
                sr_head = safe_reason
                try:
                    if str(sr_head or "").startswith("HEALTH_SYS_"):
                        ix = str(sr_head).find(" mkt=")
                        if ix > 0:
                            sr_head = str(sr_head)[:ix]
                except Exception:
                    sr_head = safe_reason
                head += f" | SAFE:ON {_run_short(sr_head, 42)}"
            else:
                head += " | SAFE:OFF"
            try:
                ages_raw = None
                try:
                    ages_raw = getattr(self.bot, "_hw_ages_raw", None)
                except Exception:
                    ages_raw = None
                if isinstance(ages_raw, dict) and ages_raw:
                    head += f" | AgeRaw radar:{fmt_age_s(ages_raw.get('radar'))} mkt:{fmt_age_s(ages_raw.get('mkt'))} top8:{fmt_age_s(ages_raw.get('top8'))} api:{fmt_age_s(ages_raw.get('api'))}"
                    try:
                        ui = {'radar': scan_age, 'mkt': market_age, 'top8': top8_age2, 'api': api_age}
                        def _diff(a, b) -> bool:
                            try:
                                if a is None or b is None:
                                    return False
                                return abs(float(a) - float(b)) >= 1.0
                            except Exception:
                                return False
                        if any(_diff(ui.get(k), ages_raw.get(k)) for k in ('radar','mkt','top8','api')):
                            head += f" | AgeUI radar:{fmt_age_s(scan_age)} mkt:{fmt_age_s(market_age)} top8:{fmt_age_s(top8_age2)} api:{fmt_age_s(api_age)}"
                    except Exception:
                        pass
                else:
                    head += f" | AgeUI radar:{fmt_age_s(scan_age)} mkt:{fmt_age_s(market_age)} top8:{fmt_age_s(top8_age2)} api:{fmt_age_s(api_age)}"
            except Exception:
                pass
            lines.append(_run_short(head, head_max))
            try:
                if summary:
                    lines.append(summary)
            except Exception:
                pass
            try:
                why_parts = []
                def _wp(x: str) -> None:
                    x = str(x or '').strip()
                    if not x:
                        return
                    if x not in why_parts:
                        why_parts.append(x)
                payload = None
                try:
                    payload = getattr(self.bot, "_last_entry_attempt", None)
                except Exception:
                    payload = None
                if isinstance(payload, dict) and payload:
                    try:
                        w0 = str(payload.get("wallet") or "").strip()
                        s0 = str(payload.get("sym") or "").strip()
                        key = f"{w0}:{s0}" if (w0 and s0) else (w0 or s0 or "")
                        by = getattr(self.bot, "_why_no_trade_by_key", None)
                        if isinstance(by, dict) and key and key in by:
                            payload = by.get(key) or payload
                    except Exception:
                        pass
                    try:
                        tags = payload.get("tags") or []
                        if isinstance(tags, (list, tuple)):
                            for t0 in tags:
                                _wp(str(t0))
                    except Exception:
                        pass
                    try:
                        w0 = str(payload.get("wallet") or "").strip()
                        s0 = str(payload.get("sym") or "").strip()
                        if w0 or s0:
                            _wp(f"CTX:{(w0 + '/' + s0).strip('/')}")
                    except Exception:
                        pass
                    try:
                        _wp(str(payload.get("status") or ""))
                    except Exception:
                        pass
                    try:
                        _wp(str(payload.get("reason") or payload.get("policy") or ""))
                    except Exception:
                        pass
                try:
                    if bool(safe_on):
                        _wp("SAFE")
                except Exception:
                    pass
                try:
                    try:
                        ttl = float(_env_float("WHY_NO_TRADE_TTL_SEC", 120.0) or 120.0)
                    except Exception:
                        ttl = 120.0
                    botx = getattr(self, "bot", None)
                    nowx = float(time.time())
                    ctx_w = ""
                    ctx_s = ""
                    rec_entry = getattr(botx, "_last_entry_attempt", None)
                    if isinstance(rec_entry, dict) and rec_entry:
                        try:
                            ts_e = float(rec_entry.get("ts", 0.0) or 0.0)
                        except Exception:
                            ts_e = 0.0
                        if ts_e > 0.0 and (nowx - ts_e) <= float(ttl):
                            ctx_w = str(rec_entry.get("wallet") or "").strip()
                            ctx_s = str(rec_entry.get("sym") or "").strip()
                    key = ""
                    if ctx_w and ctx_s:
                        key = f"{ctx_w}:{ctx_s}"
                    else:
                        key = ctx_w or ctx_s or ""
                    rec = None
                    try:
                        by = getattr(botx, "_why_no_trade_by_key", None)
                        if isinstance(by, dict) and key:
                            rec = by.get(key)
                    except Exception:
                        rec = None
                    if not (isinstance(rec, dict) and rec):
                        rec = getattr(botx, "_why_no_trade", None)
                    rec_show = rec
                    if isinstance(rec_entry, dict) and rec_entry:
                        try:
                            ts_e2 = float(rec_entry.get("ts", 0.0) or 0.0)
                        except Exception:
                            ts_e2 = 0.0
                        if ts_e2 > 0.0 and (nowx - ts_e2) <= float(ttl):
                            try:
                                st0 = str(rec_entry.get("status") or "").upper().strip()
                            except Exception:
                                st0 = ""
                            allow0 = True
                            try:
                                allow0 = bool((rec_entry.get("meta") or {}).get("allow", True))
                            except Exception:
                                allow0 = True
                            if (st0.startswith("ENTRY") and (not allow0)) or ("DENY" in st0):
                                rec_show = rec_entry
                                if not ctx_w:
                                    ctx_w = str(rec_entry.get("wallet") or "").strip()
                                if not ctx_s:
                                    ctx_s = str(rec_entry.get("sym") or "").strip()
                    if isinstance(rec_show, dict) and rec_show:
                        try:
                            ts0 = float(rec_show.get("ts", 0.0) or 0.0)
                        except Exception:
                            ts0 = 0.0
                        if ts0 > 0.0 and (nowx - ts0) <= float(ttl):
                            for t in (rec_show.get("tags") or []):
                                _wp(str(t))
                            w0 = str(ctx_w or rec_show.get("wallet") or "").strip()
                            s0 = str(ctx_s or rec_show.get("sym") or "").strip()
                            r0 = str(rec_show.get("reason") or "").strip()
                            if r0:
                                ctx = ""
                                if w0 or s0:
                                    ctx = f"{w0}:{s0}" if (w0 and s0) else (w0 or s0)
                                if ctx:
                                    _wp(f"LAST({ctx})={_run_short(r0, 64)}")
                                else:
                                    _wp(f"LAST={_run_short(r0, 64)}")
                except Exception:
                    pass
                try:
                    snapx = self.bot.snapshot() if getattr(self, "bot", None) is not None else {}
                    fx = (snapx.get("focus") or {}) if isinstance(snapx, dict) else {}
                    confx = fx.get("confidence", fx.get("focus_confidence", fx.get("focus_conf", None)))
                    statex = str(fx.get("market_state", "") or "").strip().upper()
                    if not str(fx.get("symbol") or fx.get("focus_symbol") or ""):
                        _wp("NO_DATA")
                    try:
                        minc = float(_env_float("PHOENIX_MIN_CONF", 0.35) or 0.35)
                        if confx is not None and float(confx) < float(minc):
                            cpcx = int(max(0.0, min(1.0, float(confx))) * 100)
                            _wp("LOW_CONF")
                            _wp(f"C{cpcx}%<{int(minc*100)}%")
                    except Exception:
                        pass
                    if statex in ("FLAT", "RANGE", "SIDEWAYS"):
                        _wp("REGIME")
                        _wp(f"{statex}")
                except Exception:
                    pass
                try:
                    up = float(time.time() - float(globals().get("_BOOT_TS", time.time()) or time.time()))
                    wsec = float(_env_float("BOT_WARMUP_SEC", 30.0) or 30.0)
                    if up < max(5.0, wsec):
                        _wp("WARMUP")
                        _wp(f"UP:{int(up)}s")
                except Exception:
                    pass
                if why_parts:
                    lines.append(f"🧠 WHY_NO_TRADE: {' | '.join(why_parts)[:200]}")
            except Exception:
                pass
            try:
                wb = list(health.get("warn_breakdown") or [])
            except Exception:
                wb = []
            try:
                if wb:
                    topw = ", ".join([f"{str(ev)}×{int(cnt or 0)}" for ev, cnt in wb[:3]])
                    lines.append(f"🧠 W({win_lbl}): {topw}")
            except Exception:
                pass
            try:
                snap0 = self.bot.snapshot() if getattr(self, "bot", None) is not None else {}
                focus0 = (snap0.get("focus") or {}) if isinstance(snap0, dict) else {}
                fsym0 = _canon_symbol(str(
                    focus0.get("symbol") or focus0.get("focus_symbol") or focus0.get("sym") or focus0.get("pair") or ""
                ))
                pick0 = str(
                    focus0.get("pick_reason") or focus0.get("focus_pick_reason") or focus0.get("focus_reason") or ""
                ).strip()
                fage0 = focus0.get("focus_age_sec", focus0.get("age_sec", focus0.get("age", None)))
                mage0 = focus0.get("market_age_sec", None)
                state0 = str(focus0.get("market_state", "") or "").strip().upper()
                conf0 = focus0.get("confidence", focus0.get("focus_confidence", focus0.get("focus_conf", None)))
                if fsym0:
                    try:
                        cpc = int(max(0.0, min(1.0, float(conf0 or 0.0))) * 100)
                    except Exception:
                        cpc = 0
                    age_s0 = fmt_age_s(float(fage0)) if fage0 is not None else "?"
                    lines.append(f"🧠 Focus: {fsym0} | C:{cpc}% | age:{age_s0}" + (f" | {_run_short(pick0, 28)}" if pick0 else ""))
                if state0:
                    lines.append(f"🧠 Regime: {state0}")
                if mage0 is not None:
                    lines.append(f"🧠 MKT age: {fmt_age_s(float(mage0))}")
                try:
                    ut = getattr(self.bot, "_top8_universe_total", None)
                    us = getattr(self.bot, "_top8_universe_scanned", None)
                    qc = getattr(self.bot, "_top8_universe_quote_counts", None) or {}
                    if ut is not None and int(ut or 0) > 0:
                        items = []
                        try:
                            for k, v in (qc or {}).items():
                                items.append((str(k or "?"), int(v or 0)))
                            items.sort(key=lambda kv: kv[1], reverse=True)
                        except Exception:
                            items = []
                        qtxt = ",".join([f"{k}:{v}" for (k, v) in (items or [])[:4] if int(v or 0) > 0])
                        tsu = getattr(self.bot, "_top8_universe_ts", None)
                        ageu = None
                        try:
                            if tsu:
                                ageu = float(time.time() - float(tsu))
                        except Exception:
                            ageu = None
                        atxt = f" | age:{fmt_age_s(ageu)}" if ageu is not None else ""
                        lines.append(f"🧠 Universe: total={int(ut)} scanned={int(us or 0)} | quotes {qtxt}" + atxt)
                except Exception:
                    pass
                try:
                    top8_rows = list(self.bot.get_top8_snapshot() or [])
                except Exception:
                    top8_rows = []
                syms8 = []
                try:
                    for r in (top8_rows or [])[:8]:
                        if isinstance(r, dict) and r.get("symbol"):
                            syms8.append(_canon_symbol(str(r.get("symbol"))))
                except Exception:
                    syms8 = []
                pho = getattr(self.bot, "phoenix", None)
                if pho is not None and hasattr(pho, "get_last_decision") and syms8:
                    ready = 0
                    missing = []
                    for s in syms8:
                        try:
                            d = pho.get_last_decision(s)
                        except Exception:
                            d = None
                        if d is None:
                            missing.append(s)
                            continue
                        try:
                            if bool(getattr(d, "ready", False)):
                                ready += 1
                            else:
                                missing.append(s)
                        except Exception:
                            missing.append(s)
                    lines.append(f"🧠 Phoenix ready: {ready}/{len(syms8)}" + (f" | warmup: {', '.join(missing[:4])}" if missing else ""))
            except Exception:
                pass
            try:
                for wl in (wlines or [])[:10]:
                    if "WHY " in str(wl) or "WHY:" in str(wl):
                        lines.append("🧠 " + _run_short(str(wl), 160))
            except Exception:
                pass
            try:
                try:
                    max_last = int(os.getenv("DASH_LAST_EVENTS_MAX_LINES", "12") or "12")
                except Exception:
                    max_last = 12
                max_last = max(1, min(50, int(max_last)))
                warnings_list = []
                try:
                    warnings_list = [str(x) for x in (wlines or [])]
                except Exception:
                    warnings_list = []
                unique_events = []
                try:
                    events0 = self._format_dashboard_events(recent or [])
                except Exception:
                    events0 = [str(x) for x in (recent or [])]
                for s_ev in (events0 or []):
                    try:
                        if warnings_list and any((w and w in s_ev) for w in warnings_list):
                            continue
                    except Exception:
                        pass
                    unique_events.append(str(s_ev))
                    if len(unique_events) >= max_last:
                        break
                lines += [str(x) for x in unique_events]
            except Exception:
                pass
            try:
                actions = []
                try:
                    risk = getattr(self.bot, "risk", None)
                    if bool(getattr(risk, "safe_mode", False)):
                        actions.append(f"ACTION: SAFE_MODE | {_run_short(str(getattr(risk,'safe_reason','') or ''), 90)}")
                except Exception:
                    pass
                try:
                    le = getattr(self.bot, "_last_entry_attempt", None)
                    if isinstance(le, dict) and le:
                        aa = None
                        try:
                            meta = le.get("meta", None)
                            if isinstance(meta, dict) and ("allow" in meta):
                                aa = meta.get("allow")
                        except Exception:
                            aa = None
                        if aa is None:
                            try:
                                st0 = str(le.get("status") or "").upper().strip()
                                aa = st0.endswith("ALLOW")
                            except Exception:
                                aa = None
                        if aa is not None and (not bool(aa)):
                            try:
                                why_e = str(le.get("reason") or le.get("policy") or le.get("status") or "")
                            except Exception:
                                why_e = ""
                            actions.append(f"ACTION: ENTRY_BLOCKED | {_run_short(str(why_e or ''), 90)}")
                except Exception:
                    pass
                try:
                    if scan_age is not None and float(scan_age or 0.0) > 75.0:
                        actions.append(f"ACTION: RADAR stale ({fmt_age_s(scan_age)})")
                except Exception:
                    pass
                try:
                    for wname, w in (wallets_items or []):
                        if w is None:
                            continue
                        oo = int(getattr(w, "open_orders_exch", 0) or 0)
                        if oo > 0:
                            actions.append(f"ACTION: {wname} has {oo} open orders (manual cleanup will run)")
                except Exception:
                    pass
                if actions:
                    lines += ["— ACTIONS —"] + actions[:4]
            except Exception:
                pass
            if warn_err:
                lines.append(f"{_icon('📄','LOG')} tail: " + _run_short(warn_err[-1], 120))
            if crashes:
                lines.append(_run_short(crashes[-1], 140))
            max_lines = int(_env_int("DASH_FOOTER_MAX_LINES", 10) or 10)
            footer = "\n".join([_run_short(str(x), 170) for x in lines[:max_lines]]) if lines else hb
            logs_panel = Panel(Text(footer, overflow="fold", no_wrap=False), title="Last events / logs", box=box.ROUNDED, padding=(0, 1))
            width = 0
            try:
                width = int(getattr(getattr(console, "size", None), "width", 0) or 0)
            except Exception:
                width = 0
            min_wide = int(_env_int("DASH_MIN_WIDE", 120))
            narrow = (width <= 0) or (width < min_wide)
            try:
                if _env_bool("DASH_RAZ_CORE", True):
                    return render_raz_core(ordered, wallets, logs_panel, narrow=narrow)
            except Exception:
                pass
            layout = Layout()
            if narrow:
                layout = Layout()
                w_items = list(wallets)
                try:
                    w_items.sort(key=lambda kv: str(kv[0]))
                except Exception:
                    pass
                wmap = {str(n): w for (n, w) in w_items}
                w1 = wmap.get("W1")
                w2 = wmap.get("W2")
                w3 = wmap.get("W3")
                height = 0
                try:
                    height = int(getattr(getattr(console, "size", None), "height", 0) or 0)
                except Exception:
                    height = 0
                if height > 0:
                    top_sz = max(9, min(14, int(round(height * 0.38))))
                    logs_sz = max(3, min(6, int(round(height * 0.18))))
                    rem = max(6, height - (top_sz + logs_sz))
                    min_wallet = 5
                    if rem < 2 * min_wallet:
                        need = (2 * min_wallet) - rem
                        dec = min(need, max(0, top_sz - 4))
                        top_sz -= dec
                        need -= dec
                        if need > 0:
                            dec2 = min(need, max(0, logs_sz - 3))
                            logs_sz -= dec2
                        rem = max(2 * 3, height - (top_sz + logs_sz))
                        min_wallet = max(3, rem // 2)
                    r1 = max(min_wallet, rem // 2)
                    r2 = max(min_wallet, rem - r1)
                    r2 = height - (top_sz + logs_sz + r1)
                    layout.split_column(
                        Layout(name="top", size=top_sz),
                        Layout(name="row1", size=r1),
                        Layout(name="row2", size=r2),
                        Layout(name="logs", size=logs_sz),
                    )
                else:
                    layout.split_column(
                        Layout(name="top", size=8),
                        Layout(name="row1", ratio=4),
                        Layout(name="row2", ratio=4),
                        Layout(name="logs", size=8),
                    )
                layout["top"].update(phoenix)
                layout["row1"].split_row(Layout(name="w1", ratio=1), Layout(name="w2", ratio=1))
                layout["row1"]["w1"].update(wallet_full_panel("W1", w1))
                layout["row1"]["w2"].update(wallet_full_panel("W2", w2))
                layout["row2"].split_row(Layout(name="w3", ratio=1), Layout(name="sys", ratio=1))
                layout["row2"]["w3"].update(wallet_full_panel("W3", w3))
                try:
                    layout["row2"]["sys"].update(Columns([dzh, ai], expand=True, equal=True))
                except Exception:
                    layout["row2"]["sys"].update(Group(dzh, ai))
                layout["logs"].update(logs_panel)
                return layout
            layout.split_column(
                Layout(name="hdr", size=3),
                Layout(name="body", ratio=1),
                Layout(name="logs", size=7),
            )
            layout["body"].split_row(
                Layout(name="left", ratio=2),
                Layout(name="mid", ratio=3),
                Layout(name="right", ratio=3),
            )
            layout["left"].update(wallet_overview_panel(wallets, narrow=narrow))
            mid = Layout()
            mid.split_column(Layout(name="pho", ratio=2), Layout(name="dzh", ratio=2))
            mid["pho"].update(phoenix)
            mid["dzh"].update(dzh)
            layout["mid"].update(mid)
            r = Layout()
            r.split_column(Layout(name="top", ratio=3), Layout(name="ai", ratio=2))
            r["top"].update(policy)
            r["ai"].update(ai)
            layout["right"].update(r)
            layout["hdr"].update(banner_panel())
            layout["logs"].update(logs_panel)
            return layout
        try:
            try:
                console.show_cursor(False)
            except Exception:
                pass
            with Live(console=console, refresh_per_second=max(1, int(1.0 / max(0.2, self.refresh_sec))), screen=self.screen) as live:
                for _omega_guard in range(150000):
                    try:
                        view = render()
                    except Exception:
                        try:
                            try:
                                try:
                                    import traceback
                                except:
                                    pass
                            except:
                                pass
                            view = Panel(Text(traceback.format_exc(limit=3), style="red"), title="DASHBOARD ERROR")
                        except Exception:
                            view = "DASHBOARD ERROR"
                    live.update(view, refresh=True)
                    await _sleep_or_stop(self._stop, self.refresh_sec)
        finally:
            try:
                console.show_cursor(True)
            except Exception:
                pass
    async def _run_fallback(self) -> None:
        for _omega_guard in range(150000):
            parts = []
            try:
                for wname, w in getattr(self.bot, "wallets", {}).items():
                    cash_irt = float(getattr(w, "cash_irt", 0.0) or 0.0)
                    div = 10.0 if (cash_irt >= 1_000_000.0 and abs(cash_irt) % 10 == 0) else 1.0
                    cash_t = cash_irt / div
                    posn = len(getattr(w, "positions", {}) or {})
                    le = str(getattr(w, "last_event", "") or "").strip()
                    parts.append(f"{wname}: cashT={cash_t:,.0f} pos={posn} ev={le[:28]}")
            except Exception:
                pass
            try:
                meta = self.bot.specs.status() if hasattr(self.bot.specs, "status") else {}
                meta_s = f"meta_ok={bool(meta.get('ok'))} size={int(meta.get('cache_size',0) or 0)}"
                if meta.get("age_s") is not None:
                    meta_s += f" age={float(meta.get('age_s')):,.2f}s"
                if meta.get("last_err"):
                    meta_s += f" err={str(meta.get('last_err'))[:48]}"
            except Exception:
                meta_s = "meta=?"
            line = " | ".join(parts) if parts else "..."
            print("[DASH] " + line + " || " + meta_s, flush=True)
            await _sleep_or_stop(self._stop, self.refresh_sec)