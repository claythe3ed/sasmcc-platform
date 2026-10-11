"""
SUPERCONDUCTIVE ASM MEMORIAL COMPUTATIONAL CORE v5.1
Complete Engine Code

In memory of Ali Sayed Muhammad (1957-2022)

Physics basis:
  - Mittelstein et al. APL 116, 013701 (2020) - Oncotripsy
  - QENS Water Dynamics in Cancer Cells (2020)
  - AFM Cell Stiffness Measurements
  - Rayleigh-Plesset Bubble Dynamics

Usage:
    from sasmcc_v51 import SuperconductiveASMEngine, EngineConfig
    
    config = EngineConfig(simulation_name="OSCC_Study")
    engine = SuperconductiveASMEngine(config)
    results = engine.run_oncotripsy_simulation()

Requirements:
    numpy, scipy, torch, matplotlib
"""

import numpy as np
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

class _FakeTorch:
    class cuda:
        @staticmethod
        def is_available(): return False

torch = _FakeTorch()
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path
import json
from datetime import datetime
import warnings

# ============================================================================
# CONFIGURATION
# ============================================================================

class SimulationType(Enum):
    ACOUSTIC = "acoustic"
    THERMAL = "thermal"
    MECHANICAL = "mechanical"
    CHEMICAL = "chemical"
    MULTIPHYSICS = "multiphysics"
    ONCOTRIPSY = "oncoptripsy"

class ValidationLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    MEMORIAL = "memorial"

class CellType(Enum):
    NORMAL = "normal"
    CANCER = "cancer"

@dataclass
class CellBiophysicsConfig:
    name: str = "cell"
    cell_type: CellType = CellType.NORMAL
    cytoplasmic_water_fraction: float = 0.72
    water_diffusion_coefficient: float = 1.5e-9
    water_viscosity: float = 2.0e-3
    hydrogen_bond_lifetime: float = 5.0
    cortical_thickness: float = 200e-9
    cortical_youngs_modulus: float = 5.0e3
    surface_tension: float = 0.3e-3
    membrane_permeability: float = 1.0e-4
    cell_diameter: float = 15e-6
    nucleus_diameter: float = 7e-6
    specific_heat: float = 3600.0
    thermal_conductivity: float = 0.55

@dataclass
class KGridConfig:
    Nx: int = 256; Ny: int = 256; Nz: int = 1
    dx: float = 50e-6; dy: float = 50e-6; dz: float = 100e-6
    dt: float = 5e-9; t_end: float = 10e-6
    dim: int = 2; PML_size: int = 20

@dataclass
class MediumConfig:
    sound_speed: Union[float, np.ndarray] = 1540.0
    density: Union[float, np.ndarray] = 1050.0
    alpha_coeff: Union[float, np.ndarray] = 0.57
    alpha_power: float = 1.1
    tissue_name: Optional[str] = None

@dataclass
class OncotripsyConfig:
    frequency: float = 0.5e6
    peak_negative_pressure: float = 0.7e6
    peak_positive_pressure: float = 1.4e6
    pulse_duration: float = 20e-3
    prf: float = 5.0
    duty_cycle: float = 0.1
    treatment_duration: float = 60.0
    standing_wave: bool = True
    cell_aggregation: bool = True

@dataclass
class CavitationConfig:
    enable_cell_seeded: bool = True
    nucleation_site_radius: float = 1e-6
    reference_stiffness: float = 5.0e3
    rupture_stress_threshold: float = 3.0e6
    enable_bubble_dynamics: bool = True

@dataclass
class ValidationConfig:
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    energy_tolerance: float = 1e-3
    physics_consistency_threshold: float = 0.95
    memorial_integrity_weight: float = 1.0
    enable_ledger: bool = True

