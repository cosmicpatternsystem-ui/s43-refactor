# CP003-B Baseline Impact Assessment

## Status

- Phase: CP003-B
- Document type: Baseline Impact Assessment
- Branch: cp003-b-integration-planning
- Base tag: s43-cp003-a-locked
- Insertion Map tag: s43-cp003-b-insertion-map-v1
- Runtime integration: UNAUTHORIZED
- Live trading: UNAUTHORIZED
- Baseline executable mutation: UNAUTHORIZED

## Purpose

This document assesses the potential impact of future CP003 scaffold integration on the existing S43 baseline. 

It identifies high-risk areas, defines non-negotiable safety boundaries, and categorizes potential side effects.

This assessment is for planning only and does not authorize execution.

## Critical Baseline Components (High Risk)

The following components are considered "Critical" and must not have their logic altered by any integration:

1. **Order Execution Path:** The logic that sends orders to the broker must remain deterministic and unchanged.
2. **Safety Gates (Current):** Existing risk checks (hard-coded limits, balance checks) must remain as the primary authority.
3. **Connectivity Logic:** Broker API connection and heartbeat logic.
4. **Position Tracking:** The source of truth for current holdings.

## Impact Domains

### 1. Control Flow Impact

Any future integration must be "Additive" or "Parallel" rather than "Interceptive."
- **Allowed:** Calling a CP003 function to record a receipt *after* a baseline action.
- **Allowed:** Requesting a safety opinion from CP003 that the baseline can choose to ignore or follow (Shadow Mode).
- **Disallowed:** Replacing a baseline decision function with a CP003 function without a hard-coded fallback to the original logic.

### 2. Data Integrity & State Impact

- **Allowed:** CP003 reading baseline state variables.
- **Disallowed:** CP003 modifying baseline state variables directly (e.g., changing a balance variable or an order status in the baseline's memory).
- **Disallowed:** Circular dependencies between baseline and scaffold state.

### 3. Resource & Performance Impact

- **Allowed:** Minimal latency overhead for local audit logging.
- **Disallowed:** Blocking network calls within the main execution loop.
- **Disallowed:** High-CPU computations that interfere with real-time order processing.

## Safety Boundaries & Red Lines

The following are defined as "Critical Impact Violations":

- **Violation 01:** Any integration that allows CP003 to bypass existing baseline risk limits.
- **Violation 02:** Any integration that permits CP003 to initiate an order without explicit baseline authorization.
- **Violation 03:** Any integration that hides or masks baseline error messages.
- **Violation 04:** Any integration that prevents the "Emergency Stop" functionality of the baseline.

## Risk Categorization for Future Slices

Based on the Insertion Map, the risk levels for candidate slices are:

- **Slice B1 (Passive Import):** LOW RISK. (Side-effect: Import errors).
- **Slice B2 (Offline Audit):** LOW RISK. (Side-effect: File I/O overhead).
- **Slice B3 (Shadow Safety):** MEDIUM RISK. (Side-effect: Execution latency).
- **Slice B4 (Portfolio Scenario):** MEDIUM RISK. (Side-effect: Memory usage).

## Mitigation Requirements

Any future mutation proposal must include:
1. **Isolation Proof:** How the CP003 code is prevented from affecting the main execution loop in case of failure.
2. **Error Handling:** Baseline must catch all exceptions originating from CP003.
3. **Bypass Switch:** A global constant or flag to instantly disable CP003 integration.

## Conclusion

The impact of integration is manageable provided the "No-Touch Set" is respected and the "Red Lines" are never crossed. 

This assessment confirms that the baseline is structurally ready for **Passive/Shadow integration planning**, but is not yet ready for **Active/Interceptive integration**.
