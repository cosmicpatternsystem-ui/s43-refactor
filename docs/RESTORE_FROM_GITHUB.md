# Restore From GitHub

Clone:

git clone git@github.com:cosmicpatternsystem-ui/s43-refactor.git s43_refactor_restored
cd s43_refactor_restored
git checkout phase16-core-governance-integration

Verify:

$h = (Get-FileHash ".\s43.py" -Algorithm SHA256).Hash.ToUpperInvariant()
$l = (Get-Content ".\s43.py" | Measure-Object -Line).Lines
Expected SHA256: 3DDFCF94CCC1A641AC98ADD90A4338D7138BED681AE0894C7E91E6941A8BEB4C
Expected line count: 29856

Restore is valid only if SHA256 and line count match exactly.
