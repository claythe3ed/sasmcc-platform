import json
import time
from hardware_abstraction import (
    AWG, RFAmplifier, FastRFSwitch, ImpedanceMatching,
    StepperDriver, Hydrophone, ThermocoupleAmplifier,
    SafetyRelay, Display, LEDController, Camera
)

class OncotripsyController:
    def __init__(self):
        # Initialize hardware modules
        self.awg = AWG(spi_bus=0)
        self.rf_amp = RFAmplifier(gpio_pin='PA0')
        self.rf_switch = FastRFSwitch(gpio_pin='PA1')
        self.matching = ImpedanceMatching(i2c_bus=1)
        self.safety = SafetyRelay(gpio_pin='PA2')
        self.motion = StepperDriver()  # X, Y, Z with encoders
        self.hydrophone = Hydrophone(adc_channel=0)
        self.temp = ThermocoupleAmplifier(spi_bus=1)
        self.display = Display(lvds_port=0)
        self.led = LEDController(pwm_pin='PA3')
        self.camera = Camera(usb_port=0)

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
        # Test all modules
        if not self.safety.check_ok() or not self.awg.check() or not self.rf_amp.check():
            self.display.show_error("HW fault")
            self.state = 'SHUTDOWN'
            return
        self.display.show("Ready")
        self.state = 'IDLE'

    def idle_loop(self):
        if self.display.touch_pressed():
            self.state = 'LOAD_PARAMS'
        time.sleep(0.1)

    def load_params(self):
        # Read JSON from file
        with open('/mnt/sdcard/hardware_params.json', 'r') as f:
            self.params = json.load(f)
        opt = self.params['optimal_parameters']
        # Store values
        self.frequency = opt['frequency_Hz']
        self.pressure_target = opt['peak_negative_pressure_Pa']
        self.pulse_duration = opt['pulse_duration_s']
        self.duty_cycle = opt['duty_cycle']
        self.total_time = opt['treatment_duration_s']
        self.display.show(f"Loaded: {self.frequency/1e6:.2f} MHz, {self.pressure_target/1e6:.2f} MPa")
        self.state = 'SETUP'

    def setup_treatment(self):
        # Configure RF chain
        self.awg.set_frequency(self.frequency)
        self.awg.set_waveform('sine')
        self.rf_switch.enable()
        self.rf_amp.set_gain_from_pressure(self.pressure_target)  # needs calibration
        self.matching.tune_to_frequency(self.frequency)
        # Configure motion (scanning pattern)
        self.motion.home_all_axes()
        # Start temperature monitoring and control
        self.temp.set_limits(37.0, 0.5)  # 37°C ±0.5°C
        self.display.show("Treatment ready. Press START.")
        self.state = 'IDLE'  # Wait for user confirmation

    def treatment_loop(self):
        if not self.treatment_running:
            if self.display.touch_pressed():
                self.treatment_running = True
                self.start_time = time.time()
                self.display.show("Treatment active...")
            return

        # Safety checks
        if not self.safety.is_ok():  # E‑stop pressed
            self.rf_amp.disable()
            self.display.show_error("Emergency Stop!")
            self.state = 'SHUTDOWN'
            return
        if self.temp.any_overlimit():
            self.rf_amp.disable()
            self.display.show_error("Temperature limit exceeded")
            self.state = 'SHUTDOWN'
            return

        # Check elapsed time
        elapsed = time.time() - self.start_time
        if elapsed >= self.total_time:
            self.rf_amp.disable()
            self.display.show("Treatment complete")
            self.state = 'SHUTDOWN'
            return

        # Generate a single oncotripsy pulse
        # (here simplified; actual waveform might have multiple cycles)
        self.awg.burst(self.frequency, self.pulse_duration)
        self.hydrophone.read()  # optional: log pressure
        # Wait for next pulse based on duty cycle
        period = self.pulse_duration / self.duty_cycle
        time.sleep(period - self.pulse_duration)

        # Optional: move scanning stage between pulses
        # self.motion.move_to_next_position()

    def shutdown(self):
        self.rf_amp.disable()
        self.rf_switch.disable()
        self.motion.disable()
        self.display.show("System off")
        self.safety.disable()