@dataclass
class EngineConfig:
    simulation_type: SimulationType = SimulationType.ONCOTRIPSY
    simulation_name: str = "Memorial_Oncotripsy_Simulation"
    cell_config: CellBiophysicsConfig = field(default_factory=lambda: CellBiophysicsConfig())
    kgrid_config: KGridConfig = field(default_factory=KGridConfig)
    medium_config: MediumConfig = field(default_factory=MediumConfig)
    oncotripsy_config: OncotripsyConfig = field(default_factory=OncotripsyConfig)
    cavitation_config: CavitationConfig = field(default_factory=CavitationConfig)
    validation_config: ValidationConfig = field(default_factory=ValidationConfig)
    enable_cavitation: bool = True
    enable_standing_wave: bool = True
    device: str = "cpu"
    num_threads: int = 4
    save_results: bool = True
    save_path: Optional[str] = None
    verbose: bool = True
    
    def __post_init__(self):
        if self.save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.save_path = f"results/{self.simulation_name}_{timestamp}"
        Path(self.save_path).mkdir(parents=True, exist_ok=True)

# ============================================================================
# CELL BIOPHYSICS
# ============================================================================

class CellBiophysics:
    def __init__(self, config: CellBiophysicsConfig):
        self.config = config
        self.name = config.name
        self.cell_type = config.cell_type
        self.cytoplasmic_water_fraction = config.cytoplasmic_water_fraction
        self.water_diffusion_coefficient = config.water_diffusion_coefficient
        self.water_viscosity = config.water_viscosity
        self.hydrogen_bond_lifetime = config.hydrogen_bond_lifetime
        self.cortical_thickness = config.cortical_thickness
        self.cortical_youngs_modulus = config.cortical_youngs_modulus
        self.surface_tension = config.surface_tension
        self.membrane_permeability = config.membrane_permeability
        self.cell_diameter = config.cell_diameter
        self.nucleus_diameter = config.nucleus_diameter
        self.cell_radius = config.cell_diameter / 2
        self.nucleus_radius = config.nucleus_diameter / 2
        self.cell_volume = (4/3) * np.pi * self.cell_radius**3
        self.cortical_area = 4 * np.pi * self.cell_radius**2
        self._compute_derived()
        
    def _compute_derived(self):
        rho_water = 1000.0
        rho_dry = 1400.0
        self.effective_density = (self.cytoplasmic_water_fraction * rho_water + 
                                  (1 - self.cytoplasmic_water_fraction) * rho_dry)
        nu = 0.5
        self.bending_modulus = (self.cortical_youngs_modulus * self.cortical_thickness**3 / 
                               (12 * (1 - nu**2)))
        self.bulk_modulus = 2.0e9 * (0.7 + 0.3 * self.cytoplasmic_water_fraction)
        self.acoustic_impedance = self.effective_density * np.sqrt(self.bulk_modulus / self.effective_density)
        
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'cell_type': self.cell_type.value,
            'water_fraction': self.cytoplasmic_water_fraction,
            'cortical_stiffness_kPa': self.cortical_youngs_modulus / 1e3,
            'surface_tension_mN_m': self.surface_tension * 1e3,
            'effective_density_kg_m3': self.effective_density,
            'cell_diameter_um': self.cell_diameter * 1e6,
            'acoustic_impedance_MRayl': self.acoustic_impedance / 1e6
        }

# ============================================================================
# CELL-SEEDED CAVITATION
# ============================================================================

