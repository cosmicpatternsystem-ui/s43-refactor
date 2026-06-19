# AKIA Secret Scan False Positive Review

Status: REVIEWED_FALSE_POSITIVE

Finding:

- File: s43.py
- Original pattern: AKIA[0-9A-Z]{16}
- Original PowerShell check used case-insensitive matching.
- Reported location: s43.py:48897:15987
- Reported line length: 1287100

Assessment:

- The detected text begins with AKiA, not AKIA.
- AWS access key IDs are case-sensitive and the AKIA prefix must be uppercase.
- The match appears inside a very large encoded/blob-like line, not in a credential assignment, environment variable, config file, AWS SDK call, or secret storage context.
- A case-sensitive scan using Select-String -CaseSensitive did not find any uppercase AKIA[0-9A-Z]{16} value.

Conclusion:

- This finding is treated as a false positive caused by PowerShell's default case-insensitive regex behavior.
- No full candidate secret value is recorded in this audit file.

Required follow-up:

- If GitHub secret scanning, AWS, or another provider independently reports an active credential, revoke/disable it immediately and create a new clean baseline.
