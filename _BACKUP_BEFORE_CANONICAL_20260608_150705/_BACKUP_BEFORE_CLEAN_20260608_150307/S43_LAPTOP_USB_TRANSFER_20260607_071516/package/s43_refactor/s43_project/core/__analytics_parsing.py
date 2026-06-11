class _AnalyticsParsing:
    @staticmethod
    def parse_weight_map(raw: str, *, key_upper: bool = False) -> Dict[str, float]:
        m: Dict[str, float] = {}
        s = str(raw or "")
        for item in s.split(","):
            if ":" not in item:
                continue
            k, w = item.split(":", 1)
            k = k.strip()
            if not k:
                continue
            if key_upper:
                k = k.upper()
            try:
                m[k] = float(w.strip())
            except Exception:
                continue
        return m