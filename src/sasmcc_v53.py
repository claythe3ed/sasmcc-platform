"""
SUPERCONDUCTIVE ASM MEMORIAL COMPUTATIONAL CORE v5.3
Pan-Cancer Engine — CANONICAL VERSION

In memory of Ali Sayed Muhammad Osman (1957-2022)

v5.3 supersedes v5.2 (sasmcc_v52.py, retained only as an
audit trail of the development process). Single engine class.

Physics fixes vs v5.1 (these are bug fixes, not optional modes
— there is no v5.1-compatible flag because v5.1's behavior was
incorrect):
  1. Nucleation threshold = Blake + stiffness + viscosity
     (Layer 2). Viscosity is the dominant term (~60%).
  2. Cytoskeletal disruption gated by nucleation probability
     — no bubble, no mechanical disruption.

Validation strategy:
  - THRESHOLD AGREEMENT (continuous %): v5.3's per-cell
    nucleation_threshold() and cancer_database.py's _threshold()
    use the identical Layer 2 formula and should agree to <5%.
    Large disagreement here indicates a real bug.
  - SELECTIVITY DIRECTION (binary): does P_kill(cancer) >
    P_kill(normal)? This is the clinically relevant check.
  - physics_selectivity (population-sigmoid model, from
    cancer_database) and this-run selectivity_ratio
    (deterministic multi-pulse model) are DIFFERENT METRICS
    BY DESIGN and are reported separately, never as an "error".

Usage:
    from sasmcc_v53 import run_cancer_type, SASMCCEngine
    results = run_cancer_type("BREAST")
"""

import sys, os, json, logging
from pathlib import Path
from typing import Dict, Any
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from sasmcc_v51 import (
    CellType, CellBiophysicsConfig, OncotripsyConfig,
    CavitationConfig, CellBiophysics,
    CellSeededCavitation, OncotripsyPulse, ValidationLedger,
)
from cancer_database import (
    get_cancer_params, get_hardware_params,
    list_cancer_types, DATABASE, ValidationStatus,
)


# ══════════════════════════════════════════════════════════
# PHYSICS-CORRECTED CAVITATION (Layer 2)
# ══════════════════════════════════════════════════════════

class CellSeededCavitationV3(CellSeededCavitation):
    """
    Physics-corrected nucleation threshold.
    Identical formula to cancer_database.py._threshold() —
    this is what enables the threshold-agreement validation check.
    """
    P0      = 101325.0
    GAMMA_S = 0.0728
    ETA_37  = 0.692e-3
    F_BOUND = 0.15
    K_C     = 0.8
    R_REF   = 2.0e-6
    F_REF   = 0.60
    RDOT_TH = 100.0
    SIGMOID_WIDTH = 0.0245e6  # calibrated to OSCC ~73.9x, Layer 2

    def _free_water(self, fw):
        return fw - self.F_BOUND

    def _nucleation_radius(self, fw):
        return self.R_REF * (self._free_water(fw) / self.F_REF) ** (1/3)

    def _cell_viscosity(self, fw):
        return self.ETA_37 / (self._free_water(fw) ** 2.5)

    def nucleation_threshold(self, frequency: float = None) -> float:
        """
        `frequency` retained only for base-class signature
        compatibility (nucleation_probability calls
        threshold(frequency)). Threshold is a per-cell property;
        frequency does not enter here. System-level frequency
        selection (penetration vs resolution) is handled in
        cancer_database._optimal_freq_hz(), not per-cell.
        """
        fw  = self.cell.cytoplasmic_water_fraction
        E   = self.cell.cortical_youngs_modulus / 1e3
        Rn  = self._nucleation_radius(fw)
        eta = self._cell_viscosity(fw)
        Pbl = self.P0 + 2 * self.GAMMA_S / Rn
        Pst = self.K_C * E * 1e3
        Pvi = 4 * eta * self.RDOT_TH / Rn
        return Pbl + Pst + Pvi

    def nucleation_probability(self, pressure_amplitude: float,
                                frequency: float = None) -> float:
        threshold = self.nucleation_threshold(frequency)
        P_reduced = pressure_amplitude - threshold
        if P_reduced > 0:
            return min(1.0 / (1.0 + np.exp(-P_reduced / self.SIGMOID_WIDTH)), 1.0)
        return 0.0


