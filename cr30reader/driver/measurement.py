"""
Measurement Result Classes

Data structures for storing and working with measurement results.
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class MeasurementResult:
    """Container for a complete color measurement result."""
    
    whitepoint: Tuple[float, float, float]
    xyz: Tuple[float, float, float]
    lab: Tuple[float, float, float]
    rgb: Tuple[int, int, int]
    spd: List[float]
    wavelengths: List[float]
    raw_data: Dict[str, Any]
    
    def __str__(self):
        return f"MeasurementResult(XYZ={self.xyz}, LAB={self.lab}, RGB={self.rgb})"
    
    def __repr__(self):
        return self.__str__()
    
    @property
    def xyz_dict(self) -> Dict[str, float]:
        """Return XYZ as dictionary."""
        return {"X": self.xyz[0], "Y": self.xyz[1], "Z": self.xyz[2]}

    @property
    def whitepoint_dict(self) -> Dict[str, float]:
        """Return Whitepoint as dictionary."""
        return {"X": self.whitepoint[0], "Y": self.whitepoint[1], "Z": self.whitepoint[2]}

    @property
    def lab_dict(self) -> Dict[str, float]:
        """Return LAB as dictionary."""
        return {"L": self.lab[0], "a": self.lab[1], "b": self.lab[2]}
    
    @property
    def rgb_dict(self) -> Dict[str, int]:
        """Return RGB as dictionary."""
        return {"R": self.rgb[0], "G": self.rgb[1], "B": self.rgb[2]}
    
    @property
    def spd_dict(self) -> Dict[float, float]:
        """Return SPD as wavelength->reflectance dictionary."""
        return dict(zip(self.wavelengths, self.spd))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "whitepoint": self.whitepoint_dict,
            "xyz": self.xyz_dict,
            "lab": self.lab_dict,
            "rgb": self.rgb_dict,
            "spd": self.spd_dict,
            "wavelengths": self.wavelengths,
            "raw_data": self.raw_data
        }
    
    def delta_e(self, other: 'MeasurementResult') -> float:
        """Calculate ΔE color difference with another measurement."""
        import math
        dL = self.lab[0] - other.lab[0]
        da = self.lab[1] - other.lab[1]
        db = self.lab[2] - other.lab[2]
        return math.sqrt(dL*dL + da*da + db*db)
    
    def is_similar(self, other: 'MeasurementResult', threshold: float = 1.0) -> bool:
        """Check if this measurement is similar to another (within ΔE threshold)."""
        return self.delta_e(other) <= threshold

