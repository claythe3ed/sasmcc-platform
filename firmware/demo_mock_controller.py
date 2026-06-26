"""
DEMO MOCK CONTROLLER – Oncotripsy Therapy System
Simulates the main controller state machine with mock hardware.
Uses real hardware_params.json from results/.
"""
import json
import time
import sys
import os

# ==================== MOCK HARDWARE CLASSES ====================
class AWG:
    def __init__(self, spi_bus=0):
        self.spi_bus = spi_bus
    def check(self):
        print("[AWG] Self-test OK")
        return True
    def set_frequency(self, freq):
        print(f"[AWG] Frequency set to {freq/1e6:.2f} MHz")
    def set_waveform(self, wf):
        print(f"[AWG] Waveform set to {wf}")
    def burst(self, freq, duration):
        print(f"[AWG] Burst: {freq/1e6:.2f} MHz, {duration*1e3:.1f} ms")

class RFAmplifier:
    def __init__(self, gpio_pin='PA0'):
        self.pin = gpio_pin
        self.enabled = False
    def check(self):
        print("[RF Amp] Self-test OK")
        return True
    def set_gain_from_pressure(self, pressure):
        print(f"[RF Amp] Gain set for target pressure {pressure/1e6:.2f} MPa")
    def enable(self):
        self.enabled = True
        print("[RF Amp] Enabled")
    def disable(self):
        self.enabled = False
        print("[RF Amp] Disabled")

class FastRFSwitch:
    def __init__(self, gpio_pin='PA1'):
        self.pin = gpio_pin
    def enable(self):
        print("[RF Switch] Enabled")
    def disable(self):
        print("[RF Switch] Disabled")

class ImpedanceMatching:
    def __init__(self, i2c_bus=1):
        self.bus = i2c_bus
    def tune_to_frequency(self, freq):
        print(f"[Matching] Tuned to {freq/1e6:.2f} MHz")

class SafetyRelay:
    def __init__(self, gpio_pin='PA2'):
        self.pin = gpio_pin
        self.ok = True
    def check_ok(self):
        print("[Safety] Relay check OK")
        return True
    def is_ok(self):
        # Simulate E-stop not pressed (can be changed to test safety)
        return self.ok
    def disable(self):
        print("[Safety] Relay disabled")

class StepperDriver:
    def home_all_axes(self):
        print("[Motion] Axes homed")
    def disable(self):
        print("[Motion] Disabled")
    def move_to_next_position(self):
        print("[Motion] Moving to next scan position")

class Hydrophone:
    def __init__(self, adc_channel=0):
        self.ch = adc_channel
    def read(self):
        print("[Hydrophone] Pressure reading logged")

class ThermocoupleAmplifier:
    def __init__(self, spi_bus=1):
        self.bus = spi_bus
    def set_limits(self, temp, tol):
        print(f"[Temp] Limits set: {temp}°C ±{tol}°C")
    def any_overlimit(self):
        # Simulate temperature OK
        return False

class Display:
    def __init__(self, lvds_port=0):
        self.port = lvds_port
        self.touch_count = 0
    def show(self, msg):
        print(f"[Display] {msg}")
    def show_error(self, msg):
        print(f"[Display ERROR] {msg}")
    def touch_pressed(self):
        # Simulate user touching the screen after first idle call
        self.touch_count += 1
        if self.touch_count == 1:  # first idle loop -> trigger load params
            return True
        # After setup, we need another touch to start treatment
        # This happens after the second transition to IDLE
        return False

class LEDController:
    def __init__(self, pwm_pin='PA3'):
        self.pin = pwm_pin

class Camera:
    def __init__(self, usb_port=0):
        self.port = usb_port


