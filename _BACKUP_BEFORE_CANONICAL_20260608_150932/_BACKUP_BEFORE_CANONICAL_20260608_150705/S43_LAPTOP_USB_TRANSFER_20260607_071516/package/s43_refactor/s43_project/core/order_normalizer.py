from .market_specs_cache import MarketSpecsCache

class OrderNormalizer:
    def __init__(self, specs: MarketSpecsCache):
        self._specs = specs
    async def normalize(self, symbol: str, qty: float, price: float) -> Tuple[float, float]:
        spec = await self._specs.get(symbol)
        if not spec:
            return float(qty), float(int(price))
        step = _first_num(spec, "step_size", "amount_step", "qty_step", "step", default=0.0)
        tick = _first_num(spec, "tick_size", "price_tick", "tick", default=1.0)
        min_qty = _first_num(spec, "min_amount", "min_qty", "minimum_quantity", default=0.0)
        max_qty = _first_num(spec, "max_amount", "max_qty", "maximum_quantity", default=0.0)
        min_price = _first_num(spec, "min_price", default=0.0)
        max_price = _first_num(spec, "max_price", default=0.0)
        q = float(qty)
        p = float(price)
        if step > 0:
            q = _quantize_down(q, step)
        if tick > 0:
            p = _quantize_down(p, tick)
        if min_qty > 0:
            q = max(q, float(min_qty))
        if max_qty > 0:
            q = min(q, float(max_qty))
        if min_price > 0:
            p = max(p, float(min_price))
        if max_price > 0:
            p = min(p, float(max_price))
        p = float(int(p))
        return float(q), float(p)