# Calibration Procedure: RF Amplifier Gain to Hydrophone Pressure

## Objective
Determine the relationship between the RF amplifier control signal (PWM duty cycle or AWG amplitude) and the peak negative pressure (PNP) measured by the needle hydrophone at the focal point of the transducer. Use this calibration to set the target 0.64 MPa during treatment.

## Equipment Needed
- Oncotripsy therapy system (fully assembled RF chain)
- Needle hydrophone (Onda HGL‑0400) positioned at transducer focus
- Oscilloscope or hydrophone preamplifier with data acquisition
- MATLAB/Python for analysis
- Degassed water in the water bath

## Safety
- Wear safety glasses.
- Ensure emergency stop is functional.
- Start at **minimum gain** to avoid damaging the hydrophone.

## Step‑by‑Step Procedure

### 1. Position Hydrophone
- Use the 3‑axis scanning stage to place the needle hydrophone tip precisely at the transducer’s focal point.
- Confirm alignment using a pulse‑echo test (optional).

### 2. Set Fixed Parameters
- Set the AWG frequency to **0.45 MHz** (optimal from simulation).
- Set pulse duration to **100 cycles** (≈222 µs) to avoid cavitation interference during calibration.
- Use a very low PRF (e.g., 10 Hz) to prevent heating.

### 3. Increment Amplifier Gain
- Starting from **0% PWM duty cycle** (minimum gain), increase in steps of 5% or 10%.
- At each step, record:
  - PWM duty cycle (%)
  - Hydrophone peak negative voltage (mV) – read from oscilloscope or DAQ
  - Convert voltage to pressure using the hydrophone sensitivity (e.g., 50 nV/Pa → P = V / sensitivity).

### 4. Record Data
| PWM (%) | Hydrophone Voltage (mV) | Pressure (MPa) |
|---------|--------------------------|----------------|
| 0       | 0                        | 0              |
| 10      | …                        | …              |
| 20      | …                        | …              |
| …       | …                        | …              |
| 100     | …                        | …              |

### 5. Fit a Curve
- Plot pressure vs. PWM.
- Fit a polynomial (e.g., 2nd or 3rd order) or a piecewise linear function.
- Example: `P = a*PWM² + b*PWM + c`.

### 6. Store Calibration Data
- Save the coefficients or a lookup table in the firmware.
- In the `set_pressure_target()` function, use the inverse relationship to compute the required PWM for the desired 0.64 MPa.

## Firmware Integration
The function `set_pressure_target(pressure_pa)` shall:
1. Compute PWM = `inverse_poly(pressure_pa)`
2. Set the AXI Timer/PWM duty cycle accordingly.
3. Verify with a single test pulse and hydrophone reading before starting treatment.

## Validation
- After calibration, run a series of test pulses at the treatment pulse duration (463 ms) and confirm the pressure is within ±5% of 0.64 MPa.

## Python Analysis Script (calibrate.py)
See `firmware/calibrate.py` for an example script that loads raw calibration data and computes the polynomial fit.
