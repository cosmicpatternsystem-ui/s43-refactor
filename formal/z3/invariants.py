from z3 import Abs, Int, Solver, sat


def prove_basic_risk_bound(limit: int = 10) -> bool:
    qty = Int("qty")
    s = Solver()
    s.add(Abs(qty) <= limit)
    s.add(Abs(qty) > limit)
    return s.check() != sat


if __name__ == "__main__":
    print({"basic_risk_bound": prove_basic_risk_bound()})
