# S43 Standalone Portability Roadmap

Date: 2026-06-07
Status: ACTIVE_ROADMAP
Previous phase: STRICT_GAP_REVIEW_CLOSED_SAFE

## 1. Current Baseline

The s43.py file is preserved unchanged and verified against the canonical SHA256:

8270dbb24d728c22e4a1c42b00c148dc0bf81e00454a1932003531963eef3786

The strict gap review has been completed. No validated functional gap requiring modification of s43.py was identified.

Current status:

S43_PY_MODIFIED=NO
FUNCTIONAL_PATCH_APPROVED=NO
STRICT_GAP_REVIEW_STATUS=CLOSED_SAFE

## 2. Strategic Goal

The project must no longer depend on Termux, Android-only assumptions, phone-specific paths, or one specific execution environment.

Target status:

TERMUX_DEPENDENCY=NO
ANDROID_ONLY_ASSUMPTION=NO
STANDALONE_EXECUTION=YES
EDITABLE_SOURCE_PACKAGE=YES
CROSS_MACHINE_PORTABILITY=YES

## 3. Distribution Model

The project should support two forms.

### 3.1 Editable Source Package

Used for development, review, patching, and future refactor work.

Expected structure:

s43_refactor/
- s43.py
- tools/
- docs/
- configs/
- requirements.txt
- README.md

### 3.2 Standalone Executable Package

Used for running on another compatible system without depending on Termux.

Expected structure:

dist/
- s43.exe
- config/
- docs/

The executable build may be generated later with a tool such as PyInstaller, Nuitka, or a portable Python bundle, but this must only happen after dependency and path audit is complete.

## 4. Core Portability Requirements

### 4.1 Path Independence

All hard-coded absolute paths must be avoided.

Preferred:
- relative paths
- project root detection
- config-based paths

Avoid:
- /storage/emulated/0/...
- /sdcard/...
- E:\specific\machine\path
- Termux-only paths
- phone-specific paths

### 4.2 Environment Independence

The code must avoid assumptions such as:
- Termux shell availability
- Android filesystem layout
- phone-specific storage
- manual USB transfer dependency
- one-machine-only execution

### 4.3 Configurable Runtime

Runtime behavior should eventually be controlled by config files, for example:
- configs/default.json
- configs/local.example.json
- optional .env file

No sensitive or system-specific value should be hard-coded into s43.py.

### 4.4 Dependency Clarity

All Python dependencies should be documented in:
- requirements.txt

If optional dependencies exist, they should be separated into:
- requirements.txt
- requirements-dev.txt
- requirements-build.txt

## 5. Refactor Safety Rule

The canonical s43.py must not be modified directly until a specific patch is approved.

Safe work may continue in:
- docs/
- tools/
- configs/
- tests/

Before any functional edit to s43.py, the following must exist:
- PATCH_PROPOSAL
- IMPACT_ANALYSIS
- BACKUP
- HASH_BEFORE
- ROLLBACK_PLAN

## 6. Milestones

### Milestone 1: Baseline Preservation

Status: COMPLETE

Evidence:
- docs/S43_STRICT_GAP_REVIEW_SIGNOFF.md
- docs/S43_FINAL_REVIEW_CLOSURE_NOTE.md

Goal:
Preserve known-good state before portability work.

### Milestone 2: Dependency Inventory

Status: NEXT

Goal:
Identify imports, external packages, OS calls, shell calls, path assumptions, and Android/Termux dependencies.

Output files:
- docs/S43_DEPENDENCY_INVENTORY.md
- docs/S43_IMPORTS_INDEX.txt
- docs/S43_OS_PATH_AUDIT.md

### Milestone 3: Path and Runtime Audit

Status: PLANNED

Goal:
Find all absolute paths, environment assumptions, file writes, file reads, subprocess calls, shell commands, and platform-specific behavior.

Output files:
- docs/S43_PORTABILITY_AUDIT.md
- docs/S43_PATH_DEPENDENCY_REPORT.md

### Milestone 4: Config Layer Design

Status: PLANNED

Goal:
Design a configuration system that allows the same source package to run on different systems.

Possible files:
- configs/default.json
- configs/local.example.json
- docs/S43_CONFIG_SCHEMA.md

### Milestone 5: Adapter and Abstraction Layer

Status: PLANNED

Goal:
Separate platform-specific behavior from core logic.

Possible structure:

s43_runtime/
- paths.py
- environment.py
- platform_adapter.py
- config_loader.py

This phase should be planned before editing s43.py.

### Milestone 6: Standalone Build Preparation

Status: PLANNED

Goal:
Prepare executable packaging after dependency and path audits are complete.

Possible tools:
- PyInstaller
- Nuitka
- portable Python bundle

Output files:
- build/
- dist/
- docs/S43_STANDALONE_BUILD_NOTES.md

### Milestone 7: Cross-System Validation

Status: PLANNED

Goal:
Verify the package on at least:
- current Windows laptop
- another Windows machine
- Linux machine if needed
- offline execution if required

Output:
- docs/S43_CROSS_SYSTEM_VALIDATION.md

## 7. Do Not Do Yet

Do not modify s43.py directly.
Do not build .exe before dependency audit.
Do not remove old docs or evidence.
Do not assume Termux paths.
Do not introduce machine-specific absolute paths.

## 8. Immediate Next Step

The next safe action is to create a dependency and portability inventory without changing s43.py.

Recommended next document:
- docs/S43_DEPENDENCY_INVENTORY.md

## 9. Current Roadmap Status

ROADMAP_SAVED=YES
BASELINE_SAFE=YES
TERMUX_REMOVAL_TARGET=YES
NEXT_ACTION=DEPENDENCY_INVENTORY
S43_PY_PATCH_STATUS=NOT_APPROVED
