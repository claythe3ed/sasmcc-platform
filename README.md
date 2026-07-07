![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Version](https://img.shields.io/badge/version-5.3-blue)
![CI](https://github.com/claythe3ed/sasmcc-platform/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue.svg)
![Hardware](https://img.shields.io/badge/Hardware-208%20Parts-brightgreen)
![Electrical](https://img.shields.io/badge/Electrical-164%20Connections-orange)
![Cost](https://img.shields.io/badge/Cost-10.2k--16.2k%20USD-blue)
![Simulation](https://img.shields.io/badge/Simulation-9%2F9%20PASS-success)
![GitHub stars](https://img.shields.io/github/stars/claythe3ed/sasmcc-platform?style=social)
# S-ASM-CC Platform
### Treatment Engine and Hardware Blueprint

*Dedicated to Ali Sayed Muhammad Osman (1957-2022). Every equation. Every simulation. Every result.*

---

## What This Is

Treatment simulation engine and complete preclinical hardware blueprint for the S-ASM-CC Physics Engine (https://github.com/claythe3ed/sasmcc-physics-engine).

Contains S-ASM-CC v5.3 canonical treatment simulation (nine cancer types, all passing), pan-cancer biophysical database from primary AFM literature and ADC‑derived water fraction values, nine hardware parameter JSON files, complete preclinical platform blueprint (208 parts, 164 electrical connections, 231 mechanical connections), and three automated consistency hooks.

---

## Quick Start

    pip install numpy scipy matplotlib
    cd src && python3 sasmcc_v53.py
    cd ../hooks
    python3 check_blueprint_vs_database.py
    python3 check_engine_consistency.py
    python3 check_knowledge_graph_sync.py

Expected: all nine cancer types PASS, threshold agreement 0.00%, all hooks exit 0.

---

## Cancer Type Schedule (All 9 Types Now Complete with f_water)

| Type | Frequency | Pa_opt | f_water | Selectivity | Status |
|------|-----------|--------|---------|-------------|--------|
| OSCC | 450 kHz | 0.644 MPa | 0.780 | 73.9x | VALIDATED |
| Breast IDC | 2000 kHz | 0.643 MPa | 0.732 | 965.5x | STIFFNESS_VALIDATED |
| Prostate | 886 kHz | 0.708 MPa | 0.742 | 1352.3x | STIFFNESS_VALIDATED |
| Lung NSCLC | 1182 kHz | 0.570 MPa | 0.812 | 55.5x | STIFFNESS_VALIDATED |
| Colorectal | 1013 kHz | 0.615 MPa | 0.728 | 269.5x | STIFFNESS_VALIDATED |
| Pancreatic | 709 kHz | 0.744 MPa | 0.728 | 310.8x | STIFFNESS_VALIDATED |
| Glioblastoma | 1773 kHz | 0.520 MPa | 0.752 | 26.1x | STIFFNESS_VALIDATED* |
| Cervical | 1182 kHz | 0.607 MPa | 0.729 | 95.7x | STIFFNESS_VALIDATED |
| Liver HCC | 788 kHz | 0.650 MPa | 0.787 | 190.4x | STIFFNESS_VALIDATED |

*GBM stiffer than normal brain. Stiffness opposes selectivity; water fraction carries selectivity alone.

f_water values derived from ADC literature for 8 types (plus OSCC validated). All 9 types now have complete biophysical parameters. QENS validation pending via Martins/Bordallo collaboration (University of Copenhagen).

---

## Hardware Platform (Design Only)

- Controller: Zynq UltraScale+ MPSoC, FPGA pulse timing <1 us jitter
- RF chain: DDS/DAC -> dual redundant E&I 1040L amps -> 2x8 relay matrix -> 8 PZT transducers
- Turret: Motorized indexed rotary, kinematic mounts, <10 um repeatability
- Safety: Pilz PNOZ Category 3, 7 independent hardwired interlocks
- Phase 0: Benchtop cell culture chamber, 37C, fused quartz acoustic window
- Phase 1: 9 tissue phantoms + small-animal stage, anesthesia, B-mode co-registration
- Cost: $10,200-$16,200 vs $200,000-$500,000 commercial

Full blueprint: hardware/blueprint_v2/

---

## Validation Hooks

| Hook | Result |
|------|--------|
| check_blueprint_vs_database.py | PASS |
| check_engine_consistency.py | 9/9 PASS |
| check_knowledge_graph_sync.py | PASS |

All three pass as of v5.3, knowledge graph v17, 2026-06-23.

---

## References

- Mittelstein et al. (2020). APL 116, 013701. doi:10.1063/1.5128627
- Cross et al. (2007). Nature Nanotechnology 2, 780.
- Ciesluk et al. (2020). Int J Nanomedicine. PMC7547774
- Marques et al. (2022). Cancers 14, 5053. PMC9600571
- PMC4678138 cervical cancer AFM
- Diagnostics 2022. DOI: 10.3390/diagnostics12020332 (Breast IDC f_water)
- OncoTargets 2022. DOI: 10.2147/OTT.S366723 (Prostate f_water)
- Cancers 2020. DOI: 10.3390/cancers12061493 (Lung NSCLC f_water)
- Insights Imaging 2022. DOI: 10.1007/s13244-022-01268-7 (Pancreatic f_water)
- Insights Imaging 2019. DOI: 10.1186/s13244-019-0719-6 (Glioblastoma f_water)
- PLOS ONE 2023. DOI: 10.1371/journal.pone.0285786 (Cervical f_water)
- PLOS ONE 2016. DOI: 10.1371/journal.pone.0153944 (Colorectal f_water)
- Meta-analysis (HCC f_water)

---

## Collaboration

- QENS water fraction data: Martins/Bordallo group, University of Copenhagen
- Preclinical validation: Mittelstein/Shapiro/Gharib group, Caltech
- Institutional: KAIMRC, QBRI, King Hussein Cancer Center

---

## License

MIT. See LICENSE.

*Dedicated to Ali Sayed Muhammad Osman (1957-2022).*