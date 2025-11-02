# CR30Reader Interface Design

## Overview

This document defines the public interfaces for the CR30Reader application, including function signatures, data structures, and usage patterns for each package level.

## High-Level Application Interface

### Main Application Class
```python
from cr30reader import CR30Reader

# Basic usage
reader = CR30Reader(port="COM3", baudrate=115200)
await reader.connect()
result = await reader.measure()
await reader.disconnect()
```

### Command Line Interface
```bash
# Basic measurement
python -m cr30reader --port COM3 measure --output sample.json

# Chart reading
python -m cr30reader --port COM3 chart --input ColorChecker24.ti1 --output results.ti3

# Batch measurements
python -m cr30reader --port COM3 batch --count 5 --output batch.json

# Device calibration
python -m cr30reader --port COM3 calibrate --white --black
```

### Graphical User Interface
```python
# Launch GUI
python -m cr30reader.gui
```

## Protocol Package Interfaces

### CR30Device Interface
```python
class CR30Device:
    def __init__(self, port: str = 'COM3', baudrate: int = 19200, verbose: bool = True)
    
    # Connection management
    async def connect(self) -> None
    async def disconnect(self) -> None
    
    # Raw communication
    async def send_raw(self, packet: bytes) -> None
    async def recv(self, timeout: Optional[float] = None) -> Optional[bytes]
    async def send_recv(self, start: int, cmd: int, subcmd: int = 0, 
                       param: int = 0, data: Optional[bytes] = None, 
                       timeout: float = 1.0) -> Optional[bytes]
    
    # Properties
    @property
    def name(self) -> str
    @property
    def model(self) -> str
    @property
    def serial_number(self) -> str
    @property
    def fw_version(self) -> str
```

### CR30Protocol Interface
```python
class CR30Protocol(CR30Device):
    # Device operations
    async def handshake(self) -> None
    async def calibrate(self) -> None
    async def trigger_measurement(self) -> bytes
    async def read_measurement(self, timeout_per_step: float = 1.5) -> Dict[str, Any]
```

### PacketBuilder Interface
```python
class PacketBuilder:
    @staticmethod
    def build_packet(start: int, cmd: int, subcmd: int = 0, 
                     param: int = 0, data: Optional[bytes] = None) -> bytes
    @staticmethod
    def build_handshake_packet(cmd: int, subcmd: int = 0, 
                              param: int = 0, data: Optional[bytes] = None) -> bytes
    @staticmethod
    def build_command_packet(cmd: int, subcmd: int = 0, 
                            param: int = 0, data: Optional[bytes] = None) -> bytes
    @staticmethod
    def calculate_checksum(packet: bytes) -> int
```

### PacketParser Interface
```python
class PacketParser:
    @staticmethod
    def is_valid_packet(packet: bytes) -> bool
    @staticmethod
    def extract_payload(packet: bytes) -> bytes
    @staticmethod
    def parse_header(packet: bytes) -> Dict[str, Any]
    @staticmethod
    def parse_device_info(packet: bytes) -> Dict[str, str]
    @staticmethod
    def parse_measurement_header(packet: bytes) -> Dict[str, Any]
    @staticmethod
    def parse_spd_chunk(packet: bytes) -> Dict[str, Any]
    @staticmethod
    def parse_xyz_chunk(packet: bytes) -> Dict[str, Any]
    @staticmethod
    def verify_checksum(packet: bytes) -> bool
```

## Color Science Package Interfaces

### ColorScience Abstract Interface
```python
class ColorScience(ABC):
    @abstractmethod
    def spectrum_to_xyz(self, spd, wavelengths=None, illuminant="D65/10") -> Tuple[float, float, float]
    @abstractmethod
    def adapt_xyz(self, X, Y, Z, Ws, Wd, method="bradford") -> Tuple[float, float, float]
    @abstractmethod
    def xyz_to_lab(self, X, Y, Z, whitepoint=WhitePoint.D65_10) -> Tuple[float, float, float]
    @abstractmethod
    def xyz_to_rgb(self, X, Y, Z, out_255=True) -> Tuple[float, float, float]
    @abstractmethod
    def lab_to_xyz(self, L, a, b, whitepoint=WhitePoint.D65_10) -> Tuple[float, float, float]
    @abstractmethod
    def rgb_to_xyz(self, r, g, b) -> Tuple[float, float, float]
```

