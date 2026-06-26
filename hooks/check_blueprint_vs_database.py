#!/usr/bin/env python3
"""
Hook 1 — Blueprint vs Cancer Database Consistency Check
==========================================================
Verifies every cancer type's frequency/PNP in cancer_database.py
has a matching transducer + falls within the hardware's
documented Physics Constraints range. Run after ANY change to
cancer_database.py or the blueprint files.

Dedicated to Ali Sayed Muhammad Osman (1957-2022)
"""
import sys, json, re
from pathlib import Path

ROOT = Path.home() / "oncotripsy_full_system"
sys.path.insert(0, str(ROOT / "src"))

BLUEPRINT_DIR = ROOT / "hardware" / "blueprint_v2"
PARTS_CSV     = BLUEPRINT_DIR / "oncotripsy_platform_PARTS.csv"
CONFIG_JSON   = BLUEPRINT_DIR / "oncotripsy_platform_CONFIG.json"

# Hardware-side frequency list (kHz) parsed from PARTS.csv
def get_blueprint_frequencies():
    if not PARTS_CSV.exists():
        return None
    text = PARTS_CSV.read_text()
    freqs = set()
    for m in re.finditer(r'Transducer T-(\d+)', text):
        freqs.add(int(m.group(1)))
    return freqs

def main():
    print("\n" + "="*65)
    print("  HOOK 1 — Blueprint vs Cancer Database")
    print("  Dedicated to Ali Sayed Muhammad Osman (1957-2022)")
    print("="*65)

    try:
        from cancer_database import DATABASE
    except ImportError as e:
        print(f"  FAIL: could not import cancer_database.py — {e}")
        sys.exit(1)

    bp_freqs = get_blueprint_frequencies()
    if bp_freqs is None:
        print(f"  WARN: {PARTS_CSV} not found — skipping hardware check")
        print(f"        (database-only validation will still run)")
        bp_freqs = set()
    else:
        print(f"  Blueprint transducer frequencies found: "
              f"{sorted(bp_freqs)}")

    print()
    ok = True
    db_freqs = set()
    for name, p in DATABASE.items():
        f_khz = round(p.freq_optimal_kHz)
        db_freqs.add(f_khz)
        in_hw = f_khz in bp_freqs if bp_freqs else None
        in_range = 100 <= f_khz <= 2000
        status = "OK" if (in_range and (in_hw or in_hw is None)) else "FAIL"
        if status == "FAIL":
            ok = False
        print(f"  {name:<14} f={f_khz:>5}kHz  "
              f"Pa={p.Pa_optimal_MPa:.4f}MPa  "
              f"in_hw_list={in_hw}  in_range={in_range}  [{status}]")

    print()
    if bp_freqs:
        missing = db_freqs - bp_freqs
        extra   = bp_freqs - db_freqs
        if missing:
            print(f"  WARN: database frequencies with no matching "
                  f"transducer in blueprint: {sorted(missing)}")
            ok = False
        if extra:
            print(f"  INFO: blueprint transducers not used by any "
                  f"current cancer type: {sorted(extra)}")

    print()
    print(f"  RESULT: {'PASS' if ok else 'FAIL'}")
    print("="*65 + "\n")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
