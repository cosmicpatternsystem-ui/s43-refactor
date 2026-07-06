# Portability and Platform Independence

This document defines the canonical portability and platform independence doctrine for the ASO-X repository.

## Platform Principles

- Preserve repository usability across Windows, Linux, and macOS where feasible.
- Prefer portable Python and repository-native validation patterns.
- Avoid unnecessary hardcoded environment assumptions in canonical workflows.
- Preserve cp1252-safe stdout behavior where repository standards require it.
- Preserve BOM-free UTF-8 LF text handling where repository standards require it.
- Favor atomic writes, deterministic outputs, and migration-friendly structures.
- Prefer local-first operation where feasible while remaining cloud-compatible.

## Independence Rule

No single hardware profile, operating system, runtime vendor, or hosted service should become the only viable path for operating the project.
