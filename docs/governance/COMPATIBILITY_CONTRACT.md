# ASO-X Compatibility Contract

## Status

This document defines the minimum compatibility expectations for ASO-X.

## Core Requirements

- Repository text files should use BOM-free UTF-8.
- Line endings should be LF.
- Python tooling should remain deterministic and portable.
- PowerShell automation should be safe on Windows developer machines.
- Standard output should avoid characters that break cp1252 consoles where practical.
- Critical writes performed by project tooling should be atomic.
- CI workflows should pin required runtime versions explicitly where contract tests require them.

## Runtime Policy

### Python

Preferred baseline:

- Python 3.11 for CI governance workflows where specified.
- Python code should avoid unnecessary platform-specific behavior.
- Scripts should return non-zero exit codes on validation failure.

### PowerShell

- PowerShell scripts should set error handling to stop on repository patching failures.
- Scripts should avoid ambiguous interpolation.
- Scripts should prefer safe path handling.

### JavaScript / Node

- Node usage should be documented when introduced or changed.
- Node-based tooling should not become a hidden dependency.

## Operating System Policy

The repository should remain operable from Windows-first development environments while preserving portability for GitHub Actions Linux runners where applicable.

## File Format Policy

Preferred durable formats:

- Markdown for human-readable governance.
- YAML for simple machine-readable contracts.
- JSON for schemas and registries.
- Plain text logs where long-term readability matters.

## Portability Limits

"Runs everywhere" is an aspiration, not an excuse for undocumented assumptions. Any hard requirement on OS, shell, runtime, network access, or external service must be documented.

## Anti-Obsolescence Policy

Major dependency, runtime, or platform changes should include:

- reason
- migration impact
- rollback path where practical
- decision log entry for strategic changes