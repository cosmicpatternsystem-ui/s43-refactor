class _Orch22AsyncComponent:
    def _task_name(self) -> str:
        return ""
    def age(self) -> float:
        try:
            f = getattr(self, "_fresh", None)
            if f is None:
                return 0.0
            return float(f.age())
        except Exception:
            return 0.0
    def stop(self) -> None:
        try:
            ev = getattr(self, "_stop", None)
            if ev is not None:
                ev.set()
        except Exception:
            pass
    async def start(self) -> None:
        try:
            t = getattr(self, "_task", None)
            if t is not None and hasattr(t, "done") and (not t.done()):
                return
            name = ""
            try:
                name = str(self._task_name() or "")
            except Exception:
                name = ""
            if name:
                self._task = asyncio.create_task(self._run(), name=name)
            else:
                self._task = asyncio.create_task(self._run())
        except Exception:
            return