# TriWallet Runtime

## Purpose
Define the first operational target: three active crypto wallet profiles across mobile, laptop, and server environments.

## Wallet Roles
1. Primary wallet
2. Reserve/backup wallet
3. Sandbox/low-risk wallet

## Required Metadata
- wallet_id
- wallet_name
- exchange
- token_expiry_ts
- wallet_disabled
- disable_reason
- registration_ts
- runtime_instance_id
- environment
- risk_profile
- approval_profile

## Runtime Requirements
- registration telemetry
- metadata consistency checks
- expiry visibility
- disabled-state visibility
- health check
- audit export
