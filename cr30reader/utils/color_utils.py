"""
Color Utility Functions

Common color-related utility functions.
"""

import math
from typing import Tuple, List, Dict, Any
import numpy as np


class ColorUtils:
    """Utility functions for color calculations."""
    
    @staticmethod
    def delta_e_cie76(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
        """Calculate ΔE*ab (CIE 1976) color difference."""
        dL = lab1[0] - lab2[0]
        da = lab1[1] - lab2[1]
        db = lab1[2] - lab2[2]
        return math.sqrt(dL*dL + da*da + db*db)
    
    @staticmethod
    def delta_e_cie94(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
        """Calculate ΔE*94 color difference."""
        dL = lab1[0] - lab2[0]
        da = lab1[1] - lab2[1]
        db = lab1[2] - lab2[2]
        
        C1 = math.sqrt(lab1[1]*lab1[1] + lab1[2]*lab1[2])
        C2 = math.sqrt(lab2[1]*lab2[1] + lab2[2]*lab2[2])
        dC = C1 - C2
        
        dH = math.sqrt(da*da + db*db - dC*dC)
        
        SL = 1
        SC = 1 + 0.045 * C1
        SH = 1 + 0.015 * C1
        
        kL = 1
        kC = 1
        kH = 1
        
        return math.sqrt((dL/(kL*SL))**2 + (dC/(kC*SC))**2 + (dH/(kH*SH))**2)
    
    @staticmethod
    def delta_e_cie2000(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
        """Calculate ΔE*00 (CIE 2000) color difference."""
        # This is a simplified version - full implementation is complex
        return ColorUtils.delta_e_cie94(lab1, lab2)
    
    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex string."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex string to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def lab_to_lch(lab: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Convert LAB to LCH color space."""
        L, a, b = lab
        C = math.sqrt(a*a + b*b)
        H = math.atan2(b, a) * 180 / math.pi
        if H < 0:
            H += 360
        return (L, C, H)
    
    @staticmethod
    def lch_to_lab(lch: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Convert LCH to LAB color space."""
        L, C, H = lch
        H_rad = H * math.pi / 180
        a = C * math.cos(H_rad)
        b = C * math.sin(H_rad)
        return (L, a, b)
    
    @staticmethod
    def is_color_similar(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float], 
                        threshold: float = 1.0) -> bool:
        """Check if two colors are similar within a threshold."""
        return ColorUtils.delta_e_cie76(lab1, lab2) <= threshold
    
    @staticmethod
    def calculate_gamut_volume(xyz_points: List[Tuple[float, float, float]]) -> float:
        """Calculate the volume of a color gamut from XYZ points."""
        if len(xyz_points) < 4:
            return 0.0
        
        # Convert to numpy array for easier calculation
        points = np.array(xyz_points)
        
        # Simple convex hull volume calculation
        from scipy.spatial import ConvexHull
        try:
            hull = ConvexHull(points)
            return hull.volume
        except ImportError:
            # Fallback to simple approximation
            return 0.0
    
    @staticmethod
    def calculate_gamut_area(xy_points: List[Tuple[float, float]]) -> float:
        """Calculate the area of a color gamut from xy chromaticity points."""
        if len(xy_points) < 3:
            return 0.0
        
        # Shoelace formula for polygon area
        area = 0.0
        n = len(xy_points)
        for i in range(n):
            j = (i + 1) % n
            area += xy_points[i][0] * xy_points[j][1]
            area -= xy_points[j][0] * xy_points[i][1]
        return abs(area) / 2.0
    
    @staticmethod
    def xyz_to_xy(xyz: Tuple[float, float, float]) -> Tuple[float, float]:
        """Convert XYZ to xy chromaticity coordinates."""
        X, Y, Z = xyz
        total = X + Y + Z
        if total == 0:
            return (0, 0)
        return (X / total, Y / total)
    
    @staticmethod
    def xy_to_xyz(xy: Tuple[float, float], Y: float = 1.0) -> Tuple[float, float, float]:
        """Convert xy chromaticity coordinates to XYZ."""
        x, y = xy
        if y == 0:
            return (0, 0, 0)
        X = (x * Y) / y
        Z = ((1 - x - y) * Y) / y
        return (X, Y, Z)
    
    @staticmethod
    def calculate_whitepoint_error(measured_xyz: Tuple[float, float, float], 
                                 target_xyz: Tuple[float, float, float]) -> float:
        """Calculate the error between measured and target white points."""
        # Convert to LAB for comparison
        from ..color_science import ColorScience
        cs = ColorScience()
        
        lab1 = cs.xyz_to_lab(*measured_xyz)
        lab2 = cs.xyz_to_lab(*target_xyz)
        
        return ColorUtils.delta_e_cie76(lab1, lab2)
    
    @staticmethod
    def format_color_values(xyz: Tuple[float, float, float], 
                          lab: Tuple[float, float, float], 
                          rgb: Tuple[int, int, int]) -> str:
        """Format color values for display."""
        return f"XYZ: {xyz[0]:.3f}, {xyz[1]:.3f}, {xyz[2]:.3f}\n" \
               f"LAB: {lab[0]:.3f}, {lab[1]:.3f}, {lab[2]:.3f}\n" \
               f"RGB: {rgb[0]}, {rgb[1]}, {rgb[2]}"