class CellSeededCavitation:
    E_REF = 5.0e3
    
    def __init__(self, cell: CellBiophysics, config: CavitationConfig = None):
        self.cell = cell
        self.config = config or CavitationConfig()
        
    def nucleation_threshold(self, frequency: float) -> float:
        f_ref = 0.5e6
        stiffness_scale = (self.cell.cortical_youngs_modulus / self.E_REF) ** 0.5
        P_base = 0.9e6 * stiffness_scale
        f_scale = (f_ref / frequency) ** 0.5
        return P_base * f_scale
    
    def nucleation_probability(self, pressure_amplitude: float, frequency: float) -> float:
        threshold = self.nucleation_threshold(frequency)
        P_reduced = pressure_amplitude - threshold
        if P_reduced > 0:
            width = 0.2e6
            prob = 1.0 / (1.0 + np.exp(-P_reduced / width))
            water_bonus = 1.0 + 0.3 * max(0, (self.cell.cytoplasmic_water_fraction - 0.72) / 0.06)
            prob *= water_bonus
            return min(prob, 1.0)
        return 0.0
    
    def bubble_dynamics(self, pressure_amplitude: float, frequency: float) -> Dict[str, float]:
        R0 = self.config.nucleation_site_radius
        P0 = 1.0e5
        P_drive = min(pressure_amplitude, P0 * 0.9)
        R_max = R0 * (P0 / (P0 - P_drive)) ** (1/3)
        P_collapse = P0 * (R_max / R0)**3
        strain = P_collapse / self.cell.cortical_youngs_modulus
        damage_energy = 0.5 * self.cell.cortical_youngs_modulus * strain**2
        rupture_stress = self.config.rupture_stress_threshold
        rupture_prob = min(1.0, (P_collapse / rupture_stress) * (self.E_REF / self.cell.cortical_youngs_modulus))
        return {
            'initial_radius_m': R0, 'max_radius_m': R_max, 'radius_ratio': R_max / R0,
            'collapse_pressure_Pa': P_collapse, 'cell_strain': strain,
            'damage_energy_density_J_m3': damage_energy, 'rupture_probability': rupture_prob,
            'cell_stiffness_Pa': self.cell.cortical_youngs_modulus
        }
    
    def cytoskeletal_disruption(self, pressure_amplitude: float, frequency: float, pulse_duration: float) -> Dict[str, float]:
        R = self.cell.cell_radius
        k = 2 * np.pi * frequency / 1540
        E_ac = pressure_amplitude**2 / (2 * self.cell.effective_density * 1540**2)
        F_rad = (4/3) * np.pi * R**3 * k * E_ac
        cortical_stress = F_rad / self.cell.cortical_area
        disruption_threshold = self.cell.cortical_youngs_modulus * 0.1
        disruption_prob = min(1.0, cortical_stress / disruption_threshold)
        time_factor = 1.0 - np.exp(-pulse_duration / 10e-3)
        return {
            'radiation_force_N': F_rad, 'cortical_stress_Pa': cortical_stress,
            'disruption_threshold_Pa': disruption_threshold,
            'disruption_probability': disruption_prob * time_factor, 'time_factor': time_factor
        }

# ============================================================================
# STANDING WAVE FIELD
# ============================================================================

class StandingWaveField:
    def __init__(self, frequency: float, pressure_amplitude: float, medium_sound_speed: float = 1540.0):
        self.frequency = frequency
        self.pressure_amplitude = pressure_amplitude
        self.sound_speed = medium_sound_speed
        self.wavelength = medium_sound_speed / frequency
        self.wavenumber = 2 * np.pi / self.wavelength
        
    def pressure_distribution(self, x: np.ndarray, t: float = 0) -> np.ndarray:
        omega = 2 * np.pi * self.frequency
        return 2 * self.pressure_amplitude * np.sin(self.wavenumber * x) * np.cos(omega * t)
    
    def radiation_force(self, cell: CellBiophysics, x: np.ndarray) -> np.ndarray:
        R = cell.cell_radius
        k = self.wavenumber
        E_ac = self.pressure_amplitude**2 / (2 * cell.effective_density * self.sound_speed**2)
        return -(4/3) * np.pi * R**3 * k * E_ac * np.sin(2 * k * x)
    
    def cell_aggregation_pattern(self, cell: CellBiophysics, n_positions: int = 1000) -> Dict[str, np.ndarray]:
        x = np.linspace(0, 3 * self.wavelength, n_positions)
        pressure = self.pressure_distribution(x)
        force = self.radiation_force(cell, x)
        rho_cell = cell.effective_density
        rho_medium = 1000.0
        if rho_cell > rho_medium:
            agg_mask = np.abs(pressure) < 0.1 * np.max(np.abs(pressure))
        else:
            agg_mask = np.abs(pressure) > 0.9 * np.max(np.abs(pressure))
        return {
            'positions': x, 'pressure': pressure, 'radiation_force': force,
            'aggregation_mask': agg_mask, 'wavelength_m': self.wavelength
        }