# ==================== CONTROLLER (identical logic, but uses mocks) ====================
class OncotripsyController:
    def __init__(self):
        self.awg = AWG()
        self.rf_amp = RFAmplifier()
        self.rf_switch = FastRFSwitch()
        self.matching = ImpedanceMatching()
        self.safety = SafetyRelay()
        self.motion = StepperDriver()
        self.hydrophone = Hydrophone()
        self.temp = ThermocoupleAmplifier()
        self.display = Display()
        self.led = LEDController()
        self.camera = Camera()

        self.state = 'INIT'
        self.params = {}
        self.treatment_running = False

    def run(self):
        while True:
            if self.state == 'INIT':
                self.init_system()
            elif self.state == 'IDLE':
                self.idle_loop()
            elif self.state == 'LOAD_PARAMS':
                self.load_params()
            elif self.state == 'SETUP':
                self.setup_treatment()
            elif self.state == 'TREATMENT':
                self.treatment_loop()
            elif self.state == 'SHUTDOWN':
                self.shutdown()
                break

    def init_system(self):
        self.display.show("Initializing...")
        if not self.safety.check_ok() or not self.awg.check() or not self.rf_amp.check():
            self.display.show_error("HW fault")
            self.state = 'SHUTDOWN'
            return
        self.display.show("Ready")
        self.state = 'IDLE'

    def idle_loop(self):
        if self.display.touch_pressed():
            # Determine next state: if we just came from INIT, load params;
            # if we came from SETUP, start treatment.
            if self.state == 'IDLE' and not self.treatment_running and self.params == {}:
                self.state = 'LOAD_PARAMS'
            elif self.state == 'IDLE' and not self.treatment_running and self.params != {}:
                self.treatment_running = True
                self.start_time = time.time()
                self.display.show("Treatment active...")
                self.state = 'TREATMENT'
        time.sleep(0.05)  # shorter for demo

    def load_params(self):
        # Read the actual hardware_params.json generated earlier
        json_path = os.path.join(os.path.dirname(__file__), '..', 'results', 'hardware_params.json')
        if not os.path.exists(json_path):
            # fallback if run from different cwd
            json_path = 'results/hardware_params.json'
        with open(json_path, 'r') as f:
            self.params = json.load(f)
        opt = self.params['optimal_parameters']
        self.frequency = opt['frequency_Hz']
        self.pressure_target = opt['peak_negative_pressure_Pa']
        self.pulse_duration = opt['pulse_duration_s']
        self.duty_cycle = opt['duty_cycle']
        # For demo, shorten total time to 5 seconds
        self.total_time = 5.0  # instead of 60 s
        self.display.show(f"Loaded: {self.frequency/1e6:.2f} MHz, {self.pressure_target/1e6:.2f} MPa")
        print(f"[Controller] Treatment will run for {self.total_time} seconds (demo)")
        self.state = 'SETUP'

    def setup_treatment(self):
        self.awg.set_frequency(self.frequency)
        self.awg.set_waveform('sine')
        self.rf_switch.enable()
        self.rf_amp.set_gain_from_pressure(self.pressure_target)
        self.matching.tune_to_frequency(self.frequency)
        self.motion.home_all_axes()
        self.temp.set_limits(37.0, 0.5)
        self.display.show("Treatment ready. Press START.")
        # Reset touch counter so next touch starts treatment
        self.display.touch_count = 0
        self.state = 'IDLE'

    def treatment_loop(self):
        if not self.treatment_running:
            # wait for touch (handled in idle)
            return

        if not self.safety.is_ok():
            self.rf_amp.disable()
            self.display.show_error("Emergency Stop!")
            self.state = 'SHUTDOWN'
            return
        if self.temp.any_overlimit():
            self.rf_amp.disable()
            self.display.show_error("Temperature limit exceeded")
            self.state = 'SHUTDOWN'
            return

        elapsed = time.time() - self.start_time
        if elapsed >= self.total_time:
            self.rf_amp.disable()
            self.display.show("Treatment complete")
            self.state = 'SHUTDOWN'
            return

        # Generate a pulse
        self.awg.burst(self.frequency, self.pulse_duration)
        self.hydrophone.read()
        period = self.pulse_duration / self.duty_cycle
        time.sleep(period - self.pulse_duration)

    def shutdown(self):
        self.rf_amp.disable()
        self.rf_switch.disable()
        self.motion.disable()
        self.display.show("System off")
        self.safety.disable()
        print("\n[DONE] System shutdown complete.")


# ==================== MAIN ====================
if __name__ == "__main__":
    print("=" * 60)
    print("ONCOTRIPSY CONTROLLER DEMO (Mock Hardware)")
    print("=" * 60)
    controller = OncotripsyController()
    controller.run()
