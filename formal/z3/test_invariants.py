from formal.z3.invariants import prove_basic_risk_bound


def test_basic_risk_bound() -> None:
    assert prove_basic_risk_bound()