### ColorScienceImpl Interface
```python
class ColorScienceImpl(ColorScience):
    def __init__(self, wavelengths=None, load=True)
    
    # Core conversions
    def spectrum_to_xyz(self, spd, wavelengths=None, illuminant="D65/10") -> Tuple[float, float, float]
    def xyz_to_lab(self, X, Y, Z, whitepoint=WhitePoint.D65_10) -> Tuple[float, float, float]
    def xyz_to_rgb(self, X, Y, Z, out_255=True) -> Tuple[float, float, float]
    def lab_to_xyz(self, L, a, b, whitepoint=WhitePoint.D65_10) -> Tuple[float, float, float]
    def rgb_to_xyz(self, r, g, b) -> Tuple[float, float, float]
    
    # Chromatic adaptation
    def adapt_xyz(self, X, Y, Z, Ws, Wd, method="bradford") -> Tuple[float, float, float]
    
    # Utility methods
    def load_csv(self, path: str) -> List[List[float]]
    def interpolate_spectrum(self, wavelengths: List[float], values: List[float], 
                           target_wavelengths: List[float]) -> List[float]
```

### WhitePoint Interface
```python
class WhitePoint:
    # Standard white points
    D65_2 = (0.95047, 1.00000, 1.08883)
    D65_10 = (0.94811, 1.00000, 1.07304)
    D50_2 = (0.96422, 1.00000, 0.82521)
    D50_10 = (0.96720, 1.00000, 0.81427)
    
    @staticmethod
    def get_available_white_points() -> Dict[str, Tuple[float, float, float]]
    @staticmethod
    def get_white_point(name: str) -> Tuple[float, float, float]
```

## Driver Package Interfaces

### CR30Reader Interface
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

### MeasurementResult Interface
```python
@dataclass
class MeasurementResult:
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
    def xyz_dict(self) -> Dict[str, float]
    @property
    def lab_dict(self) -> Dict[str, float]
    @property
    def rgb_dict(self) -> Dict[str, int]
```

## File Handling Package Interfaces

### ChartReader Interface
```python
class ChartReader:
    def __init__(self, device: CR30Reader, chart_file: str)
    
    # Chart operations
    async def read_chart(self, output_file: Optional[str] = None) -> ChartResult
    async def read_patch(self, patch_id: str) -> MeasurementResult
    async def read_patches(self, patch_ids: List[str]) -> List[MeasurementResult]
    
    # Chart information
    def get_chart_info(self) -> Dict[str, Any]
    def get_patch_list(self) -> List[str]
    def get_patch_count(self) -> int
    
    # Output generation
    def generate_ti2(self, measurements: List[MeasurementResult]) -> str
    def generate_ti3(self, measurements: List[MeasurementResult]) -> str
    def save_results(self, measurements: List[MeasurementResult], 
                    output_file: str, format: str = "ti3") -> None
```

### TIParser Interface
```python
class TIParser:
    def __init__(self)
    
    # File parsing
    def parse_ti1(self, file_path: str) -> TIFile
    def parse_ti2(self, file_path: str) -> TIFile
    def parse_ti3(self, file_path: str) -> TIFile
    def parse_file(self, file_path: str) -> TIFile
    
    # Validation
    def validate_ti1(self, file_path: str) -> bool
    def validate_ti2(self, file_path: str) -> bool
    def validate_ti3(self, file_path: str) -> bool
    
    # Information extraction
    def get_chart_info(self, file_path: str) -> Dict[str, Any]
    def get_patch_count(self, file_path: str) -> int
```

### TIFile Interface
```python
@dataclass
class TIFile:
    format: str  # "ti1", "ti2", "ti3"
    version: str
    chart_info: Dict[str, Any]
    patches: List[PatchInfo]
    measurements: Optional[List[MeasurementResult]]
    
    # File operations
    def to_ti1(self) -> str
    def to_ti2(self) -> str
    def to_ti3(self) -> str
    def save(self, file_path: str) -> None
    
    # Data access
    def get_patch(self, patch_id: str) -> Optional[PatchInfo]
    def get_measurement(self, patch_id: str) -> Optional[MeasurementResult]
    def add_measurement(self, patch_id: str, measurement: MeasurementResult) -> None
```

## Utils Package Interfaces