class OncotripsyPulseV3(OncotripsyPulse):
    """Cytoskeletal disruption gated by nucleation probability."""
    def __init__(self, cell, config=None):
        super().__init__(cell, config)
        self.cavitation = CellSeededCavitationV3(cell, CavitationConfig())

    def cell_death_probability(self, frequency=None, pressure_amplitude=None,
                                pulse_duration=None, duty_cycle=None,
                                total_exposure_time=None) -> float:
        f     = frequency or self.config.frequency
        P     = pressure_amplitude or self.config.peak_negative_pressure
        pd    = pulse_duration or self.config.pulse_duration
        dc    = duty_cycle or self.config.duty_cycle
        t_exp = total_exposure_time or self.config.treatment_duration

        p_nuc    = self.cavitation.nucleation_probability(P, f)
        dynamics = self.cavitation.bubble_dynamics(P, f)
        p_damage = dynamics['rupture_probability']

        cyto = self.cavitation.cytoskeletal_disruption(P, f, pd)
        # GATE: no nucleation -> no cytoskeletal disruption
        p_disruption = cyto['disruption_probability'] * p_nuc

        p_death_per_pulse = 1.0 - (
            (1.0 - p_nuc * p_damage) * (1.0 - p_disruption)
        )

        prf = dc / pd
        n_pulses = int(t_exp * prf)
        if p_death_per_pulse > 0:
            return 1.0 - (1.0 - p_death_per_pulse) ** n_pulses
        return 0.0


# ══════════════════════════════════════════════════════════
# VALIDATOR
# ══════════════════════════════════════════════════════════

class PhysicsEngineValidator:
    """
    Two independent, honestly-separated checks:
      1. threshold_error_pct  — continuous, v5.3 vs cancer_database
         (same formula -> should be near 0%; large error = real bug)
      2. selectivity_direction_ok — binary clinical outcome check
    Does NOT compare sasmcc selectivity ratio to physics_selectivity
    as an "error" — they are different metrics by construction.
    """
    THRESHOLD_TOLERANCE_PCT = 5.0

    def validate(self, sasmcc_pth_cancer_Pa, sasmcc_pth_normal_Pa,
                  db_pth_cancer_Pa, db_pth_normal_Pa,
                  p_kill_cancer, p_kill_normal,
                  cancer_type, validation_status):

        err_c = abs(sasmcc_pth_cancer_Pa - db_pth_cancer_Pa) / db_pth_cancer_Pa
        err_n = abs(sasmcc_pth_normal_Pa - db_pth_normal_Pa) / db_pth_normal_Pa
        threshold_error_pct = max(err_c, err_n) * 100
        threshold_ok = threshold_error_pct < self.THRESHOLD_TOLERANCE_PCT

        direction_ok = p_kill_cancer > p_kill_normal

        confidence = {
            ValidationStatus.VALIDATED:       "HIGH",
            ValidationStatus.STIFFNESS_VALID: "MEDIUM",
            ValidationStatus.PREDICTED:       "LOW",
        }.get(validation_status, "UNKNOWN")

        if threshold_ok and direction_ok and confidence == "HIGH":
            rec = "Engine matches physics model and shows correct selectivity — proceed"
        elif threshold_ok and direction_ok:
            rec = "Selectivity direction correct; underlying water/stiffness data still need experimental validation"
        else:
            rec = "Threshold disagreement or wrong-direction selectivity — review engine code"

        return {
            'cancer_type':            cancer_type,
            'threshold_error_pct':    threshold_error_pct,
            'threshold_within_tolerance': threshold_ok,
            'selectivity_direction_ok':   direction_ok,
            'validation_status':     validation_status,
            'confidence':            confidence,
            'recommendation':        rec,
            'dedication':            'Ali Sayed Muhammad Osman (1957-2022)',
        }


# ══════════════════════════════════════════════════════════
# CANONICAL ENGINE
# ══════════════════════════════════════════════════════════

