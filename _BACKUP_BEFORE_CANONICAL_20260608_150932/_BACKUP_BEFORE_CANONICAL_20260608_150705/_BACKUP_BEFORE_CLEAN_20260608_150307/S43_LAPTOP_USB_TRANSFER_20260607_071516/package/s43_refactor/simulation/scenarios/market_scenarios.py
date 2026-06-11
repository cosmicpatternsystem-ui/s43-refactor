import random


def normal_market(price):
    return price + random.uniform(-0.5, 0.5)


def high_volatility(price):
    return price + random.uniform(-3, 3)


def low_liquidity(price):
    return price + random.uniform(-0.2, 0.2)


def price_spike(price):
    if random.random() < 0.05:
        return price + random.uniform(-10, 10)
    return price + random.uniform(-0.5, 0.5)


SCENARIOS = {
    "normal": normal_market,
    "high_volatility": high_volatility,
    "low_liquidity": low_liquidity,
    "price_spike": price_spike,
}
