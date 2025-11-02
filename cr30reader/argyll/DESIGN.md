# Argyll Package Design

## Overview

The `argyll` package provides read/write support for ArgyllCMS file formats. It handles TI2 and CHT file reading, and TI3 file writing. All other operations (profiling, calibration, etc.) are handled by the ArgyllCMS suite manually.

## Package Structure

```
argyll/
├── __init__.py           # Package exports
├── argyll_parser.py      # TIFormat, TIReader, TIWriter - File format handling
└── DESIGN.md            # This document
```

## Dependencies

**External Dependencies:**
- `typing` - Type hints
- `dataclasses` - Data structure definitions
- `pathlib` - Path handling

**Internal Dependencies:**
- None - This package is standalone

## Core Classes

### TIFormat
**Purpose**: Shared format utilities for TI file operations

**Key Responsibilities:**
- Validate file formats
- Detect file formats from content
- Provide format constants

**Interface:**
```python
class TIFormat:
    @staticmethod
    def validate_ti2(file_path: str) -> bool
    @staticmethod
    def validate_cht(file_path: str) -> bool
    @staticmethod
    def detect_format(file_path: str) -> Optional[str]
```

### TIReader
**Purpose**: Read TI2 and CHT files

**Key Responsibilities:**
- Parse TI2 files (measurement data)
- Parse CHT files (chart definition with expected values)
- Uses TIFormat for validation

**Interface:**
```python
class TIReader:
    def __init__(self)
    
    # File reading
    def read_ti2(self, file_path: str) -> TIFile
    def read_cht(self, file_path: str) -> CHTFile
```

### TIWriter
**Purpose**: Write TI3 files

**Key Responsibilities:**
- Write TI3 files (complete chart data)
- Validate data before writing
- Uses TIFormat for format constants

**Interface:**
```python
class TIWriter:
    def __init__(self)
    
    # File writing
    def write_ti3(self, ti_file: TIFile, output_path: str) -> None
```

### ArgyllParser (Backwards Compatibility)
**Purpose**: Alias for TIReader for backwards compatibility

### TIFile
**Purpose**: Data structure for TI2/TI3 file contents

**Interface:**
```python
@dataclass
class TIFile:
    patches: List[TIPatch]
    metadata: Dict[str, Any]
    file_type: str  # "TI2" or "TI3"
```

### CHTFile
**Purpose**: Data structure for CHT file contents

**Interface:**
```python
@dataclass
class CHTFile:
    patches: List[CHTPatch]
    metadata: Dict[str, Any]
    box_shrink: Optional[float]
    ref_rotation: Optional[float]
```

## File Format Support

### TI2 Format (Read Only)
- **Purpose**: Measurement data from device
- **Content**: Patch names, XYZ values
- **Usage**: Input from device measurements

### CHT Format (Read Only)
- **Purpose**: Chart definition with expected values
- **Content**: Patch positions, expected XYZ values, chart layout
- **Usage**: Input for chart measurement workflows

### TI3 Format (Write Only)
- **Purpose**: Complete chart data for ArgyllCMS
- **Content**: Patch names, XYZ values, LAB values
- **Usage**: Output to ArgyllCMS for profiling

## Design Principles

1. **Separation of Concerns**: This package only handles file I/O, not chart reading workflows
2. **Minimal Scope**: Only read TI2/CHT, write TI3 - ArgyllCMS handles the rest
3. **Simple Interface**: Clean, focused API for file operations
4. **Error Handling**: Graceful failures with descriptive error messages

## Key Workflows

These workflows are external to this library and illustrate common usage patterns.

### Measurement Workflow (External)
1. Load TI2 or CHT file (using TIReader)
2. Initialize measurement session (handled externally)
3. For each patch:
   - Position sample (handled externally)
   - Measure color (handled externally)
   - Store result (handled externally)
4. Calculate errors for patches (handled externally)
5. Generate TI3 output (using TIWriter)
6. Save results (using TIWriter)

## Error Handling

### File Format Errors
- Graceful handling of malformed files
- Detailed error messages
- Format validation

### I/O Errors
- File permission handling
- File not found errors
- Fail gracefully

