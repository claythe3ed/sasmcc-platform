#!/usr/bin/env python3
"""
Hook 2 — Physics Engine Consistency Check
=============================================
Standalone, scriptable version of PhysicsEngineValidator.
Re-runs sasmcc_v53.py for all 9 cancer types and confirms:
  1. Threshold agreement vs Layer 2 stays under 5%
  2. Selectivity direction (P_kill cancer > P_kill normal)
     is correct for every type
Exits non-zero if ANY type fails either check — safe to wire
into a pre-commit hook or cron job.

Dedicated to Ali Sayed Muhammad Osman (1957-2022)
"""
import sys, io, contextlib
from pathlib import Path

ROOT = Path.home() / "oncotripsy_full_system"
sys.path.insert(0, str(ROOT / "src"))

def main():
    print("\n" + "="*65)
    print("  HOOK 2 — Physics Engine Consistency")
    print("  Dedicated to Ali Sayed Muhammad Osman (1957-2022)")
    print("="*65)

    try:
        from sasmcc_v53 import SASMCCEngine
        from cancer_database import DATABASE
    except ImportError as e:
        print(f"  FAIL: import error — {e}")
        sys.exit(1)

    all_ok = True
    print(f"\n  {'Type':<14} {'Thresh err%':>11} {'Dir OK':>7} "
          f"{'Status':<22} {'Result'}")
    print("  " + "-"*65)

    for name in DATABASE.keys():
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                engine = SASMCCEngine(name)
                results = engine.run_oncotripsy_simulation()
            pv = results['physics_validation']
            t_ok = pv['threshold_within_tolerance']
            d_ok = pv['selectivity_direction_ok']
            row_ok = t_ok and d_ok
            if not row_ok:
                all_ok = False
            print(f"  {name:<14} {pv['threshold_error_pct']:>10.2f}% "
                  f"{str(d_ok):>7} {pv['validation_status']:<22} "
                  f"{'PASS' if row_ok else 'FAIL'}")
        except Exception as e:
            all_ok = False
            print(f"  {name:<14} ERROR: {e}")

    print()
    print(f"  RESULT: {'PASS — all 9 cancer types consistent' if all_ok else 'FAIL — see above'}")
    print("="*65 + "\n")
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
