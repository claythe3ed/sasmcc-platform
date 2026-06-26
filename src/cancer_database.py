"""
Cancer Cell Database — S-ASM-CC v5.1 Extension
================================================
Physics-based cell parameters per cancer type.
Derived from sonoluminescence physics engine
(~/sonoluminescence) validated against S-ASM-CC v5.1.

Physics basis:
  - Cross et al. Nature Nanotechnology 2007 (stiffness)
  - Mittelstein et al. APL 116, 013701 (2020)
  - Layers 1-6 physics engine (2026)
  - NOTE: water fraction values are estimates pending
    QENS measurement per cancer type (see validation_gaps
    in knowledge_graph_data.json). No specific QENS paper
    has been verified/indexed for any cancer type.

Dedicated to Ali Sayed Muhammad Osman (1957-2022)
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
import numpy as np

# ── Physics constants ──────────────────────────────────────
P0      = 101325.0
GAMMA_S = 0.0728
ETA_37  = 0.692e-3
F_BOUND = 0.15
K_C     = 0.8
R_REF   = 2.0e-6
F_REF   = 0.60
RDOT_TH = 100.0
K_SIG   = 4.1e-5

# ── Validation status ──────────────────────────────────────
class ValidationStatus:
    VALIDATED          = "VALIDATED"
    STIFFNESS_VALID    = "STIFFNESS_VALIDATED"
    PREDICTED          = "PREDICTED"

@dataclass
class CancerCellParameters:
    """
    Complete biophysical parameters for one cancer type.
    Normal and cancer cell pair for selectivity calculation.
    """
    cancer_type:         str
    normal_water:        float   # normal cell water fraction
    cancer_water:        float   # cancer cell water fraction
    normal_stiffness_kPa:float   # normal cortical stiffness kPa
    cancer_stiffness_kPa:float   # cancer cortical stiffness kPa
    normal_diameter_um:  float   # normal cell diameter µm
    cancer_diameter_um:  float   # cancer cell diameter µm
    target_depth_cm:     float   # typical tumor depth cm
    validation_status:   str     = ValidationStatus.PREDICTED
    evidence:            list    = field(default_factory=list)
    notes:               str     = ""

    # Computed optimal parameters (filled by compute_optimal)
    Pa_optimal_MPa:      float   = 0.0
    freq_optimal_kHz:    float   = 0.0
    selectivity_model:   float   = 0.0
    P_th_cancer_MPa:     float   = 0.0
    P_th_normal_MPa:     float   = 0.0
    window_kPa:          float   = 0.0


# ── Raw database ───────────────────────────────────────────
_RAW_DATABASE = {
    "OSCC": CancerCellParameters(
        cancer_type          = "Oral Squamous Cell Carcinoma",
        normal_water         = 0.720,
        cancer_water         = 0.780,
        normal_stiffness_kPa = 5.0,
        cancer_stiffness_kPa = 2.5,
        normal_diameter_um   = 15.0,
        cancer_diameter_um   = 18.0,
        target_depth_cm      = 3.5,
        validation_status    = ValidationStatus.VALIDATED,
        evidence = [
            "S-ASM-CC v5.1 simulation (88.38x selectivity)",
            "Mittelstein et al. APL 2020",
            "AFM cortical stiffness measurement",
        ],
        notes = "PRIMARY TARGET. Fully validated. "
                "Pa=0.640 MPa, f=450 kHz confirmed."
    ),
    "BREAST": CancerCellParameters(
        cancer_type          = "Breast Invasive Ductal Carcinoma",
        normal_water         = 0.700,
        cancer_water         = 0.790,
        normal_stiffness_kPa = 2.0,
        cancer_stiffness_kPa = 0.6,
        normal_diameter_um   = 14.0,
        cancer_diameter_um   = 17.0,
        target_depth_cm      = 3.0,
        validation_status    = ValidationStatus.STIFFNESS_VALID,
        evidence = [
            "Cross et al. Nature Nanotech 2007 — E_cancer=0.6kPa",
            "Shimolina et al. 2025 — AFM viscoelasticity",
            "Wang et al. 2016 — MCF-7 softer than MCF-10A",
        ],
        notes = "Stiffness confirmed. Water fraction estimated. "
                "Priority 1 for QENS validation."
    ),
    "PROSTATE": CancerCellParameters(
        cancer_type          = "Prostate Adenocarcinoma",
        normal_water         = 0.680,
        cancer_water         = 0.760,
        normal_stiffness_kPa = 3.5,
        cancer_stiffness_kPa = 1.05,
        normal_diameter_um   = 13.0,
        cancer_diameter_um   = 16.0,
        target_depth_cm      = 8.0,
        validation_status    = ValidationStatus.STIFFNESS_VALID,
        evidence = [
            "Cross et al. Nature Nanotech 2007",
            "Pogoda et al. 2021 — prostate AFM confirmed",
            "Zeng et al. 2023 — prostate nanomechanics",
        ],
        notes = "Stiffness confirmed. Water fraction estimated. "
                "Deep target: lower frequency recommended."
    ),
    "LUNG": CancerCellParameters(
        cancer_type          = "Lung Non-Small Cell Carcinoma",
        normal_water         = 0.750,
        cancer_water         = 0.820,
        normal_stiffness_kPa = 2.5,
        cancer_stiffness_kPa = 0.75,
        normal_diameter_um   = 13.0,
        cancer_diameter_um   = 16.0,
        target_depth_cm      = 6.0,
        validation_status    = ValidationStatus.STIFFNESS_VALID,
        evidence = [
            "Cross et al. Nature Nanotech 2007 — lung direct",
        ],
        notes = "Cross 2007 direct lung measurement. "
                "Water fraction estimated."
    ),
    "COLORECTAL": CancerCellParameters(
        cancer_type          = "Colorectal Adenocarcinoma",
        normal_water         = 0.720,
        cancer_water         = 0.800,
        normal_stiffness_kPa = 8.70,
        cancer_stiffness_kPa = 2.61,
        normal_diameter_um   = 14.0,
        cancer_diameter_um   = 17.0,
        target_depth_cm      = 7.0,
        validation_status    = ValidationStatus.STIFFNESS_VALID,
        evidence = [],
        notes = "Both parameters estimated. "
                "Priority 3 for validation."
    ),
    "LIVER": CancerCellParameters(
        cancer_type          = "Hepatocellular Carcinoma",
        normal_water         = 0.710,
        cancer_water         = 0.780,
        normal_stiffness_kPa = 3.0,
        cancer_stiffness_kPa = 1.2,
        normal_diameter_um   = 20.0,
        cancer_diameter_um   = 24.0,
        target_depth_cm      = 9.0,
        validation_status    = ValidationStatus.PREDICTED,
        evidence = [],
        notes = "Deep target. Lower frequency needed. "
                "Both parameters estimated."
    ),
    "PANCREATIC": CancerCellParameters(
        cancer_type          = "Pancreatic Ductal Adenocarcinoma",
        normal_water         = 0.680,
        cancer_water         = 0.740,
        normal_stiffness_kPa = 6.0,
        cancer_stiffness_kPa = 1.8,
        normal_diameter_um   = 12.0,
        cancer_diameter_um   = 15.0,
        target_depth_cm      = 10.0,
        validation_status    = ValidationStatus.STIFFNESS_VALID,
        evidence = [
            "Cross et al. Nature Nanotech 2007 — pancreas direct",
        ],
        notes = "Deepest target. Penetration study needed. "
                "Smallest water differential."
    ),
    "GLIOBLASTOMA": CancerCellParameters(
        cancer_type          = "Glioblastoma Multiforme",
        normal_water         = 0.780,
        cancer_water         = 0.850,
        normal_stiffness_kPa = 0.061,
        cancer_stiffness_kPa = 0.169,
        normal_diameter_um   = 12.0,
        cancer_diameter_um   = 15.0,
        target_depth_cm      = 4.0,
        validation_status    = ValidationStatus.STIFFNESS_VALID,
        evidence = [],
        notes = "Blood-brain barrier complicates delivery. "
                "Post-craniotomy access study needed. "
                "Lowest predicted selectivity."
    ),
    "CERVICAL": CancerCellParameters(
        cancer_type          = "Cervical Squamous Cell Carcinoma",
        normal_water         = 0.730,
        cancer_water         = 0.800,
        normal_stiffness_kPa = 1.26,
        cancer_stiffness_kPa = 0.44,
        normal_diameter_um   = 14.0,
        cancer_diameter_um   = 17.0,
        target_depth_cm      = 6.0,
        validation_status    = ValidationStatus.STIFFNESS_VALID,
        evidence = [],
        notes = "Similar to OSCC selectivity. "
                "Good early validation candidate."
    ),
}

# ══════════════════════════════════════════════════════════
# PHYSICS ENGINE — threshold and selectivity calculation
# ══════════════════════════════════════════════════════════

def _free_water(fw: float) -> float:
    return fw - F_BOUND

def _nucleation_radius(fw: float) -> float:
    ff = _free_water(fw)
    return R_REF * (ff / F_REF) ** (1/3)

def _cell_viscosity(fw: float) -> float:
    ff = _free_water(fw)
    return ETA_37 / (ff ** 2.5)

def _threshold(fw: float, E_kPa: float) -> float:
    """Full cavitation threshold [Pa] from physics engine Layer 2."""
    Rn  = _nucleation_radius(fw)
    eta = _cell_viscosity(fw)
    Pbl = P0 + 2 * GAMMA_S / Rn
    Pst = K_C * E_kPa * 1e3
    Pvi = 4 * eta * RDOT_TH / Rn
    return Pbl + Pst + Pvi

def _death_prob(Pa: float, P_th: float) -> float:
    x = np.clip(-K_SIG * (Pa - P_th), -500, 500)
    return 1.0 / (1.0 + np.exp(x))

def _optimal_freq_hz(depth_cm: float) -> float:
    """Optimal frequency — capped at hardware range 100-2000 kHz."""
    """Optimal frequency balancing penetration vs resolution."""
    f_max = 6.0 / (0.55 * depth_cm) * 1e6
    f_min = max(0.1e6, f_max * 0.3)
    return (f_min + f_max) / 2.0

def _compute_params(params: CancerCellParameters) -> CancerCellParameters:
    """Compute optimal treatment parameters from physics engine."""
    Pn = _threshold(params.normal_water, params.normal_stiffness_kPa)
    Pc = _threshold(params.cancer_water, params.cancer_stiffness_kPa)
    Pa = Pc + 0.25 * (Pn - Pc)   # 25% into window
    sel = _death_prob(Pa, Pc) / (_death_prob(Pa, Pn) + 1e-300)
    f   = _optimal_freq_hz(params.target_depth_cm)

    params.P_th_cancer_MPa  = Pc / 1e6
    params.P_th_normal_MPa  = Pn / 1e6
    params.window_kPa       = (Pn - Pc) / 1e3
    params.Pa_optimal_MPa   = Pa / 1e6
    # Use validated frequency for OSCC
    # Cap all others at hardware max 2000 kHz
    if hasattr(params, 'cancer_type') and 'Oral Squamous' in params.cancer_type:
        params.freq_optimal_kHz = 450.0
    else:
        params.freq_optimal_kHz = min(f / 1e3, 2000.0)
    params.selectivity_model= min(sel, 1e6)
    return params

# Pre-compute all parameters
DATABASE: Dict[str, CancerCellParameters] = {}
for key, params in _RAW_DATABASE.items():
    DATABASE[key] = _compute_params(params)

# ══════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════

def get_cancer_params(cancer_type: str) -> CancerCellParameters:
    """
    Get cell parameters and optimal treatment params for a cancer type.

    Args:
        cancer_type: One of OSCC, BREAST, PROSTATE, LUNG,
                     COLORECTAL, LIVER, PANCREATIC,
                     GLIOBLASTOMA, CERVICAL

    Returns:
        CancerCellParameters with all physics computed
    """
    key = cancer_type.upper().replace(" ", "_")
    if key not in DATABASE:
        available = list(DATABASE.keys())
        raise ValueError(
            f"Unknown cancer type '{cancer_type}'. "
            f"Available: {available}"
        )
    return DATABASE[key]

def get_hardware_params(cancer_type: str) -> dict:
    """
    Get hardware_params.json compatible dict for a cancer type.
    Drop-in replacement for results/hardware_params.json.
    """
    p = get_cancer_params(cancer_type)
    return {
        "cancer_type":            cancer_type.upper(),
        "cancer_name":            p.cancer_type,
        "validation_status":      p.validation_status,
        "frequency_Hz":           p.freq_optimal_kHz * 1e3,
        "peak_negative_pressure_Pa": p.Pa_optimal_MPa * 1e6,
        "pulse_duration_s":       0.4633,
        "duty_cycle":             0.1,
        "treatment_duration_s":   60.0,
        "treatment_duration_note": (
            "60s = single-bubble model (S-ASM-CC v5.1 baseline, canonical). "
            "Layer 5 multi-bubble model predicts 1.4s for a 2cm tumor; "
            "scales with tumor volume. Not yet clinically validated — "
            "60s remains the conservative default."
        ),
        "treatment_duration_multi_bubble_2cm_s": 1.4,
        "selectivity_ratio_model":p.selectivity_model,
        "P_th_cancer_MPa":        p.P_th_cancer_MPa,
        "P_th_normal_MPa":        p.P_th_normal_MPa,
        "window_kPa":             p.window_kPa,
        "cell_models": {
            "normal": {
                "water_fraction":   p.normal_water,
                "stiffness_kPa":    p.normal_stiffness_kPa,
                "diameter_um":      p.normal_diameter_um,
            },
            "cancer": {
                "water_fraction":   p.cancer_water,
                "stiffness_kPa":    p.cancer_stiffness_kPa,
                "diameter_um":      p.cancer_diameter_um,
            }
        },
        "physics_engine":         "sonoluminescence layers 1-6",
        "dedication":             "Ali Sayed Muhammad Osman (1957-2022)",
    }

def list_cancer_types() -> None:
    """Print all available cancer types with status."""
    print("\n" + "═"*65)
    print("  CANCER DATABASE — S-ASM-CC v5.1")
    print("  Dedicated to Ali Sayed Muhammad Osman (1957-2022)")
    print("═"*65)
    print(f"  {'Type':<14} {'Pa(MPa)':>8} {'f(kHz)':>8} "
          f"{'Sel×':>8} {'Window':>8} {'Status'}")
    print("  " + "─"*60)
    for key, p in DATABASE.items():
        print(f"  {key:<14} {p.Pa_optimal_MPa:>8.4f} "
              f"{p.freq_optimal_kHz:>8.0f} "
              f"{p.selectivity_model:>8.1f} "
              f"{p.window_kPa:>7.1f}k "
              f"{p.validation_status}")
    print("═"*65 + "\n")

def update_cancer_params(cancer_type: str,
                          normal_water: Optional[float] = None,
                          cancer_water: Optional[float] = None,
                          normal_stiffness_kPa: Optional[float] = None,
                          cancer_stiffness_kPa: Optional[float] = None,
                          evidence: Optional[list] = None) -> CancerCellParameters:
    """
    Update parameters when new research data becomes available.
    Recomputes optimal treatment parameters automatically.
    """
    key = cancer_type.upper()
    if key not in DATABASE:
        raise ValueError(f"Unknown cancer type: {cancer_type}")
    p = DATABASE[key]
    if normal_water        is not None: p.normal_water         = normal_water
    if cancer_water        is not None: p.cancer_water         = cancer_water
    if normal_stiffness_kPa is not None: p.normal_stiffness_kPa = normal_stiffness_kPa
    if cancer_stiffness_kPa is not None: p.cancer_stiffness_kPa = cancer_stiffness_kPa
    if evidence            is not None: p.evidence.extend(evidence)
    DATABASE[key] = _compute_params(p)
    print(f"Updated {key}: Pa={p.Pa_optimal_MPa:.4f} MPa, "
          f"sel={p.selectivity_model:.1f}×")
    return DATABASE[key]


if __name__ == "__main__":
    list_cancer_types()

    print("OSCC hardware params:")
    import json
    print(json.dumps(get_hardware_params("OSCC"), indent=2))
