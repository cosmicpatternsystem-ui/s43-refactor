# TriWallet Profile Schema

## Purpose

This document defines the initial profile schema for the S43 TriWallet runtime layer.

The profile layer is designed to make wallet configuration explicit, auditable, and safe before it is connected to runtime code.

## Scope

This document covers:

- wallet identity
- wallet role
- enablement state
- execution mode
- approval mode
- secret reference
- token expiry requirement
- risk profile
- permission flags
- global policy defaults

This document does not enable live trading and does not modify `s43.py`.

## Profile Set Fields

### schema_version

Type: string

Purpose: Tracks the schema version used by the profile file.

Current value: `0.1.0`

### profile_set_name

Type: string

Purpose: Human-readable profile set identifier.

### description

Type: string

Purpose: Short explanation of the profile set.

### wallets

Type: array

Purpose: List of wallet profile objects.

### global_policy

Type: object

Purpose: Default safety policy for the wallet profile set.

## Wallet Fields

### wallet_id

Type: string

Required: yes

Example values:

- primary
- reserve
- sandbox

Purpose: Stable wallet identifier used by configuration, audit, and runtime mapping.

### display_name

Type: string

Required: yes

Purpose: Human-readable wallet name.

### role

Type: string

Required: yes

Allowed values:

- primary
- reserve
- sandbox

Purpose: Defines the operational role of the wallet.

### enabled_by_default

Type: boolean

Required: yes

Purpose: Defines whether the wallet should be active when the profile set is loaded.

### execution_mode

Type: string

Required: yes

Allowed values:

- dry_run
- guarded
- disabled

Purpose: Defines the highest permitted execution mode for the wallet.

### approval_mode

Type: string

Required: yes

Allowed values:

- required
- not_required_for_dry_run
- disabled

Purpose: Defines whether operator approval is required before execution.

### secret_source

Type: string

Required: yes

Allowed values:

- environment
- disabled

Purpose: Defines where wallet secrets are expected to come from.

Secrets must not be hardcoded in repository files.

### secret_key_ref

Type: string

Required: yes

Purpose: Name of the environment variable that should contain the wallet secret.

Example: `S43_WALLET_PRIMARY_TOKEN`

### token_expiry_required

Type: boolean

Required: yes

Purpose: Defines whether token expiry validation is required for this wallet.

## Risk Profile

### max_single_order_value_quote

Type: number

Purpose: Maximum value of a single order in quote currency.

A value of `0.0` means no live order size is authorized by the example file.

### max_daily_order_value_quote

Type: number

Purpose: Maximum total daily order value in quote currency.

A value of `0.0` means no live daily order value is authorized by the example file.

### max_daily_loss_quote

Type: number

Purpose: Maximum allowed daily loss in quote currency.

A value of `0.0` means no live loss budget is authorized by the example file.

### max_open_positions

Type: integer

Purpose: Maximum number of open positions allowed for this wallet.

### cooldown_seconds_after_order

Type: integer

Purpose: Minimum cooldown after an order action.

## Permissions

### allow_market_data

Type: boolean

Purpose: Allows market data access for the wallet profile.

### allow_balance_read

Type: boolean

Purpose: Allows balance read access for the wallet profile.

### allow_order_draft

Type: boolean

Purpose: Allows order draft creation for the wallet profile.

### allow_live_execution

Type: boolean

Purpose: Allows live execution only if all risk, policy, approval, and connector checks pass.

The example profile sets this to `false` for all wallets.

## Global Policy

### live_execution_default

Type: boolean

Recommended value: `false`

Purpose: Prevents accidental live execution unless explicitly enabled by a later approved policy layer.

### require_human_approval_for_live_execution

Type: boolean

Recommended value: `true`

Purpose: Requires human approval for live execution.

### deny_unknown_wallets

Type: boolean

Recommended value: `true`

Purpose: Rejects wallets that are not listed in the profile set.

### deny_missing_secrets

Type: boolean

Recommended value: `true`

Purpose: Rejects wallets with missing required secrets.

### deny_expired_tokens

Type: boolean

Recommended value: `true`

Purpose: Rejects wallets with expired tokens.

### audit_profile_load

Type: boolean

Recommended value: `true`

Purpose: Requires audit logging for profile load events.

## Safety Position

The initial TriWallet profile layer is configuration-only.

It does not:

- change runtime behavior
- place orders
- enable live execution
- store secrets
- bypass approval
- bypass risk policy

## Next Integration Step

The next safe step is to create a read-only profile loader that validates this schema and reports wallet profile health without changing execution behavior.