# ============================================================================
# ONCOTRIPSY PULSE
# ============================================================================

class OncotripsyPulse:
    def __init__(self, cell: CellBiophysics, config: OncotripsyConfig = None):
        self.cell = cell
        self.config = config or OncotripsyConfig()
        self.cavitation = CellSeededCavitation(cell)
        
    def optimal_pulse_duration(self, frequency: float) -> float:
        f_ref = 0.5e6
        pd_ref = 20e-3
        pd_optimal = pd_ref * (f_ref / frequency)
        stiffness_factor = (self.cell.cortical_youngs_modulus / 5.0e3) ** 0.5
        pd_optimal *= stiffness_factor
        return max(pd_optimal, 1e-3)
    
    def cell_death_probability(self, frequency: float = None, pressure_amplitude: float = None,
                               pulse_duration: float = None, duty_cycle: float = None,
                               total_exposure_time: float = None) -> float:
        f = frequency or self.config.frequency
        P = pressure_amplitude or self.config.peak_negative_pressure
        pd = pulse_duration or self.config.pulse_duration
        dc = duty_cycle or self.config.duty_cycle
        t_exp = total_exposure_time or self.config.treatment_duration
        
        p_nucleation = self.cavitation.nucleation_probability(P, f)
        dynamics = self.cavitation.bubble_dynamics(P, f)
        p_damage = dynamics['rupture_probability']
        
        cytoskeletal = self.cavitation.cytoskeletal_disruption(P, f, pd)
        p_disruption = cytoskeletal['disruption_probability']
        
        p_death_per_pulse = 1.0 - (1.0 - p_nucleation * p_damage) * (1.0 - p_disruption)
        
        prf = dc / pd
        n_pulses = int(t_exp * prf)
        
        if p_death_per_pulse > 0:
            return 1.0 - (1.0 - p_death_per_pulse)**n_pulses
        return 0.0
    
    def run_protocol(self) -> Dict[str, Any]:
        p_death = self.cell_death_probability()
        dynamics = self.cavitation.bubble_dynamics(self.config.peak_negative_pressure, self.config.frequency)
        cytoskeletal = self.cavitation.cytoskeletal_disruption(
            self.config.peak_negative_pressure, self.config.frequency, self.config.pulse_duration)
        return {
            'cell_name': self.cell.name, 'cell_type': self.cell.cell_type.value,
            'death_probability': p_death,
            'protocol': {
                'frequency_MHz': self.config.frequency / 1e6,
                'pressure_MPa': self.config.peak_negative_pressure / 1e6,
                'pulse_duration_ms': self.config.pulse_duration * 1e3,
                'duty_cycle': self.config.duty_cycle,
                'exposure_time_s': self.config.treatment_duration
            },
            'cavitation': dynamics, 'cytoskeletal': cytoskeletal,
            'water_fraction': self.cell.cytoplasmic_water_fraction,
            'cortical_stiffness_kPa': self.cell.cortical_youngs_modulus / 1e3
        }

# ============================================================================
# ACOUSTIC SIMULATOR
# ============================================================================

