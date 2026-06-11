# S43 Diff Notes

Canonical:
- MY_S43_LATEST.py

Runtime copy:
- s43.py

Candidate/reference:
- s43_instrumented_LATEST.py

Known state:
- MY_S43_LATEST.py and s43.py are the baseline pair.
- s43_instrumented_LATEST.py is a candidate and must be reviewed before merging.

Cleanliness scan:
- Repeated-character scan only found normal section separators.
- Examples:
  - ################################################################################################
  - #===================================================================================================
- These are not junk.

pasted-text.txt:
- Not present in the active directory.
- Pasted/log text must not be used as source code.

Pending work:
- Compare MY_S43_LATEST.py with s43_instrumented_LATEST.py.
- Classify differences as safe logging, format-only, risk decision change, trade execution change, or unknown/risky.
- Only safe and understood changes may be ported into MY_S43_LATEST.py.