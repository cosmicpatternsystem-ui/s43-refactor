---- MODULE trading_core ----
EXTENDS Naturals, Sequences

CONSTANT RiskLimit
VARIABLE qty

Init == qty = 0

Next ==
    \/ \E q \in 1..RiskLimit: qty' = qty + q
    \/ \E q \in 1..RiskLimit: qty' = qty - q

RiskInvariant == Abs(qty) <= RiskLimit

====