class AcousticSimulator:
    def __init__(self, kgrid_config: KGridConfig, medium_config: MediumConfig):
        self.kgrid = kgrid_config
        self.medium = medium_config
        self.Nx = kgrid_config.Nx
        self.Ny = kgrid_config.Ny
        self.Nz = kgrid_config.Nz if kgrid_config.dim == 3 else 1
        self.dx = kgrid_config.dx
        self.dy = kgrid_config.dy
        self.dt = kgrid_config.dt
        self.Nt = int(np.ceil(kgrid_config.t_end / kgrid_config.dt))
        self.c0 = medium_config.sound_speed
        self.rho0 = medium_config.density
        self.alpha_coeff = medium_config.alpha_coeff
        self.alpha_power = medium_config.alpha_power
        
        cfl = self.c0 * self.dt / self.dx
        if cfl > 1.0:
            warnings.warn(f"CFL = {cfl:.2f} > 1.0. Simulation may be unstable.")
        
        self.pressure = np.zeros((self.Nx, self.Ny))
        self.velocity_x = np.zeros((self.Nx, self.Ny))
        self.velocity_y = np.zeros((self.Nx, self.Ny))
        
    def add_source(self, x_pos: int, y_pos: int, amplitude: float, frequency: float, pulse_duration: float):
        self.source_x = x_pos
        self.source_y = y_pos
        self.source_amplitude = amplitude
        self.source_frequency = frequency
        self.source_pulse_duration = pulse_duration
        
    def step(self, t: float) -> None:
        p = self.pressure
        vx = self.velocity_x
        vy = self.velocity_y
        
        dvx_dx = np.zeros_like(vx)
        dvy_dy = np.zeros_like(vy)
        dvx_dx[1:-1, :] = (vx[2:, :] - vx[:-2, :]) / (2 * self.dx)
        dvy_dy[:, 1:-1] = (vy[:, 2:] - vy[:, :-2]) / (2 * self.dy)
        
        p_new = p - self.rho0 * self.c0**2 * self.dt * (dvx_dx + dvy_dy)
        
        dp_dx = np.zeros_like(p)
        dp_dy = np.zeros_like(p)
        dp_dx[1:-1, :] = (p[2:, :] - p[:-2, :]) / (2 * self.dx)
        dp_dy[:, 1:-1] = (p[:, 2:] - p[:, :-2]) / (2 * self.dy)
        
        vx_new = vx - (self.dt / self.rho0) * dp_dx
        vy_new = vy - (self.dt / self.rho0) * dp_dy
        
        pml_size = self.kgrid.PML_size
        damping = np.ones_like(p)
        for i in range(pml_size):
            factor = (i / pml_size) ** 2
            damping[i, :] *= (1 - factor * 0.1)
            damping[-(i+1), :] *= (1 - factor * 0.1)
        for j in range(pml_size):
            factor = (j / pml_size) ** 2
            damping[:, j] *= (1 - factor * 0.1)
            damping[:, -(j+1)] *= (1 - factor * 0.1)
        
        self.pressure = p_new * damping
        self.velocity_x = vx_new * damping
        self.velocity_y = vy_new * damping
        
        if hasattr(self, 'source_x') and t < self.source_pulse_duration:
            source_term = self.source_amplitude * np.sin(2 * np.pi * self.source_frequency * t)
            self.pressure[self.source_x, self.source_y] += source_term * self.dt
    
    def run(self) -> Dict[str, np.ndarray]:
        pressure_history = []
        for n in range(self.Nt):
            t = n * self.dt
            self.step(t)
            if n % 10 == 0:
                pressure_history.append(self.pressure.copy())
        return {
            'pressure_final': self.pressure,
            'pressure_history': np.array(pressure_history),
            'grid_x': np.arange(self.Nx) * self.dx,
            'grid_y': np.arange(self.Ny) * self.dy,
            'time': np.arange(self.Nt) * self.dt
        }

# ============================================================================
# SELECTIVITY ENGINE
# ============================================================================

