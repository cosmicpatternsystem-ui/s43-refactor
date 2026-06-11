from pathlib import Path
import shutil, time

p = Path("s43.py")
bak = Path(f"s43.py.bak_fix_dashboard_core_{int(time.time())}")
shutil.copy2(p, bak)

lines = p.read_text(encoding="utf-8").splitlines()

start = None
run_fb = None
end = None

# Prefer the Dashboard __init__ immediately after deep_prune_ghost_orders.
for i, line in enumerate(lines):
    if line.startswith("    def __init__("):
        # Pick the first class-level __init__ after deep_prune_ghost_orders return area.
        if i > 1100:
            start = i
            break

if start is None:
    raise SystemExit("ERROR: Dashboard __init__ start not found")

for i in range(start, len(lines)):
    if lines[i].startswith("    async def _run_fallback("):
        run_fb = i
        break

if run_fb is None:
    raise SystemExit("ERROR: Dashboard _run_fallback start not found")

# End at the next class-level method after _run_fallback.
for j in range(run_fb + 1, len(lines)):
    if (
        lines[j].startswith("    async def ")
        or lines[j].startswith("    def ")
    ):
        end = j
        break

# If _run_fallback is the last method in the class, fall back to next top-level boundary.
if end is None:
    for j in range(run_fb + 1, len(lines)):
        if (
            lines[j].startswith("class ")
            or lines[j].startswith("async def ")
            or lines[j].startswith("def ")
        ):
            end = j
            break

if end is None:
    raise SystemExit("ERROR: boundary after Dashboard _run_fallback not found")

replacement = [
    "    def __init__(",
    "        self,",
    "        bot: \"TradingBot\",",
    "        *,",
    "        refresh_sec: float = 1.0,",
    "        screen: bool = True,",
    "    ) -> None:",
    "        self.bot = bot",
    "        self.refresh_sec = float(max(0.2, refresh_sec))",
    "        self.screen = bool(screen)",
    "",
    "        try:",
    "            env_screen = os.getenv(\"DASH_SCREEN\", \"\").strip()",
    "        except Exception:",
    "            env_screen = \"\"",
    "",
    "        if env_screen:",
    "            try:",
    "                self.screen = bool(int(env_screen))",
    "            except Exception:",
    "                try:",
    "                    self.screen = env_screen.lower() in (\"1\", \"true\", \"yes\", \"on\")",
    "                except Exception:",
    "                    pass",
    "        else:",
    "            try:",
    "                is_termux = bool(os.getenv(\"TERMUX_VERSION\"))",
    "            except Exception:",
    "                is_termux = False",
    "",
    "            if not is_termux:",
    "                try:",
    "                    pref = str(os.getenv(\"PREFIX\") or \"\") + \" \" + str(os.getenv(\"HOME\") or \"\")",
    "                    if \"com.termux\" in pref:",
    "                        is_termux = True",
    "                except Exception:",
    "                    pass",
    "",
    "            if is_termux:",
    "                self.screen = False",
    "",
    "        self._stop: asyncio.Event = asyncio.Event()",
    "        self._task: Optional[asyncio.Task] = None",
    "",
    "    def start(self) -> None:",
    "        if self._task is not None and not self._task.done():",
    "            return",
    "        try:",
    "            loop = asyncio.get_running_loop()",
    "        except Exception:",
    "            return",
    "        self._stop.clear()",
    "        self._task = loop.create_task(self._run(), name=\"Dashboard\")",
    "",
    "    def stop(self) -> None:",
    "        try:",
    "            self._stop.set()",
    "        except Exception:",
    "            pass",
    "",
    "        t = self._task",
    "        if t is not None and not t.done():",
    "            try:",
    "                t.cancel()",
    "            except Exception:",
    "                pass",
    "",
    "    async def _run(self) -> None:",
    "        await self._run_fallback()",
    "",
    "    async def _run_fallback(self) -> None:",
    "        \"\"\"Lightweight, Termux-safe dashboard loop.",
    "",
    "        This fallback intentionally avoids curses/rich dependencies. It prints",
    "        a compact status line periodically and never raises into the trading",
    "        loop.",
    "        \"\"\"",
    "        while True:",
    "            try:",
    "                if self._stop.is_set():",
    "                    return",
    "",
    "                bot = self.bot",
    "                parts = []",
    "",
    "                try:",
    "                    wallet = getattr(bot, \"_wallet\", None) or getattr(bot, \"wallet\", None) or \"W?\"",
    "                    parts.append(f\"wallet={wallet}\")",
    "                except Exception:",
    "                    pass",
    "",
    "                try:",
    "                    cfg = getattr(bot, \"cfg\", None)",
    "                    dry = bool(getattr(cfg, \"dry_run\", False)) if cfg is not None else False",
    "                    parts.append(f\"dry_run={int(dry)}\")",
    "                except Exception:",
    "                    pass",
    "",
    "                try:",
    "                    ghost = int(getattr(bot, \"ghost_order_count\", 0) or 0)",
    "                    parts.append(f\"ghost={ghost}\")",
    "                except Exception:",
    "                    pass",
    "",
    "                try:",
    "                    active = getattr(bot, \"active_orders\", None)",
    "                    if isinstance(active, dict):",
    "                        parts.append(f\"active_orders={len(active)}\")",
    "                except Exception:",
    "                    pass",
    "",
    "                try:",
    "                    positions = getattr(bot, \"positions\", None)",
    "                    if isinstance(positions, dict):",
    "                        parts.append(f\"positions={len(positions)}\")",
    "                except Exception:",
    "                    pass",
    "",
    "                try:",
    "                    risk_halt = bool(getattr(bot, \"risk_halt\", False) or getattr(bot, \"_risk_halt\", False))",
    "                    if risk_halt:",
    "                        parts.append(\"risk_halt=1\")",
    "                except Exception:",
    "                    pass",
    "",
    "                if not parts:",
    "                    parts.append(\"dashboard=running\")",
    "",
    "                line = \" | \".join(parts)",
    "",
    "                try:",
    "                    if self.screen:",
    "                        os.system(\"clear\")",
    "                        print(line, flush=True)",
    "                    else:",
    "                        print(line, flush=True)",
    "                except Exception:",
    "                    pass",
    "",
    "                try:",
    "                    await asyncio.wait_for(self._stop.wait(), timeout=float(self.refresh_sec))",
    "                except asyncio.TimeoutError:",
    "                    pass",
    "",
    "            except asyncio.CancelledError:",
    "                raise",
    "            except Exception:",
    "                try:",
    "                    await asyncio.sleep(float(self.refresh_sec))",
    "                except asyncio.CancelledError:",
    "                    raise",
    "                except Exception:",
    "                    await asyncio.sleep(1.0)",
]

lines[start:end] = replacement

p.write_text("\\n".join(lines) + "\\n", encoding="utf-8")
print(f"patched Dashboard core: lines {start+1}..{end}; backup={bak}")