class SASMCCEngine:
    """S-ASM-CC v5.3 — Pan-Cancer Engine (canonical, single class)."""
    VERSION = "5.3"

    def __init__(self, cancer_type: str = "OSCC"):
        self.cancer_type = cancer_type.upper()
        self.db = get_cancer_params(cancer_type)
        self.logger = self._setup_logger()
        self.validator = PhysicsEngineValidator()

        normal_cfg = CellBiophysicsConfig(
            name=f"normal_{cancer_type.lower()}", cell_type=CellType.NORMAL,
            cytoplasmic_water_fraction=self.db.normal_water,
            cortical_youngs_modulus=self.db.normal_stiffness_kPa * 1e3,
            cell_diameter=self.db.normal_diameter_um * 1e-6)
        cancer_cfg = CellBiophysicsConfig(
            name=f"cancer_{cancer_type.lower()}", cell_type=CellType.CANCER,
            cytoplasmic_water_fraction=self.db.cancer_water,
            cortical_youngs_modulus=self.db.cancer_stiffness_kPa * 1e3,
            cell_diameter=self.db.cancer_diameter_um * 1e-6)

        self.normal_cell = CellBiophysics(normal_cfg)
        self.cancer_cell = CellBiophysics(cancer_cfg)

        self.onco_cfg = OncotripsyConfig(
            frequency=self.db.freq_optimal_kHz * 1e3,
            peak_negative_pressure=self.db.Pa_optimal_MPa * 1e6,
            pulse_duration=0.4633, duty_cycle=0.10,
            treatment_duration=60.0)

        self.normal_pulse = OncotripsyPulseV3(self.normal_cell, self.onco_cfg)
        self.cancer_pulse = OncotripsyPulseV3(self.cancer_cell, self.onco_cfg)
        self.ledger = ValidationLedger()

        self.logger.info(f"S-ASM-CC v{self.VERSION} — {cancer_type} "
                         f"[{self.db.validation_status}] "
                         f"Pa={self.db.Pa_optimal_MPa:.4f}MPa "
                         f"f={self.db.freq_optimal_kHz:.0f}kHz")

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"SASMCC53_{self.cancer_type}")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            h = logging.StreamHandler()
            h.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(h)
        return logger

    def run_oncotripsy_simulation(self) -> Dict[str, Any]:
        p_cancer = self.cancer_pulse.cell_death_probability()
        p_normal = self.normal_pulse.cell_death_probability()
        sel = p_cancer / p_normal if p_normal > 0.001 else p_cancer / 0.001

        sasmcc_pth_cancer = self.cancer_pulse.cavitation.nucleation_threshold()
        sasmcc_pth_normal = self.normal_pulse.cavitation.nucleation_threshold()

        pv = self.validator.validate(
            sasmcc_pth_cancer, sasmcc_pth_normal,
            self.db.P_th_cancer_MPa * 1e6, self.db.P_th_normal_MPa * 1e6,
            p_cancer, p_normal,
            self.cancer_type, self.db.validation_status)

        results = {
            'cancer_type':        self.cancer_type,
            'cancer_name':        self.db.cancer_type,
            'p_death_cancer':     p_cancer,
            'p_death_normal':     p_normal,
            'selectivity_ratio':  min(sel, 1e6),
            'physics_selectivity_model': self.db.selectivity_model,
            'physics_validation': pv,
        }

        print("\n" + "═"*70)
        print(f"  S-ASM-CC v{self.VERSION} — {self.db.cancer_type}")
        print(f"  Dedicated to Ali Sayed Muhammad Osman (1957-2022)")
        print("═"*70)
        print(f"  Pa = {self.db.Pa_optimal_MPa:.4f} MPa   "
              f"f = {self.db.freq_optimal_kHz:.0f} kHz")
        print(f"  P_kill(cancer) = {p_cancer:.6f}")
        print(f"  P_kill(normal) = {p_normal:.6f}")
        print(f"  Selectivity (this run, deterministic): {results['selectivity_ratio']:.2f}x")
        print(f"  Selectivity (Layer 6 population model): {self.db.selectivity_model:.1f}x")
        print(f"  Threshold agreement vs Layer 2: {pv['threshold_error_pct']:.2f}% "
              f"({'OK' if pv['threshold_within_tolerance'] else 'CHECK'})")
        print(f"  Selectivity direction correct: "
              f"{'YES' if pv['selectivity_direction_ok'] else 'NO'}")
        print(f"  Confidence: {pv['confidence']}  |  Status: {pv['validation_status']}")
        print(f"  -> {pv['recommendation']}")
        print("═"*70)
        return results

    def save_hardware_params(self, output_dir: str = "results") -> str:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        hw = get_hardware_params(self.cancer_type)
        fname = f"{output_dir}/hardware_params_{self.cancer_type.lower()}.json"
        with open(fname, 'w') as f:
            json.dump(hw, f, indent=2)
        print(f"  Hardware params -> {fname}")
        return fname


def run_cancer_type(cancer_type: str, save_results: bool = True,
                     output_dir: str = "results") -> Dict[str, Any]:
    engine = SASMCCEngine(cancer_type)
    results = engine.run_oncotripsy_simulation()
    if save_results:
        engine.save_hardware_params(output_dir)
    return results


if __name__ == "__main__":
    print("\n" + "═"*70)
    print("  S-ASM-CC v5.3 — Pan-Cancer Engine (canonical)")
    print("  In memory of Ali Sayed Muhammad Osman (1957-2022)")
    print("═"*70)
    list_cancer_types()
    for ct in DATABASE.keys():
        run_cancer_type(ct, output_dir="results")
    print("\n  All cancer types processed. Hardware params in results/")
    print("  In memory of Ali Sayed Muhammad Osman (1957-2022)\n")
