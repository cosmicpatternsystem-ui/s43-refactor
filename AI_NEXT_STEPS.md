# S43 AI Next Steps

This is a companion note for future AI and human review.

Current priority:
- Compare MY_S43_LATEST.py with s43_instrumented_LATEST.py.
- Classify differences before any merge.
- Keep MY_S43_LATEST.py as canonical.
- Keep s43.py as runtime copy.
- Keep s43_instrumented_LATEST.py as candidate/reference only.

Do not:
- Do not replace canonical code before diff review.
- Do not enable autonomous trading.
- Do not use pasted/log text as source code.
- Do not edit s43.py as the primary source.

Safe order:
1. Review diff.
2. Classify changes.
3. Port only safe and understood changes to MY_S43_LATEST.py.
4. Run py_compile.
5. Copy MY_S43_LATEST.py to s43.py only after validation.