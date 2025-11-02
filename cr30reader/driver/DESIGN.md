# Driver Package Design

## Overview

The `driver` package provides the high-level interface for CR30 colorimeter operations. It combines protocol communication with color science calculations to offer a user-friendly API for color measurements and chart reading.

## Package Structure

```
driver/
├── __init__.py           # Package exports
├── cr30_reader.py        # CR30Reader - Main driver class
├── measurement.py        # MeasurementResult - Data structures
└── DESIGN.md            # This document
```

## Dependencies

**External Dependencies:**
- `asyncio` - Asynchronous programming
- `typing` - Type hints
- `dataclasses` - Data structure definitions

**Internal Dependencies:**
- `protocol` - Low-level device communication
- `color_science` - Spectral color calculations

## Core Classes

### CR30Reader
**Purpose**: High-level interface for CR30 colorimeter operations

**Key Responsibilities:**
- Coordinate protocol and color science operations
- Provide simplified measurement interface
- Handle device connection and calibration
- Manage measurement callbacks and events

**Interface:**
```python
class CR30Reader(CR30Protocol):
    def __init__(self, science: ColorScienceImpl = None, 
                 whitepoints=WhitePoint(), *args, **kwargs)
    
    # Connection management
    async def connect(self, upsample=True) -> None
    async def disconnect(self) -> None
    
    # Measurement operations
    async def measure(self, space='XYZ', illuminant='D65/10', 
                     wait=0, timeout_per_step=0.5) -> Tuple
    async def measure_spectral(self, illuminant='D65/10', 
                              wait=0, timeout_per_step=0.5) -> Dict[str, Any]
    
    # Calibration
    async def calibrate(self, white=True, black=True) -> None
    
    # Properties
    @property
    def science(self) -> ColorScienceImpl
    @property
    def whitepoint(self) -> WhitePoint
    @property
    def wavelengths(self) -> List[float]
    
    # Callback management
    def add_measurement_callback(self, callback: callable) -> None
    def remove_measurement_callback(self, callback: callable) -> None
```

### MeasurementResult
**Purpose**: Data structure for measurement results

**Key Responsibilities:**
- Store complete measurement data
- Provide formatted output methods
- Support serialization for file I/O

**Interface:**
```python
@dataclass
class MeasurementResult:
    whitepoint: Tuple[float, float, float]
    xyz: Tuple[float, float, float]
    lab: Tuple[float, float, float]
    rgb: Tuple[int, int, int]
    spd: List[float]
    wavelengths: List[float]
    raw_data: Dict[str, Any]
    
    # Output methods
    def to_text(self) -> str
    def to_json(self) -> str
    def to_csv(self) -> str
    
    # Property access
    @property
    def whitepoint_dict(self) -> Dict[str, float]
    @property
    def xyz_dict(self) -> Dict[str, float]
    @property
    def lab_dict(self) -> Dict[str, float]
    @property
    def rgb_dict(self) -> Dict[str, int]
```

## Design Patterns

### Composition over Inheritance
- `CR30Reader` inherits from `CR30Protocol` but composes `ColorScienceImpl`
- Clear separation between communication and calculation concerns

### Async/Await Pattern
- All I/O operations are asynchronous
- Non-blocking measurement operations
- Proper resource cleanup on disconnect

### Callback System
- Event-driven measurement processing
- Extensible callback mechanism
- Real-time data processing support

### Data Encapsulation
- `MeasurementResult` encapsulates all measurement data
- Multiple output formats supported
- Type-safe data access

## Key Workflows

### Single Measurement
1. Connect to device
2. Calibrate if needed
3. Trigger measurement
4. Process spectral data
5. Convert to target color space
6. Return structured result

### Batch Measurements
1. Initialize measurement session
2. For each measurement:
   - Wait for user trigger
   - Measure and process
   - Store result
3. Return batch results

### Averaging
1. User triggers a measurement
2. Number of measurements are taken automatically
3. Measured spectrum is averaged and used for XYZ calculation

## Error Handling

### Connection Errors
- Do not retry, exit early
- Clear error messages for troubleshooting
- Graceful degradation when device unavailable

### Measurement Errors
- Timeout handling for slow measurements
- Validation of measurement quality

### Data Processing Errors
- Spectral data validation
- Color space conversion error handling
- Fallback to raw data when processing fails

## Open Questions

1. **Measurement Quality**: How should we validate measurement quality and detect bad measurements?
   1. This package don't. User decides by calculating deltaE

2. **Calibration Strategy**: Should calibration be automatic, manual, or configurable?
   1. Configurable calibration. User chooses to call Calibrate or not and in what order.

3. **Error Recovery**: What strategies should be used when measurements fail or timeout?
   1. Raise an exception.

4. **Data Persistence**: Should measurement results be automatically saved to files or database?
   1. This package does not concern itself with external databases or files.

5. **Real-time Processing**: Should spectral data be processed in real-time or batched?
   1. Realtime processing.

6. **Measurement Modes**: How should we handle different measurement modes (reflectance, transmittance, etc.)?
   1. User selectable.
   2. User should be able to select observer and illuminant.

7. **Batch Operations**: How should batch measurements be optimized for performance?
   1. Don't optimize for performance.

8. **Callback Management**: How should we handle callback errors and prevent them from breaking measurements?
   1. Ignore errors.
   2. Exceptions should function as usual.

9.  **Resource Management**: How should we ensure proper cleanup of resources and connections?
    1.  User should call disconnect.

10. **Configuration**: How should device-specific settings be managed and persisted?
    1.  This package does not concern itself with external settings.
    2.  All required data should be provided either during instantiation or method calling.

