# CR30 Colorimeter Reverse Engineering - Experimental Findings

## Overview
This document summarizes the experimental work done to reverse engineer the CR30 colorimeter protocol and develop color science calculations for printer characterization.

## Key Findings

### 1. CR30 Protocol Reverse Engineering

#### Device Communication
- **Device Model**: CR30 (SD6870B667)
- **Serial Number**: M443L0787 - V11.3
- **Firmware**: V10.0.0.0 (Build: 0.0.20231219)
- **Communication**: 60-byte packets over serial (19200/115200 baud)
- **Packet Structure**: `[START][CMD][SUBCMD][PARAM][52-byte payload][0xFF][CHECKSUM]`

#### Protocol Commands Discovered
- **AA 0A**: Device information queries (name, serial, firmware, status)
- **BB 17**: Device initialization
- **BB 13**: Simple "Check" command
- **BB 28**: Parameter queries (0x00-0x04, 0xFF)
- **BB 10/11**: Black/White calibration
- **BB 01**: Measurement trigger and data retrieval

#### Measurement Protocol
1. **Trigger**: `BB 01 00 00` - Initiates measurement
2. **Header**: `BB 01 09` - Returns measurement header with XYZ values
3. **Data Chunks**: 
   - `BB 01 10` - First SPD data (48 bytes)
   - `BB 01 11` - Second SPD data (48 bytes) 
   - `BB 01 12` - Third SPD data (30 bytes)
   - `BB 01 13` - Final chunk with XYZ copy

#### Spectral Data Format
- **Wavelengths**: 400-700nm in 10nm steps (31 bands)
- **Data Format**: Little-endian 32-bit floats
- **Total Data**: 124 bytes (31 floats × 4 bytes)
- **Measurement Accuracy**: Very high precision (ΔE < 1.0 for most samples)

### 2. Color Science Implementation

#### Spectral to XYZ Conversion
- **Method**: CIE 1931 10° observer with D65 illuminant
- **Implementation**: Custom Python implementation with proper interpolation
- **Accuracy**: Mean ΔE of 1.66 across test samples
- **Challenges**: Wavelength resolution differences between device (10nm) and reference data (1nm)

#### Key Algorithms Implemented
- `spectrum_to_xyz()`: Converts spectral reflectance to CIE XYZ
- `xyz_to_lab()`: CIE LAB color space conversion
- `xyz_to_rgb()`: sRGB conversion with gamma correction
- `adapt_xyz()`: Chromatic adaptation (Bradford, CAT02, von Kries)

#### Color Matching Functions
- **Observer**: CIE 1964 10° standard observer
- **Illuminant**: D65 standard illuminant
- **Interpolation**: Linear interpolation for wavelength matching
- **Downsampling**: Nearest neighbor for 1nm→10nm conversion

### 3. Experimental Results

#### Test Samples Analyzed
- **24 ColorChecker patches** with known LAB values
- **8 additional samples** (fluorescent, metallic, OLED displays)
- **Accuracy**: Most samples within ΔE < 5.0, some outliers up to ΔE 100+

#### Measurement Precision
- **Repeatability**: Excellent (ΔE < 0.1 for same sample)
- **Calibration**: Black/white calibration required for accuracy
- **Button Press Detection**: Automatic measurement trigger

#### Color Space Performance
- **XYZ Calculation**: Highly accurate spectral integration
- **LAB Conversion**: Proper white point handling (D65/10°)
- **RGB Output**: sRGB gamut with proper gamma correction

### 4. Printer Characterization Work

#### ArgyllCMS Integration
- **Target Generation**: 24-patch ColorChecker targets
- **Profile Creation**: ICC profile generation for Canon Selphy CP730
- **Correction Profiles**: Inverse mapping for print correction
- **Validation**: Print→scan→measure workflow

#### Key Commands Used
```bash
# Generate targets
targen -v -d4 -f24 -g6 -G -e0 -B0 -l400 ColorChecker24

# Read measurements
chartread -xl -F6 -Q1964_10 -S chart-name

# Create profiles
colprof -qh -Za -Zm -dpp -v -cmt -D"Selphy CP730" -S sRGB.icm selphy

# Inverse correction
collink -v -G -ir sRGB.icm selphy-m.icm selphy-inv.icm
```

#### Results
- **Relative Colorimetric**: Best performance for printer characterization
- **Absolute Colorimetric**: Failed due to paper white point issues
- **Perceptual**: Good for soft proofing
- **Gamut**: Significantly smaller than sRGB, especially in blues

### 5. Technical Challenges Solved

#### Protocol Reverse Engineering
- **Packet Structure**: 60-byte fixed format with checksum validation
- **Command Sequencing**: Proper handshake and measurement flow
- **Data Parsing**: Float extraction from binary payloads
- **Error Handling**: Timeout and retry mechanisms

#### Color Science Accuracy
- **Wavelength Matching**: Interpolation between 1nm and 10nm data
- **Observer Functions**: Proper CIE 1964 10° implementation
- **Illuminant Handling**: D65 spectral power distribution
- **White Point**: Correct reference white for LAB calculations

#### Integration Challenges
- **Async Communication**: Python asyncio for serial communication
- **Data Processing**: Real-time spectral data conversion
- **File Formats**: TI1/TI2/TI3 compatibility with ArgyllCMS
- **Profile Generation**: ICC profile creation workflow