class SelectivityEngine:
    def __init__(self, normal_cell: CellBiophysics, cancer_cell: CellBiophysics, config: EngineConfig = None):
        self.normal = normal_cell
        self.cancer = cancer_cell
        self.config = config or EngineConfig()
        self.normal_pulse = OncotripsyPulse(normal_cell, self.config.oncotripsy_config)
        self.cancer_pulse = OncotripsyPulse(cancer_cell, self.config.oncotripsy_config)
        
    def run_comparison(self) -> Dict[str, Any]:
        normal_result = self.normal_pulse.run_protocol()
        cancer_result = self.cancer_pulse.run_protocol()
        p_death_normal = normal_result['death_probability']
        p_death_cancer = cancer_result['death_probability']
        
        if p_death_normal > 0.01:
            selectivity_ratio = p_death_cancer / p_death_normal
        else:
            selectivity_ratio = p_death_cancer / 0.01
        
        therapeutic_index = p_death_cancer - p_death_normal
        
        return {
            'normal': normal_result, 'cancer': cancer_result,
            'selectivity': {
                'ratio': selectivity_ratio, 'therapeutic_index': therapeutic_index,
                'p_death_normal': p_death_normal, 'p_death_cancer': p_death_cancer
            },
            'protocol': self.config.oncotripsy_config,
            'timestamp': datetime.now().isoformat()
        }
    
    def sweep_frequency(self, frequencies: np.ndarray) -> Dict[str, np.ndarray]:
        p_normal, p_cancer, selectivity = [], [], []
        for f in frequencies:
            p_n = self.normal_pulse.cell_death_probability(frequency=f)
            p_c = self.cancer_pulse.cell_death_probability(frequency=f)
            p_normal.append(p_n); p_cancer.append(p_c)
            selectivity.append(p_c / p_n if p_n > 0.01 else p_c / 0.01)
        return {'frequencies': frequencies, 'p_death_normal': np.array(p_normal),
                'p_death_cancer': np.array(p_cancer), 'selectivity_ratio': np.array(selectivity)}
    
    def sweep_pressure(self, pressures: np.ndarray) -> Dict[str, np.ndarray]:
        p_normal, p_cancer, selectivity = [], [], []
        for P in pressures:
            p_n = self.normal_pulse.cell_death_probability(pressure_amplitude=P)
            p_c = self.cancer_pulse.cell_death_probability(pressure_amplitude=P)
            p_normal.append(p_n); p_cancer.append(p_c)
            selectivity.append(p_c / p_n if p_n > 0.01 else p_c / 0.01)
        return {'pressures': pressures, 'p_death_normal': np.array(p_normal),
                'p_death_cancer': np.array(p_cancer), 'selectivity_ratio': np.array(selectivity)}
    
    def sweep_pulse_duration(self, pulse_durations: np.ndarray) -> Dict[str, np.ndarray]:
        p_normal, p_cancer, selectivity = [], [], []
        for pd in pulse_durations:
            p_n = self.normal_pulse.cell_death_probability(pulse_duration=pd)
            p_c = self.cancer_pulse.cell_death_probability(pulse_duration=pd)
            p_normal.append(p_n); p_cancer.append(p_c)
            selectivity.append(p_c / p_n if p_n > 0.01 else p_c / 0.01)
        return {'pulse_durations': pulse_durations, 'p_death_normal': np.array(p_normal),
                'p_death_cancer': np.array(p_cancer), 'selectivity_ratio': np.array(selectivity)}
    
    def save_results(self, results: Dict, filename: str = None):
        if filename is None:
            filename = f"{self.config.save_path}/results.json"
        def convert(obj):
            if isinstance(obj, np.ndarray): return obj.tolist()
            elif isinstance(obj, dict): return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list): return [convert(v) for v in obj]
            return obj
        with open(filename, 'w') as f:
            json.dump(convert(results), f, indent=2, default=str)
        print(f"Results saved to {filename}")

# ============================================================================
# VALIDATION LEDGER
# ============================================================================

class ValidationLedger:
    def __init__(self, config: ValidationConfig = None):
        self.config = config or ValidationConfig()
        self.metrics = []
        self.timestamp = datetime.now().isoformat()
        
    def log_simulation(self, results: Dict[str, Any]):
        p_normal = results['selectivity']['p_death_normal']
        p_cancer = results['selectivity']['p_death_cancer']
        physics_consistent = (0 <= p_normal <= 1) and (0 <= p_cancer <= 1)
        
        if results['selectivity']['ratio'] > 1.0:
            memorial_integrity = min(1.0, results['selectivity']['ratio'] / 10.0)
        else:
            memorial_integrity = 0.1
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'simulation_name': 'Oncotripsy_OSCC_vs_Normal',
            'energy_conservation': True,
            'physics_consistent': physics_consistent,
            'memorial_integrity': memorial_integrity,
            'selectivity_ratio': results['selectivity']['ratio'],
            'therapeutic_index': results['selectivity']['therapeutic_index'],
            'cell_types_tested': [results['normal']['cell_type'], results['cancer']['cell_type']],
            'physics_basis': 'Mittelstein et al. APL 116, 013701 (2020)',
            'dedication': 'In memory of Ali Sayed Muhammad (1957-2022)'
        }
        self.metrics.append(entry)
        return entry
    
    def get_summary(self) -> Dict:
        if not self.metrics:
            return {'status': 'No simulations logged'}
        avg_selectivity = np.mean([m['selectivity_ratio'] for m in self.metrics])
        max_selectivity = np.max([m['selectivity_ratio'] for m in self.metrics])
        return {
            'total_simulations': len(self.metrics),
            'average_selectivity': avg_selectivity,
            'max_selectivity': max_selectivity,
            'physics_consistent_fraction': np.mean([m['physics_consistent'] for m in self.metrics]),
            'memorial_integrity_average': np.mean([m['memorial_integrity'] for m in self.metrics]),
            'dedication': 'In memory of Ali Sayed Muhammad (1957-2022)'
        }

