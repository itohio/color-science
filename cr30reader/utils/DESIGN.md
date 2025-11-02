# Utils Package Design

## Overview

The `utils` package provides common utility functions and helpers used throughout the CR30Reader application. It includes color manipulation utilities, file operations, and other shared functionality.

## Package Structure

```
utils/
├── __init__.py           # Package exports
├── color_utils.py        # ColorUtils - Color manipulation
├── file_utils.py         # FileUtils - File operations
└── DESIGN.md            # This document
```

## Dependencies

**External Dependencies:**
- `typing` - Type hints
- `pathlib` - Path manipulation
- `json` - JSON serialization
- `csv` - CSV file operations
- `datetime` - Date/time utilities

**Internal Dependencies:**
- None (utility functions)

## Core Classes

### ColorUtils
**Purpose**: Color manipulation and conversion utilities

**Key Responsibilities:**
- Color space conversions
- Color validation
- Color formatting
- Color comparison operations

**Interface:**
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

### FileUtils
**Purpose**: File and directory operations

**Key Responsibilities:**
- File path manipulation
- File validation
- Directory operations
- File format detection

**Interface:**
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

## Design Patterns

### Static Utility Classes
- No state management
- Pure functions
- Easy to test and maintain

### Functional Programming
- Immutable operations
- No side effects
- Composable functions

### Error Handling
- Graceful error handling
- Meaningful error messages
- Fallback behaviors

## Key Utilities

### Color Manipulation
- **RGB ↔ Hex**: Convert between RGB and hexadecimal color formats
- **RGB ↔ HSV**: Convert between RGB and HSV color spaces
- **Color Validation**: Validate color values and ranges
- **Color Formatting**: Format colors for display and output

### File Operations
- **Path Management**: Safe path manipulation and validation
- **File Validation**: Check file existence, readability, writability
- **Format Detection**: Automatic file format detection
- **Backup Operations**: Create and restore file backups

### Data Formatting
- **Color Formatting**: Format color values for different outputs
- **Precision Control**: Control decimal precision in formatting
- **Output Formats**: Support multiple output formats

## Error Handling

### Color Validation
- Range checking for color values
- Format validation for hex colors
- Clamping out-of-range values

### File Operations
- Permission checking
- Path validation
- Graceful error handling

### Data Formatting
- Type checking
- Precision validation
- Format validation

## Open Questions

1. **Color Space Support**: Should we add support for additional color spaces (CMYK, HSL, etc.)?

2. **Delta E Methods**: Should we implement more advanced delta E calculations (CIEDE2000, etc.)?

3. **File Format Support**: Should we add support for additional file formats (ICC profiles, etc.)?

4. **Performance**: How should we optimize utility functions for performance?

5. **Validation Rules**: What validation rules should be applied to color and file data?

6. **Error Messages**: How should we provide meaningful error messages for utility functions?

7. **Configuration**: Should utility functions be configurable for different use cases?

8. **Logging**: Should utility functions include logging for debugging and monitoring?

9. **Testing**: How should we ensure comprehensive testing of utility functions?

10. **Documentation**: How should we document utility functions for users and developers?