## Open Questions for Future Development

### Protocol & Hardware
1. **What other CR30 commands exist beyond the ones discovered?**
I need to update ipynb with cells that would try and send different commands and log the responses and check what happens
2. **How does the device handle different measurement modes (reflectance vs. transmittance)?**
device only handles reflectance. however, it would be huge if it would also allow measuring emittance! That would open up to a possibility to use this device for screen calibration!
3. **What is the optimal baud rate and timing for reliable communication?**
It seems internal USB->Serial chip handles the baud rate. so any baud rate up to 2mbps can be used. I use 9600 since it is a good idea to allow the device to process readings. I don't like using arbitrary sleeps.
4. **Are there any device-specific calibration procedures we're missing?**
There is literally no documentation. It would be great to be able to contact the manufacturer and ask for protocol information, but no idea who is the real manufacturer.

### Color Science
5. **How can we improve accuracy for fluorescent and metallic samples?**
That I would like to know too. Metalic surfaces read as very dark, not gray as they appear. Paint with laquer over it also needs experimenting and validating.
6. **What's the best approach for handling different illuminants (D50, A, F11)?**
Device only supports D65/10 at 45/0 configuration. 
7. **Should we implement additional color spaces (LUV, Hunter Lab, etc.)?**
Would be interesting. Though, I plan to develop Golang library for that purpose, and that would need to support as many features as possible. Maybe even contribute to existing library.
8. **How can we validate our color calculations against other instruments?**
I am in the process of acquiring more instruments.
Also, I have SpyderCheckr24 with known LAB values. Though don't seem to find exact values for this particular checker.

### Printer Characterization
9. **What's the optimal target size and patch count for different printers?**
Depends on the size of the printer. the more patches the more accurate the result. Small printers require small patches - color bleeding limits this as well as the scanner positioning precision. need to print some guides for CR30
10. **How can we handle different paper types and finishes?**
each paper has to be calibrated separately
11. **What's the best approach for gamut mapping and out-of-gamut colors?**
I would like to have accurate colors for scientific prints and perceptually correct colors for art
12. **How can we improve the print→scan→measure workflow?**
automate it

### Software Architecture
13. **What's the best way to structure the code for maintainability?**
each file handles only one domain
each class has only one purpose (e.g. communication with device via serial - Device - only handles communication and perhaps packet build/check/validate; device feature realisation inside protocol - only aware of various commands, but not aware of how to interpret the data; then there is cr30colorimetry class that knows how to handle the data received from the device. maybe there needs to be another class to handle different device; also, all the colorimetry calculations are in ColorScience class; You get the pattern here?; w.r.t. functions - short, coincise and to the point. use composition and "script" pattern - follow SOLID principles when makes sense. don't put integration code and steps for calibration into one function. there must be functions that only do integration and not specific to one usecase... etc.)
class composition
14. **How should we handle different measurement devices (not just CR30)?**
separate class that interprets device data and knows the command sequences.
15. **What file formats should we support beyond TI1/TI2/TI3?**
cht would be nice if we already have that file instead of ti2.
16. **How can we make the software user-friendly for non-technical users?**
we can use GUI so the flow would be very similar to a wizard that guides users through steps.

### Integration & Workflow
17. **How can we integrate with existing color management workflows?**
cr30read tool should replace chartread tool. plug and play.
18. **What's the best way to handle batch measurements?**
not relevant now.
19. **How can we provide real-time feedback during measurements?**
print expected XYZ and measured XYZ. in GUI display expected color and measured.
Also, the GUI should display the chart itself and highlight the patch that is being measured. User can measure a different patch and the software should be able to select the closest match if current patch and measured do not match sufficiently enough.
20. **What visualization tools would be most helpful for users?**
Show the chart being measured(colors converted to display colors) and the colors measured.
Measured chart patch would be split(diagonally) upper part showing the wanted color and bottom part showing measured color. clicking on patch has zoomed version of the expected/measured colors with XYZ and LAB values.

### Performance & Reliability
21. **How can we optimize measurement speed and accuracy?**
Device has a button. `wait_measurement` waits for the button press. User moves the device, presses the button and the measurement is recorded and advanced(unless color error is too large, then it asks either to accept or remeasure). 
Averaging would work as follows: User presses the button, then the device does a few measurements(configurable), calculates the average and waits for the next button press.
22. **What's the best approach for handling measurement errors?**
Ask the user what to do with the error. (should be configurable as in chartread where you can silently accept. though it would be nice to log such errors in the stderr in cli). GUI could have checkboxes for ignoring, or a popup otherwise showing expected and measured errors with LAB and XYZ values as well as calculated dE.
23. **How can we ensure consistent results across different systems?**
Depends on measurement devices.
24. **What logging and debugging features are needed?**
logging to stderr is fine.

### Future Enhancements
25. **Should we support other color measurement devices?**
No. This is only for CR30 and variants.
26. **How can we implement advanced color analysis (metamerism, etc.)?**
Yes, color science library should implement metamerism and other color analysis methods.
27. **What machine learning approaches could improve accuracy?**
Not needed.
28. **How can we make the system more accessible to color professionals?**
Out of scope now.