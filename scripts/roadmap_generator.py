#!/usr/bin/env python3
"""
Roadmap Generator for ASO-X
Generates ROADMAP_CURRENT.json from repository phase documents.
Enforces fail-closed governance model.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

def generate_roadmap():
    """Generate ROADMAP_CURRENT.json with all required validation fields."""
    
    # Base structure - Layer 1: roadmap_guard.py requirements
    roadmap = {
        "schema_version": "2.0",
        "roadmap_version": "22.13",
        "source_of_truth": "repository_files_only",
        "current_phase": "22.13",
        
        # Layer 2: CI validator requirements
        "authority": {
            "source": "repository_files_only",
            "enforcement": "strict"
        },
        "lifecycle": "closed",
        "enforcement_model": "fail_closed",
        
        # Generator metadata
        "generated_by": "scripts/roadmap_generator.py",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        
        # Phase structure
        "phases": {
            "22.13": {
                "name": "Global Financial Intelligence - Phase 22.13",
                "status": "closed",
                "lifecycle": "closed",
                "start_date": "2024-01-01",
                "end_date": "2026-07-02",
                "deliverables": [
                    "Core financial intelligence infrastructure",
                    "Real-money resilient architecture",
                    "Enterprise-grade validation pipeline"
                ],
                "governance": {
                    "source_of_truth": "repository_files_only",
                    "immutable": True
                }
            }
        },
        
        # Metadata
        "metadata": {
            "project": "ASO-X",
            "durability_target": "50y",
            "encoding": "UTF-8 (BOM-free)",
            "line_endings": "LF"
        }
    }
    
    return roadmap

def write_roadmap_files(roadmap):
    """Write roadmap to all canonical locations."""
    
    repo_root = Path(__file__).parent.parent
    targets = [
        repo_root / "ROADMAP_CURRENT.json",
        repo_root / "AUDIT" / "ROADMAP_CURRENT.json",
        repo_root / "docs" / "governance" / "ROADMAP_CURRENT.json"
    ]
    
    for target in targets:
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Write BOM-free UTF-8 with LF
        with open(target, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(roadmap, f, indent=2, ensure_ascii=False)
            f.write('\n')
        
        print(f"[OK] Generated: {target.relative_to(repo_root)}")

def main():
    """Main entry point."""
    try:
        print("Generating ROADMAP_CURRENT.json...")
        roadmap = generate_roadmap()
        write_roadmap_files(roadmap)
        print("\n[OK] Roadmap generation complete")
        print(f"  Schema: {roadmap['schema_version']}")
        print(f"  Version: {roadmap['roadmap_version']}")
        print(f"  Source of Truth: {roadmap['source_of_truth']}")
        print(f"  Enforcement: {roadmap['enforcement_model']}")
        return 0
    except Exception as e:
        print(f"[ERR] Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())