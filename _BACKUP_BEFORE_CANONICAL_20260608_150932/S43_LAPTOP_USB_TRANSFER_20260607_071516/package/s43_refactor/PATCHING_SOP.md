# S43 Safe Patching SOP

## Purpose

This document defines the standard safe workflow for applying patches to `s43.py` in Termux.

## Tools

Required tools:

- `termux_write_sh`
- `termux_write_text`
- `termux_verify_script`
- `termux_safe_apply_patch`

## Standard Workflow

### 1. Pre-flight check

Verify that the target file exists:


```bash
ls -l ~/s43.py

```

Verify that the patch file exists:


```bash
ls -l ./your_patch.patch

```

### 2. Apply the patch safely

Use the safe patch tool with backup retention:


```bash
termux_safe_apply_patch --keep-backups=5 ~/s43.py ./your_patch.patch

```

### 3. Check the latest patch log


```bash
cat "$(ls -1t ~/.tmp/termux_safe_patch_*.log | head -n 1)"

```

### 4. Python syntax validation


```bash
python -m py_compile ~/s43.py

```

### 5. Backup inspection


```bash
ls -1t ~/s43.py.bak.safe_patch.* | head

```

## Notes

- Do not apply patches manually unless absolutely necessary.
- Always use `termux_safe_apply_patch` for controlled patching.
- Keep at least 5 backups during active refactoring.
- Archive stable milestones before major changes.
