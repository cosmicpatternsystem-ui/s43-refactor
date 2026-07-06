# Repository Truth Contract

## Mission
ASO-X repository is the sole authoritative source of operational truth.

## Authoritative Scope
Only committed repository artifacts on the default branch, validated by governance gates, are authoritative.

## Non-Authoritative Scope
The following are never authoritative:
- chat transcripts
- local notes
- copied prompts
- temporary files
- backup files
- retired files
- unmerged branch state
- external memory
- screenshots without committed textual normalization

## Authority Order
1. docs/governance/GOAL_CONSTITUTION.md
2. docs/governance/ROADMAP_CONSTITUTION.md
3. ROADMAP_CURRENT.json
4. ROADMAP_CANONICAL.md
5. PROJECT_STATE.md
6. POLICY_MATRIX.md
7. ROADMAP.md
8. README.md

## Conflict Resolution
If two artifacts conflict, the artifact with higher authority prevails.
Lower-authority artifacts must be updated in the same change set.
Unresolved authority conflicts are release-blocking.

## Roadmap Rules
ROADMAP_CURRENT.json is the machine-readable active roadmap state.
ROADMAP_CANONICAL.md is the human-readable canonical roadmap.
ROADMAP.md is derivative and must never override canonical truth.

## Artifact Retention Rules
Historical artifacts may exist only as retention artifacts and are never active inputs.
Files matching these patterns are non-authoritative:
- *.bak
- *.tmp
- *.old
- *.orig
- *.rej
- *.RETIRED.txt
- *.disabled
- *patch_log*

## AI and Automation Rules
No AI, script, or contributor may invent goals, alter authority order, or treat non-authoritative artifacts as active truth.
All roadmap-affecting changes must preserve cross-file consistency.

## Required Repository Guarantees
- UTF-8 without BOM
- LF line endings
- atomic writes for generated state
- cp1252-safe stdout
- repo-relative paths only
- CI enforcement for governance truth