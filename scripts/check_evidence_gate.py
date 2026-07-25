import datetime, json, sys
from pathlib import Path

ROADMAP = Path('docs/governance/ROADMAP_CURRENT.json')
WAIVER_EXPIRY = datetime.date(2026, 8, 1)

def evaluate_phase(phase: dict) -> str:
    if phase.get('status') != 'complete':
        return 'GATE_SKIP'
    if phase.get('evidence'):
        return 'GATE_PASS'
    if phase.get('documentation_only'):
        if datetime.date.today() <= WAIVER_EXPIRY:
            print(f"[GATE_WAIVED] {phase['id']} - waiver active until {WAIVER_EXPIRY}")
            return 'GATE_WAIVED'
        print(f"[GATE_FAIL] {phase['id']} - waiver expired {WAIVER_EXPIRY}")
        return 'GATE_FAIL'
    return 'GATE_FAIL'

def main():
    phases = json.loads(ROADMAP.read_text('utf-8')).get('phases', [])
    results = {r: [] for r in ('GATE_PASS','GATE_WAIVED','GATE_FAIL','GATE_SKIP')}
    for p in phases:
        results[evaluate_phase(p)].append(p['id'])
    for r, ids in results.items():
        if ids:
            print(f"{r}: {len(ids)}")
    if results['GATE_FAIL']:
        print("FAILURES:", results['GATE_FAIL'])
        sys.exit(1)

if __name__ == '__main__':
    main()
