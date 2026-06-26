## Tools
- 3D printer (FDM, PETG/ABS capable)
- Filaments (PETG, ABS)
- M6 Hex Key
- M2.5, M3, M4 Hex Keys/Screwdrivers (various sizes for module mounting)
- Wire Strippers (20-30 AWG)
- Crimping Tool (for JST, Molex, and RF connectors)
- Soldering Iron (fine tip for MCUs, general purpose for larger pads)
- Solder (lead-free recommended)
- Heat Gun (for heat shrink tubing)
- Digital Multimeter (DMM)
- Oscilloscope (100MHz+ bandwidth for RF signal analysis)
- Spectrum Analyzer (for RF signal characterization)
- Adjustable DC Power Supply (benchtop, 0-30V, 5A+)
- Precision Calipers/Ruler
- Drill and Drill Bit Set (for panel mounts and custom holes)
- M6 Tap and Tapping Handle (for aluminum extrusions if not pre-tapped)
- Deburring Tool
- Acrylic Solvent/Adhesive (for chamber assembly)
- SMA Wrench (torque limited)
- Pliers (needle-nose, cutting)
- Cable Ties and Mounts
- Label Printer/Marker
- Safety Glasses
- ESD Mat and Wrist Strap

## Assumptions
- Builder has basic electronics knowledge and soldering experience.
- Builder is familiar with mechanical assembly of aluminum extrusions and 3D printed parts.
- Builder has access to CAD software for reviewing assembly diagrams.
- Builder has experience flashing firmware and using embedded development environments (e.g., Vivado, Vitis, PlatformIO/Arduino IDE).
- Builder understands basic RF safety precautions and practices.
- Builder has access to degassed water for the experimental chamber and chiller loop.

## 1. Fabrication
### 1.1 3D Print all custom mounting brackets, housings, and chamber parts
*(not yet generated)*

### 1.2 Prepare aluminum extrusions by cutting, tapping M6 holes, and deburring edges
*(not yet generated)*

### 1.3 Drill and prepare openings in enclosure panels for display, panel-mount connectors, and fan
*(not yet generated)*

### 1.4 Assemble the cell culture chamber components including sealing the quartz bottom and borosilicate wall
*(not yet generated)*

### 1.5 Adhere acoustic foam panels to the interior surfaces of the enclosure panels
*(not yet generated)*

### 1.6 Attach RF amplifier mount plates to the top shelf plate
*(not yet generated)*

## 2. Wiring
### 2.1 Solder power and data headers/wires to Main MCU and Safety Watchdog MCU if not pre-populated
*(not yet generated)*

### 2.2 Wire AC input from isolation transformer to 24V power supply and verify output voltage
*(not yet generated)*

### 2.3 Connect 24V DC power distribution to main system components and voltage converters
*(not yet generated)*

### 2.4 Connect 5V and 3.3V regulated power to low-voltage electronics and sensors
*(not yet generated)*

### 2.5 Connect 12V buck converter output to impedance matching networks
*(not yet generated)*

### 2.6 Route and connect RF signal paths using SMA cables from DDS DAC to Transducers
*(not yet generated)*

### 2.7 Connect all safety interlock components to the Main Safety Relay Module
*(not yet generated)*

### 2.8 Wire data communication lines (SPI, I2C, UART, GPIO, USB) between MCUs, drivers, and sensors
*(not yet generated)*

## 3. Bring-up
### 3.1 Power up main 24V supply and verify 5V and 3.3V regulator outputs with DMM
*(not yet generated)*

### 3.2 Flash base firmware to Main MCU and Safety Watchdog MCU, establish serial communication
*(not yet generated)*

### 3.3 Test SPI communication with DDS DAC, power monitor ADC, RF variable attenuator, and RTD amplifiers
*(not yet generated)*

### 3.4 Verify I2C communication with CO2 sensor and impedance matching networks
*(not yet generated)*

### 3.5 Test UART communication with optical O2 sensor and all stepper drivers
*(not yet generated)*

### 3.6 Individually test and calibrate all stepper motors and encoders (XYZ stage, transducer turret, reflector stages)
*(not yet generated)*

### 3.7 Test RF signal path end-to-end with low power, verifying amplifier enables and relay switching functionality
*(not yet generated)*

## 4. Assembly
### 4.1 Assemble the main frame using aluminum extrusions, corner brackets, T-slot nuts, and M6 screws
*(not yet generated)*

### 4.2 Install all shelf plates and sorbothane isolation feet onto the main frame
*(not yet generated)*

### 4.3 Mount the XYZ stage rails, leadscrews, stepper motors, and encoders onto the middle shelf
*(not yet generated)*

### 4.4 Install the transducer turret mechanism, stepper motor, and all 8 transducers into their kinematic mounts
*(not yet generated)*

### 4.5 Mount all RF electronics, power supplies, and safety modules onto the shelves using their printed mounts
*(not yet generated)*

### 4.6 Install the cell chamber assembly, animal stage, water bath, and reflector mechanism onto the middle shelf
*(not yet generated)*

### 4.7 Mount the display, camera, and LED illumination, then install all enclosure panels including the door and safety interlock switch
*(not yet generated)*

### 4.8 Perform final cable routing, strain relief, and labeling throughout the system, ensuring all connections are secure and neat
*(not yet generated)*
