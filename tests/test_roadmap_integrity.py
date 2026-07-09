import os
import sys

CANONICAL_ROADMAP = os.path.join("docs", "governance", "ROADMAP_CURRENT.json")

def verify_roadmap_integrity():
    if not os.path.exists(CANONICAL_ROADMAP):
        sys.exit(1)

    shadow_copies = []
    exclusions = [".git", ".roadmap_archive", "ARCHIVE", "_LOCAL_DEFERRED_AI_ARTIFACTS"]
    
    for root, dirs, files in os.walk("."):
        if any(x in root for x in exclusions):
            continue
        if "ROADMAP_CURRENT.json" in files:
            current_path = os.path.join(root, "ROADMAP_CURRENT.json")
            if os.path.abspath(current_path) != os.path.abspath(CANONICAL_ROADMAP):
                shadow_copies.append(current_path)

    if shadow_copies:
        sys.exit(1)

if __name__ == "__main__":
    verify_roadmap_integrity()
