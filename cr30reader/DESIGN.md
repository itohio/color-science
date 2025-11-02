# CR30Reader Design Document

## High-Level Architecture

CR30Reader is a modular Python application for color chart reading using the CR30 colorimeter device. The architecture follows a layered approach with clear separation of concerns.

### Package Structure

```
cr30reader/
├── protocol/          # Low-level device communication
├── color_science/     # Spectral color calculations
├── driver/            # High-level device interface
├── argyll/            # ArgyllCMS file format support (TI2/CHT read, TI3 write)
├── utils/             # Common utilities
├── data/              # Reference data (CIE observers, illuminants)
├── examples/          # Usage examples
├── cli.py             # Command-line interface
├── gui.py             # Graphical user interface
└── __main__.py        # Package entry point
```

### Dependencies

**External Dependencies:**
- `pyserial-asyncio` - Asynchronous serial communication
- `numpy` - Numerical computations
- `scipy` - Scientific computing (interpolation)
- `colour-science` - Color science algorithms
- `matplotlib` - Plotting and visualization
- `customtkinter` - Modern GUI framework

**Internal Dependencies:**
- `protocol` → `color_science` (for spectral calculations)
- `driver` → `protocol` + `color_science`
- `cli/gui` → `driver` + `argyll` + `utils`

### Core Interfaces

#### Main Application Interface
```python
# High-level usage
from cr30reader import CR30Reader

reader = CR30Reader(port="COM3")
await reader.connect()
result = await reader.measure()
```

#### Command Line Interface
```bash
# CLI usage
python -m cr30reader --port COM3 measure --output sample.json
python -m cr30reader --port COM3 chart --input ColorChecker24.ti1
```

#### GUI Interface
```python
# GUI usage
python -m cr30reader.gui
```

## Open Questions

1. **Error Handling Strategy**: Should the application use exceptions or return error codes for device communication failures?
   1. Exceptions

2. **Configuration Management**: How should device settings (baud rate, timeouts) be persisted and managed?
   1. Command line parameters

3. **Measurement Validation**: What validation rules should be applied to ensure measurement quality?
   1. If calculating average check for stdev

4. **File Format Support**: Should we support additional chart formats beyond TI1/TI2/TI3?
   1. TI2 and CHT for reading (via argyll package)
   2. TI3 for writing only (via argyll package)
   3. All other operations (profiling, calibration) handled by ArgyllCMS suite manually
   4. Output JSON (via utils)
   5. Output CSV (via utils)
      1. XYZ, LAB, RGB - expand to separate columns
      2. Wavelengths go to column header and SPD to the column values
         1. Each measurement should have the same wavelengths, so use first one for the headers
   6. Output to console as a pretty table by default

5. **Real-time Processing**: Should spectral data be processed in real-time during measurement or batched?
   1. Realtime

6. **Threading Model**: How should the GUI handle long-running measurements without blocking?
   1. Asynchronously

7. **Data Persistence**: Should measurement history be automatically saved to a database or files?
   1. No.
   2. Measurements themselves are saved either in TI3, CSV, JSON, or printed to the console

8. **Plugin Architecture**: Should the application support plugins for custom color science algorithms?
   1. No need

9.  **Performance Optimization**: What caching strategies should be used for frequently accessed reference data?
    1.  Load once on startup or first use

10. **Internationalization**: Should the application support multiple languages for UI and error messages?
    1.  No

