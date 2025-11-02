# Illuminant Data Directory

This directory contains spectral data for various standard illuminants used in color science calculations.

## Standard Illuminants

- **CIE Illuminant A**: Incandescent light (tungsten filament)
- **CIE Illuminant D50**: Daylight with correlated color temperature of 5000K
- **CIE Illuminant D65**: Daylight with correlated color temperature of 6500K (standard for sRGB)

## Adding New Illuminants

To add new illuminant data:

1. Create a CSV file with the format: `wavelength,spectral_power`
2. Place it in this directory
3. Update the `ColorScience` class to include the new illuminant
4. Add the illuminant to the `WhitePoint` mapping if it has a standard white point

## File Format

CSV files should have two columns:
- Column 1: Wavelength in nanometers
- Column 2: Spectral power distribution (relative values)

Example:
```
300,0.930483
301,0.967643
302,1.00597
...
```

## Available Illuminants

- `CIE_std_illum_A_1nm.csv` - CIE Standard Illuminant A (1nm resolution)
- `CIE_std_illum_D50.csv` - CIE Standard Illuminant D50
- `CIE_std_illum_D65.csv` - CIE Standard Illuminant D65

