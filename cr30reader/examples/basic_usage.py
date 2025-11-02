#!/usr/bin/env python3
"""
Basic usage example for CR30Reader

This example demonstrates how to use the CR30Reader library for color measurements.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import cr30reader
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from cr30reader.driver import CR30Reader
from cr30reader.color_science import ColorScience


async def main():
    """Main example function."""
    print("CR30Reader Basic Usage Example")
    print("=" * 40)
    
    # Initialize color science
    print("Initializing color science...")
    color_science = ColorScience()
    print(f"Color science initialized with {len(color_science.wavelengths) if color_science.wavelengths else 0} wavelength bands")
    
    # Example spectral data (simulated)
    print("\nExample spectral measurement:")
    wavelengths = color_science.wavelengths or [400 + i * 10 for i in range(31)]  # Default CR30 wavelengths
    spd = [0.5] * len(wavelengths)  # Simulated 50% reflectance across all wavelengths
    
    # Convert to XYZ
    xyz = color_science.spectrum_to_xyz(spd, wavelengths)
    print(f"XYZ: {xyz[0]:.3f}, {xyz[1]:.3f}, {xyz[2]:.3f}")
    
    # Convert to LAB
    lab = color_science.xyz_to_lab(*xyz)
    print(f"LAB: {lab[0]:.3f}, {lab[1]:.3f}, {lab[2]:.3f}")
    
    # Convert to RGB
    rgb = color_science.xyz_to_rgb(*xyz)
    print(f"RGB: {rgb[0]:.0f}, {rgb[1]:.0f}, {rgb[2]:.0f}")
    
    print("\nExample completed successfully!")
    print("\nTo use with actual CR30 device:")
    print("1. Connect CR30 to USB port")
    print("2. Run: python -m cr30reader.cli --port COM3 measure")
    print("3. Or use the GUI: python -m cr30reader.gui")


if __name__ == "__main__":
    asyncio.run(main())

