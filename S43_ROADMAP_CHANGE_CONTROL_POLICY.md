# S43 Roadmap Change Control Policy

**Parent Roadmap:** S43_UNIFIED_OPERATIONAL_MASTER_ROADMAP.md  
**Status:** ACTIVE / MANDATORY  

---

## 1. Purpose

This policy controls all future changes to the S43 unified operational roadmap.

It prevents:

- duplicate roadmap creation,
- repeated decision-making,
- undocumented architectural changes,
- loss of Git/GitHub synchronization,
- loss of recovery evidence,
- uncontrolled production-readiness drift.

---

## 2. Mandatory Change Record

text
CHANGE_ID:
DATE:
REQUESTED_BY:
REASON:
AFFECTED_SECTIONS:
AFFECTED_FILES:
RISK:
DECISION:
APPROVED_BY:
GIT_COMMIT:
BACKUP_REFERENCE:

---

## 3. Change Classes

- CLASS A — Minor documentation clarification
- CLASS B — Operational rule change
- CLASS C — Architecture / runtime / safety impact
- CLASS D — Production status change

---

## 4. Git Requirements

Every approved change must be committed and pushed when ready.

---

## 5. Prohibited Actions

1. Creating a competing roadmap without superseding the existing one.
2. Editing the roadmap without decision-log context for major changes.
3. Changing production status without explicit approval.
4. Deleting roadmap evidence.
5. Relying on memory instead of documented decisions.
6. Making roadmap changes that are not committed to Git.

---

## 6. Required Persistence

The current roadmap must exist in:

- Local laptop repository
- Git history
- GitHub remote repository
- Backup archive after major changes

---

## 7. Current Policy Declaration

text
ROADMAP_CHANGE_CONTROL: ENABLED
UNAPPROVED_ROADMAP_CHANGES: NOT_ALLOWED
DUPLICATE_ROADMAPS: NOT_ALLOWED
GITHUB_SYNC_REQUIRED: YES
BACKUP_FOR_MAJOR_CHANGES: YES
