import json, re, sys
from pathlib import Path
from datetime import datetime, timezone

def parse_phase(p):
    t = p.read_text(encoding="utf-8").strip().split("\n")
    m = re.search(r"^#\s+(.+)$", t[0])
    if not m: return None
    n = re.match(r"PHASE_(\d+)_(\d+)", p.name)
    if not n: return None
    return {"id": f"{int(n[1])}.{int(n[2])}", "title": m[1].strip()}

phases = [parse_phase(p) for p in sorted(Path(".").glob("PHASE_*.md"))]
phases = [p for p in phases if p]

roadmap = {
    "schema_version": 2.0,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "generated_by": "asoctl.py roadmap",
    "phases": sorted(phases, key=lambda x: x["id"])
}

for t in ["ROADMAP_CURRENT.json", "docs/governance/ROADMAP_CURRENT.json", "AUDIT/ROADMAP_CURRENT.json"]:
    p = Path(t)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(roadmap, indent=2) + "\n", encoding="utf-8")

print(f"Generated {len(phases)} phases")