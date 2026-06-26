"""
calibrate.py - RF Amplifier Calibration Analysis
Reads a CSV file with columns: pwm(%), voltage_mV
Assumes hydrophone sensitivity: 50 nV/Pa (adjust for your Onda model).
Computes polynomial fit and exports coefficients for firmware.
"""
import numpy as np
import matplotlib.pyplot as plt
import sys

# Hydrophone sensitivity (V/Pa) - check your calibration sheet!
SENSITIVITY = 50e-9  # 50 nV/Pa → 50e-9 V/Pa

def load_data(filename):
    data = np.loadtxt(filename, delimiter=',', skiprows=1)
    pwm = data[:,0]
    voltage_mV = data[:,1]  # mV
    voltage_V = voltage_mV / 1000.0
    pressure_Pa = voltage_V / SENSITIVITY
    pressure_MPa = pressure_Pa / 1e6
    return pwm, pressure_MPa

def fit_polynomial(pwm, pressure, degree=2):
    coeffs = np.polyfit(pwm, pressure, degree)
    return coeffs

def plot_fit(pwm, pressure, coeffs):
    pwm_fine = np.linspace(0, 100, 100)
    pressure_fit = np.polyval(coeffs, pwm_fine)
    plt.plot(pwm, pressure, 'o', label='Data')
    plt.plot(pwm_fine, pressure_fit, '-', label=f'Poly fit degree {len(coeffs)-1}')
    plt.xlabel('PWM Duty Cycle (%)')
    plt.ylabel('Pressure (MPa)')
    plt.grid(True)
    plt.legend()
    plt.title('Amplifier Calibration: Pressure vs PWM')
    plt.savefig('calibration_curve.png')
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python calibrate.py <calibration_data.csv>")
        sys.exit(1)
    filename = sys.argv[1]
    pwm, pressure = load_data(filename)
    coeffs = fit_polynomial(pwm, pressure, degree=2)
    print("Polynomial coefficients (highest power first):")
    print(coeffs)
    # Inverse function: for a desired pressure, estimate PWM
    # We can solve numerically or use polyval with np.roots
    # Example: to achieve 0.64 MPa
    target = 0.64
    # Solve poly - target = 0
    poly_to_solve = np.poly1d(coeffs) - target
    roots = poly_to_solve.r
    # Real root between 0 and 100
    real_roots = roots[np.isreal(roots)].real
    pwm_target = real_roots[(real_roots >= 0) & (real_roots <= 100)]
    if len(pwm_target) > 0:
        print(f"To achieve {target} MPa, set PWM to {pwm_target[0]:.1f}%")
    plot_fit(pwm, pressure, coeffs)
