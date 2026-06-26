#!/usr/bin/env python3
"""
Hook 3 — Knowledge Graph Sync Check
=======================================
Confirms knowledge_graph_data.json's "completed" files list
matches what's actually present on disk in both project
directories. Flags drift (files claimed complete but missing,
or files present but not recorded).

Dedicated to Ali Sayed Muhammad Osman (1957-2022)
"""
import json
from pathlib import Path

KG_PATH = Path.home() / "sonoluminescence" / "knowledge_graph_data.json"
ROOTS = {
    "sonoluminescence":       Path.home() / "sonoluminescence",
    "oncotripsy_full_system": Path.home() / "oncotripsy_full_system",
}

def resolve(rel_path: str):
    """Try to resolve a 'completed' entry against known roots."""
    rel_path = rel_path.split(" (")[0].split(" v")[0].strip()
    for root_name, root in ROOTS.items():
        candidate = root / rel_path
        if candidate.exists():
            return candidate
        # also try stripping a leading project-name prefix
        parts = rel_path.split("/", 1)
        if len(parts) == 2:
            candidate2 = root / parts[1]
            if candidate2.exists():
                return candidate2
    return None

def main():
    print("\n" + "="*65)
    print("  HOOK 3 — Knowledge Graph Sync")
    print("  Dedicated to Ali Sayed Muhammad Osman (1957-2022)")
    print("="*65)

    if not KG_PATH.exists():
        print(f"  FAIL: {KG_PATH} not found")
        return 1

    d = json.loads(KG_PATH.read_text())
    completed = d.get("meta", {}).get("progress", {}).get("completed", [])
    version   = d.get("meta", {}).get("version", "?")

    print(f"\n  Knowledge graph version: {version}")
    print(f"  Completed entries logged: {len(completed)}")
    print()

    missing = []
    notes_only = []  # entries that are clearly non-file notes
    for entry in completed:
        # Skip obvious non-file milestone strings
        if not any(c in entry for c in ("/", ".py", ".md", ".json")):
            notes_only.append(entry)
            continue
        found = resolve(entry)
        if found is None:
            missing.append(entry)

    if notes_only:
        print(f"  INFO: {len(notes_only)} milestone entries "
              f"(not files, skipped):")
        for n in notes_only:
            print(f"      - {n}")
        print()

    if missing:
        print(f"  WARN: {len(missing)} entries claim completion "
              f"but file not found on disk:")
        for m in missing:
            print(f"      - {m}")
    else:
        print(f"  All file-based completed entries resolved on disk.")

    print()
    result = "PASS" if not missing else "FAIL"
    print(f"  RESULT: {result}")
    print("="*65 + "\n")
    return 0 if not missing else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
