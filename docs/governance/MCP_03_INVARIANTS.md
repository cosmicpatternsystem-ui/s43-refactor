# MCP-03 Invariant Specification Pack

## Domain Vocabulary
- FillEvent: immutable execution event
- PositionState: current quantity, average price, fees, realized pnl, and applied fill ids

## Numeric Policy
- Use Decimal for monetary and quantity values
- Canonical serialization uses strings

## Policies
- Duplicate fill ids are ignored after first successful application
- Replay is deterministic for a given ordered fill sequence

## Invariants
1. Risk Limit: abs(position.quantity) <= risk_limit
2. Idempotency: applying the same fill twice does not change state after the first apply
3. Fee Conservation: accumulated fees equal the sum of accepted fill fees
4. Quantity Transition: next.quantity = prev.quantity + signed_fill_quantity
5. Replay Determinism: identical ordered input yields identical canonical state hash
6. Gross Exposure: abs(quantity) * mark_price remains within configured gross limit