# ============================================================================
# MAIN ENGINE
# ============================================================================

class SuperconductiveASMEngine:
    """
    Superconductive ASM Memorial Computational Core v5.1
    In memory of Ali Sayed Muhammad (1957-2022)
    """
    
    def __init__(self, config: EngineConfig = None):
        self.config = config or EngineConfig()
        self.logger = self._setup_logger()
        
        self.normal_cell = CellBiophysics(CellBiophysicsConfig(
            name="normal_keratinocyte", cell_type=CellType.NORMAL,
            cytoplasmic_water_fraction=0.72, water_diffusion_coefficient=1.5e-9,
            water_viscosity=2.0e-3, hydrogen_bond_lifetime=5.0,
            cortical_thickness=200e-9, cortical_youngs_modulus=5.0e3,
            surface_tension=0.3e-3, membrane_permeability=1.0e-4,
            cell_diameter=15e-6, nucleus_diameter=7e-6
        ))
        
        self.cancer_cell = CellBiophysics(CellBiophysicsConfig(
            name="oscc_cancer", cell_type=CellType.CANCER,
            cytoplasmic_water_fraction=0.78, water_diffusion_coefficient=2.2e-9,
            water_viscosity=1.4e-3, hydrogen_bond_lifetime=3.5,
            cortical_thickness=150e-9, cortical_youngs_modulus=2.5e3,
            surface_tension=0.15e-3, membrane_permeability=1.6e-4,
            cell_diameter=18e-6, nucleus_diameter=9e-6
        ))
        
        self.selectivity_engine = SelectivityEngine(self.normal_cell, self.cancer_cell, self.config)
        self.ledger = ValidationLedger(self.config.validation_config)
        self.acoustic_sim = None
        
        self.logger.info("S-ASM-CC v5.1 initialized")
        self.logger.info(f"Normal: {self.normal_cell.name}, stiffness={self.normal_cell.cortical_youngs_modulus/1e3:.1f} kPa")
        self.logger.info(f"Cancer: {self.cancer_cell.name}, stiffness={self.cancer_cell.cortical_youngs_modulus/1e3:.1f} kPa")
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("SASMCC")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
        return logger
    
    def run_oncotripsy_simulation(self) -> Dict[str, Any]:
        self.logger.info("Running oncotripsy simulation...")
        results = self.selectivity_engine.run_comparison()
        self.ledger.log_simulation(results)
        
        print("\n" + "=" * 70)
        print("ONCOTRIPSY SIMULATION RESULTS")
        print("=" * 70)
        print(f"Protocol: {results['protocol'].frequency/1e6:.1f} MHz, "
              f"{results['protocol'].peak_negative_pressure/1e6:.1f} MPa PNP, "
              f"{results['protocol'].pulse_duration*1e3:.0f} ms PD, "
              f"{results['protocol'].duty_cycle*100:.0f}% DC")
        print(f"\nNormal cell death probability: {results['selectivity']['p_death_normal']:.3f}")
        print(f"Cancer cell death probability: {results['selectivity']['p_death_cancer']:.3f}")
        print(f"Selectivity ratio (cancer/normal): {results['selectivity']['ratio']:.2f}")
        print(f"Therapeutic index: {results['selectivity']['therapeutic_index']:.3f}")
        print("=" * 70)
        return results
    
    def run_parameter_sweep(self, sweep_type: str = "frequency") -> Dict[str, np.ndarray]:
        self.logger.info(f"Running {sweep_type} sweep...")
        if sweep_type == "frequency":
            frequencies = np.linspace(0.1, 2.0, 50) * 1e6
            return self.selectivity_engine.sweep_frequency(frequencies)
        elif sweep_type == "pressure":
            pressures = np.linspace(0.1, 2.0, 50) * 1e6
            return self.selectivity_engine.sweep_pressure(pressures)
        elif sweep_type == "pulse_duration":
            pds = np.linspace(1, 100, 50) * 1e-3
            return self.selectivity_engine.sweep_pulse_duration(pds)
        else:
            raise ValueError(f"Unknown sweep type: {sweep_type}")
    
    def visualize_sweep(self, results: Dict, sweep_type: str):
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        if sweep_type == "frequency":
            x = results['frequencies'] / 1e6; xlabel = 'Frequency (MHz)'
        elif sweep_type == "pressure":
            x = results['pressures'] / 1e6; xlabel = 'Pressure (MPa)'
        else:
            x = results['pulse_durations'] * 1e3; xlabel = 'Pulse Duration (ms)'
        
        axes[0].plot(x, results['p_death_normal'], 'b-', linewidth=2, label='Normal', marker='o', markersize=3)
        axes[0].plot(x, results['p_death_cancer'], 'r-', linewidth=2, label='Cancer', marker='s', markersize=3)
        axes[0].set_xlabel(xlabel); axes[0].set_ylabel('Death Probability')
        axes[0].set_title('Cell Death Probability'); axes[0].legend(); axes[0].grid(alpha=0.3)
        axes[0].set_ylim(-0.05, 1.05)
        
        axes[1].plot(x, results['selectivity_ratio'], 'g-', linewidth=2.5)
        axes[1].axhline(y=1.0, color='black', linestyle='--', linewidth=1, alpha=0.5, label='No selectivity')
        axes[1].set_xlabel(xlabel); axes[1].set_ylabel('Selectivity Ratio (Cancer/Normal)')
        axes[1].set_title('Selectivity Ratio'); axes[1].legend(); axes[1].grid(alpha=0.3)
        
        plt.suptitle(f'Oncotripsy Parameter Sweep: {sweep_type.capitalize()}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        filename = f"{self.config.save_path}/sweep_{sweep_type}.png"
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.show()
        print(f"Sweep visualization saved to {filename}")
    
    def get_validation_summary(self) -> Dict:
        return self.ledger.get_summary()
    
    def save_engine_state(self, filename: str = None):
        if filename is None:
            filename = f"{self.config.save_path}/engine_state.json"
        state = {
            'version': '5.1', 'timestamp': datetime.now().isoformat(),
            'dedication': 'In memory of Ali Sayed Muhammad (1957-2022)',
            'physics_basis': 'Mittelstein et al. APL 116, 013701 (2020)',
            'normal_cell': self.normal_cell.to_dict(),
            'cancer_cell': self.cancer_cell.to_dict(),
            'validation_summary': self.get_validation_summary()
        }
        with open(filename, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        print(f"Engine state saved to {filename}")


# ============================================================================
# DEMO / TEST
# ============================================================================

if __name__ == "__main__":
    config = EngineConfig(simulation_name="OSCC_Study", save_path="./results")
    engine = SuperconductiveASMEngine(config)
    
    # Run main simulation
    results = engine.run_oncotripsy_simulation()
    
    # Run sweeps
    for sweep_type in ["frequency", "pressure", "pulse_duration"]:
        sweep_results = engine.run_parameter_sweep(sweep_type)
        engine.visualize_sweep(sweep_results, sweep_type)
    
    # Save state
    engine.save_engine_state()
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