### ColorUtils Interface
```python
class ColorUtils:
    # Color space conversions
    @staticmethod
    def rgb_to_hex(r: int, g: int, b: int) -> str
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]
    @staticmethod
    def rgb_to_hsv(r: int, g: int, b: int) -> Tuple[float, float, float]
    @staticmethod
    def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]
    
    # Color validation
    @staticmethod
    def is_valid_rgb(r: int, g: int, b: int) -> bool
    @staticmethod
    def is_valid_hex(hex_color: str) -> bool
    @staticmethod
    def clamp_rgb(r: int, g: int, b: int) -> Tuple[int, int, int]
    
    # Color formatting
    @staticmethod
    def format_rgb(r: int, g: int, b: int, format: str = "decimal") -> str
    @staticmethod
    def format_lab(L: float, a: float, b: float, precision: int = 2) -> str
    @staticmethod
    def format_xyz(X: float, Y: float, Z: float, precision: int = 4) -> str
    
    # Color comparison
    @staticmethod
    def delta_e_cie76(lab1: Tuple[float, float, float], 
                      lab2: Tuple[float, float, float]) -> float
    @staticmethod
    def delta_e_cie94(lab1: Tuple[float, float, float], 
                      lab2: Tuple[float, float, float]) -> float
    @staticmethod
    def color_difference(lab1: Tuple[float, float, float], 
                        lab2: Tuple[float, float, float], 
                        method: str = "cie76") -> float
```

### FileUtils Interface
```python
class FileUtils:
    # Path operations
    @staticmethod
    def ensure_directory(path: str) -> None
    @staticmethod
    def get_file_extension(file_path: str) -> str
    @staticmethod
    def get_file_size(file_path: str) -> int
    @staticmethod
    def file_exists(file_path: str) -> bool
    
    # File validation
    @staticmethod
    def is_valid_file(file_path: str) -> bool
    @staticmethod
    def is_readable_file(file_path: str) -> bool
    @staticmethod
    def is_writable_file(file_path: str) -> bool
    
    # Directory operations
    @staticmethod
    def create_directory(path: str) -> None
    @staticmethod
    def list_files(directory: str, pattern: str = "*") -> List[str]
    @staticmethod
    def clean_directory(directory: str) -> None
    
    # File format detection
    @staticmethod
    def detect_file_format(file_path: str) -> str
    @staticmethod
    def is_ti_file(file_path: str) -> bool
    @staticmethod
    def is_csv_file(file_path: str) -> bool
    @staticmethod
    def is_json_file(file_path: str) -> bool
    
    # Backup operations
    @staticmethod
    def create_backup(file_path: str) -> str
    @staticmethod
    def restore_backup(backup_path: str, original_path: str) -> None
```

## Usage Patterns

### Basic Measurement
```python
from cr30reader import CR30Reader

reader = CR30Reader(port="COM3")
await reader.connect()
result = await reader.measure()
print(f"XYZ: {result.xyz}")
print(f"LAB: {result.lab}")
print(f"RGB: {result.rgb}")
await reader.disconnect()
```

### Chart Reading
```python
from cr30reader import CR30Reader
from cr30reader.file_handling import ChartReader

reader = CR30Reader(port="COM3")
await reader.connect()

chart_reader = ChartReader(reader, "ColorChecker24.ti1")
results = await chart_reader.read_chart("results.ti3")

await reader.disconnect()
```

### Custom Color Science
```python
from cr30reader.color_science import ColorScienceImpl, WhitePoint

cs = ColorScienceImpl()
X, Y, Z = cs.spectrum_to_xyz(spd_data, illuminant="D65/10")
L, a, b = cs.xyz_to_lab(X, Y, Z, WhitePoint.D65_10)
r, g, b = cs.xyz_to_rgb(X, Y, Z)
```

## Open Questions

1. **Error Handling**: Should interfaces use exceptions or return error codes for error handling?
   1. Interfaces don't do anything (unimplemented method call fails automatically)

2. **Async Patterns**: How should synchronous and asynchronous operations be mixed in the interfaces?
   1. Async is anything that accesses serial port

3. **Type Safety**: Should we use more specific type hints and validation for interface parameters?
   1. Specific type hints are good

4. **Backward Compatibility**: How should we handle interface changes while maintaining backward compatibility?
   1. Interfaces should not change at all unless new features are added
   2. Or explicitly fixing naming

5. **Documentation**: How should interface documentation be maintained and updated?
   1. Docstrings

6. **Testing**: How should interface contracts be tested and validated?
   1. Unit tests

7. **Performance**: What performance characteristics should be guaranteed by the interfaces?
   1. Don't care about performance

8. **Configuration**: How should interface behavior be configured and customized?
   1. Interfaces are not configurable. Implementation is.

9.  **Logging**: Should interfaces include logging and debugging capabilities?
    1.  Logging should be first class citisen, however, interfaces don't implement anything, they provide the contracts for type safety.

10. **Extensibility**: How should interfaces be designed for future extensions and modifications?
    One step at a time.
