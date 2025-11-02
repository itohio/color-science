"""
ArgyllCMS File Format Support

Provides read/write support for ArgyllCMS file formats:
- Read: TI2 (measurement data), CHT (chart definition)
- Write: TI3 (complete chart data)

All other operations (profiling, calibration) are handled by ArgyllCMS suite.
"""

from .argyll_parser import (
    TIFormat,
    TIReader,
    TIWriter,
    ArgyllParser,  # Backwards compatibility alias
    TIFile,
    CHTFile,
    TIPatch,
    CHTPatch
)

__all__ = [
    "TIFormat",
    "TIReader",
    "TIWriter",
    "ArgyllParser",  # Backwards compatibility
    "TIFile",
    "CHTFile",
    "TIPatch",
    "CHTPatch"
]

