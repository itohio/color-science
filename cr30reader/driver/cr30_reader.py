"""
CR30 Reader - High-level interface for CR30 colorimeter operations

Provides a user-friendly interface for color measurements and chart reading.
"""

import asyncio
from typing import Tuple, Optional, Dict, Any, List, Callable
from ..protocol import CR30Protocol
from ..color_science import ColorScience, WhitePoint
from .measurement import MeasurementResult


class CR30Reader(CR30Protocol):
    """High-level interface for CR30 colorimeter operations."""
    
    def __init__(self, science: ColorScience = None, whitepoints=WhitePoint(), *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cs = science or ColorScience(load=True)
        self._wp = whitepoints
        self._measurement_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._wavelengths = []
    
    @property
    def science(self) -> ColorScience: 
        return self._cs
    
    @property
    def whitepoint(self) -> WhitePoint: 
        return self._wp

    async def connect(self, upsample=True):
        """Connect to the device and initialize color science."""
        await super().connect()
        
        if self.model == "CR30":
            self._wavelengths = [400+i*(700-400)/30.0 for i in range(31)]
        
        if not upsample:
            self._cs = ColorScience(wavelengths=self._wavelengths, load=True)

    async def measure(self, space='XYZ', illuminant='D65/10', wait=0, timeout_per_step=0.5) -> Tuple:
        """
        Perform a single measurement and return color values.
        
        Args:
            space: Color space to return ('XYZ', 'LAB', 'RGB')
            illuminant: Illuminant for calculation ('D65/10', 'D50/10', etc.)
            wait: Time to wait for button press (0 = immediate trigger)
            timeout_per_step: Timeout for each measurement step
            
        Returns:
            Tuple of color values in requested space
        """
        space = space.upper()
        illuminant = illuminant.upper()
        
        result = await super().measure(timeout_per_step=timeout_per_step) if wait == 0 else await self.wait_measurement(timeout=wait, timeout_per_step=timeout_per_step)
        
        xyz = [float(i) for i in self._cs.spectrum_to_xyz(result["spd"], wavelengths=self._wavelengths, illuminant=illuminant)]
        return self._decide(xyz, space, illuminant)

    async def measure_avg(self, space='XYZ', illuminant='D65/10', count=3, delay=.5, wait=0, timeout_per_step=0.5) -> Tuple:
        """
        Perform multiple measurements and return averaged color values.
        
        Args:
            space: Color space to return ('XYZ', 'LAB', 'RGB')
            illuminant: Illuminant for calculation
            count: Number of measurements to average
            delay: Delay between measurements
            wait: Time to wait for first button press
            timeout_per_step: Timeout for each measurement step
            
        Returns:
            Tuple of averaged color values
        """
        space = space.upper()
        illuminant = illuminant.upper()
        
        if count < 1:
            raise ValueError("count must be positive")
        
        results = []
        result = await super().measure(timeout_per_step=timeout_per_step) if wait == 0 else await self.wait_measurement(timeout=wait, timeout_per_step=timeout_per_step)
        results.append(result)
        
        for i in range(count-1):
            await asyncio.sleep(delay)
            result = await super().measure(timeout_per_step=timeout_per_step)
            results.append(result)

        # Average the SPD values
        spd = [0] * len(results[0]["spd"])
        for r in results:
            spd = [a+b for a, b in zip(spd, r["spd"])]
        spd = [i / count for i in spd]

        xyz = [float(i) for i in self._cs.spectrum_to_xyz(spd, wavelengths=self._wavelengths, illuminant=illuminant)]
        return self._decide(xyz, space, illuminant)

    def _decide(self, xyz, space, illuminant) -> Tuple:
        """Convert XYZ to requested color space."""
        if space == 'XYZ':
            return tuple(xyz)

        whitepoint = self._wp[illuminant]

        if space == 'LAB':
            return self._cs.xyz_to_lab(*xyz, illuminant=whitepoint)

        if space == 'RGB':
            return self._cs.xyz_to_rgb(*xyz)

        raise ValueError(f"Unknown color space: {space}")

    async def calibrate_black(self, timeout: float = 5.0) -> Dict:
        """Perform black calibration."""
        return await self.calibrate(white=False, timeout=timeout)

    async def calibrate_white(self, timeout: float = 5.0) -> Dict:
        """Perform white calibration."""
        return await self.calibrate(white=True, timeout=timeout)

    def register_measurement_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for measurement results."""
        self._measurement_callbacks.append(callback)

    async def get_measurement_result(self, whitepoint=None, wait: float = 15, timeout_per_step: float = 1.5) -> MeasurementResult:
        """
        Get a complete measurement result with all color space conversions.
        
        Args:
            whitepoint: White point tuple (X, Y, Z) for LAB calculation. Defaults to D65/10.
            wait: Time to wait for button press
            timeout_per_step: Timeout for each measurement step
            
        Returns:
            MeasurementResult object with all color data
        """
        if whitepoint is None:
            whitepoint = self._wp['D65/10']
        
        result = await self.wait_measurement(timeout=wait, timeout_per_step=timeout_per_step)
        
        # Calculate all color spaces
        xyz = self._cs.spectrum_to_xyz(result["spd"], wavelengths=self._wavelengths, illuminant="D65/10")
        lab = self._cs.xyz_to_lab(*xyz, illuminant=whitepoint)
        rgb = self._cs.xyz_to_rgb(*xyz)
        
        return MeasurementResult(
            whitepoint=whitepoint,
            xyz=xyz,
            lab=lab,
            rgb=rgb,
            spd=result["spd"],
            wavelengths=self._wavelengths,
            raw_data=result
        )

