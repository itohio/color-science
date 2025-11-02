"""
White Point Definitions

Provides CIE 1931 XYZ white points as a read-only mapping.
Supports standard illuminants and common white LEDs.
"""

from collections.abc import Mapping
from typing import Dict, Tuple


class WhitePoint(Mapping):
    """Provides CIE 1931 XYZ white points as a read-only mapping.
    
    Can be used like a smart enum:
        WhitePoint.D65_10  # Returns (94.81, 100.000, 107.32)
        WhitePoint['D65/10']  # Same as above
        WhitePoint.get('D65/10')  # Same as above
    """
    
    # Base white points dictionary (private class variable)
    _data: Dict[str, Tuple[float, float, float]] = {
        # Standard illuminants
        "D50/10": (96.72, 100.000, 81.43),
        "D55/10": (95.682, 100.000, 92.149),
        "D65/10": (94.81, 100.000, 107.32),
        "D75/10": (94.972, 100.000, 122.638),
        "D50/2": (96.422, 100.000, 82.521),
        "D65/2": (95.047, 100.000, 108.883),
        "D75/2": (94.972, 100.000, 122.638),
        "A": (109.850, 100.000, 35.585),
        "B": (99.092, 100.000, 85.313),
        "C": (98.074, 100.000, 118.232),
        "E": (100.000, 100.000, 100.000),
        "F1": (92.834, 100.000, 103.665),
        "F2": (99.187, 100.000, 67.395),
        "F3": (103.754, 100.000, 49.861),
        "F4": (109.147, 100.000, 38.813),
        "F5": (90.872, 100.000, 98.723),
        "F6": (97.309, 100.000, 60.188),
        "F7": (95.044, 100.000, 108.755),
        "F8": (96.413, 100.000, 82.333),
        "F9": (100.365, 100.000, 67.868),
        "F10": (96.174, 100.000, 108.882),
        "F11": (100.966, 100.000, 64.370),
        "F12": (108.046, 100.000, 39.228),
        
        # Common white LEDs
        "LED_CW_6500K":  (95.04, 100.0, 108.88),
        "LED_NW_4300K":  (97.0, 100.0, 92.0),
        "LED_WW_3000K":  (98.5, 100.0, 67.0),
        "LED_VWW_2200K": (103.0, 100.0, 50.0),
    }
    
    # Static properties for easy enum-like access
    D50_10 = _data["D50/10"]
    D55_10 = _data["D55/10"]
    D65_10 = _data["D65/10"]
    D75_10 = _data["D75/10"]
    D50_2 = _data["D50/2"]
    D65_2 = _data["D65/2"]
    D75_2 = _data["D75/2"]
    
    # Standard illuminants
    A = _data["A"]
    B = _data["B"]
    C = _data["C"]
    E = _data["E"]
    F1 = _data["F1"]
    F2 = _data["F2"]
    F3 = _data["F3"]
    F4 = _data["F4"]
    F5 = _data["F5"]
    F6 = _data["F6"]
    F7 = _data["F7"]
    F8 = _data["F8"]
    F9 = _data["F9"]
    F10 = _data["F10"]
    F11 = _data["F11"]
    F12 = _data["F12"]
    
    # Common white LEDs
    LED_CW_6500K = _data["LED_CW_6500K"]
    LED_NW_4300K = _data["LED_NW_4300K"]
    LED_WW_3000K = _data["LED_WW_3000K"]
    LED_VWW_2200K = _data["LED_VWW_2200K"]
    
    def __init__(self):
        """Initialize WhitePoint instance (for mapping interface compatibility)."""
        pass
    
    def __getitem__(self, key):
        """Get white point by key (supports automatic /10 suffix for D illuminants)."""
        # Auto-append /10 for standard illuminants without observer
        key_upper = key.upper()
        if "/" not in key_upper and key_upper in ["D50", "D55", "D65", "D75"]:
            key_upper += "/10"
        if key_upper not in self._data:
            raise KeyError(f"Unknown whitepoint '{key}'")
        return self._data[key_upper]  # Works because _data is a class variable
    
    def __iter__(self):
        """Iterate over white point keys."""
        return iter(self._data)  # Works because _data is a class variable
    
    def __len__(self):
        """Get number of white points."""
        return len(self._data)  # Works because _data is a class variable
    
    @classmethod
    def get(cls, key: str, default=None):
        """Get white point by key with optional default value."""
        key_upper = key.upper()
        if "/" not in key_upper and key_upper in ["D50", "D55", "D65", "D75"]:
            key_upper += "/10"
        return cls._data.get(key_upper, default)
    
    @classmethod
    def get_all(cls) -> Dict[str, Tuple[float, float, float]]:
        """Get all white points as a dictionary."""
        return cls._data.copy()
