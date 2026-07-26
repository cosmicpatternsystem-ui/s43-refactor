import sys

# =============================================================================
# DEPRECATED - DO NOT RUN
# =============================================================================
# This script contains HARDCODED Phase 22 data (P22-13 only). Running it
# OVERWRITES ROADMAP_CURRENT.json and destroys all phases 23..33, including
# the active P33-01 phase and its pending tasks.
#
# Incident reference: ROADMAP_CURRENT.json corruption on 2026-07-24
# (see ROADMAP_CURRENT.json.bak.20260724-*).
#
# The ONLY authorized generator is: scripts/update-roadmap.ps1
# Canonical source:                 docs/governance/ROADMAP_CANONICAL.md
# =============================================================================

DEPRECATION_MESSAGE = """
FATAL: roadmap_generator.py is DEPRECATED and destructive.

  - It writes hardcoded Phase 22 (P22-13) data only.
  - Running it WIPES all later phases from ROADMAP_CURRENT.json.

Use instead:
  scripts/update-roadmap.ps1   (authorized generator)

If you believe you need this legacy script, restore it from
roadmap_generator.py.backup_20260702_104708 in a sandbox -- never
against the live ROADMAP_CURRENT.json.
"""


def main():
    sys.stderr.write(DEPRECATION_MESSAGE)
    sys.exit(2)


if __name__ == "__main__":
    main()