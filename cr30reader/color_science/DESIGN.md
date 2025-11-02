# Color Science Package Design

## Overview

The `color_science` package provides comprehensive spectral color calculations, including SPD-to-color space conversions, chromatic adaptation, and color space transformations. It handles the complexity of different spectral resolutions between device measurements and reference data.

## Package Structure

```
color_science/
├── __init__.py           # Package exports
├── color_science.py      # ColorScience, ColorScienceBase, SpectrumDataLoader
├── white_points.py       # WhitePoint - Standard illuminants
├── DESIGN.md            # This document
└── data/                # Reference data (moved to main data/)
    ├── CIE_xyz_1931_2deg.csv
    ├── CIE_xyz_1964_10deg.csv
    ├── CIE_std_illum_D65.csv
    ├── CIE_std_illum_D50.csv
    └── CIE_std_illum_A_1nm.csv
```

## Dependencies

**External Dependencies:**
- `numpy` - Numerical computations and array operations
- `scipy` - Interpolation functions for spectral resampling
- `colour-science` - Advanced color science algorithms (optional)

**Internal Dependencies:**
- `data/` - Reference CSV files for CIE observers and illuminants

## Core Classes

### ColorScienceBase (Abstract Base Class)
**Purpose**: Define interface for color science implementations

**Interface:**
```python
class ColorScienceBase(ABC):
    @abstractmethod
    def spectrum_to_xyz(self, spd, wavelengths=None, illuminant="D65/10") -> Tuple[float, float, float]
    @abstractmethod
    def adapt_xyz(self, X, Y, Z, Ws, Wd, method="bradford") -> Tuple[float, float, float]
    @abstractmethod
    def xyz_to_lab(self, X, Y, Z, whitepoint=WhitePoint().D65_10) -> Tuple[float, float, float]
    @abstractmethod
    def xyz_to_rgb(self, X, Y, Z, out_255=True) -> Tuple[float, float, float]
    @abstractmethod
    def lab_to_xyz(self, L, a, b, whitepoint=WhitePoint().D65_10) -> Tuple[float, float, float]
    @abstractmethod
    def rgb_to_xyz(self, r, g, b) -> Tuple[float, float, float]
```

### SpectrumDataLoader
**Purpose**: Loads and manages CIE observer and illuminant spectral datasets from CSV files

**Key Responsibilities:**
- Load CSV files from data directory
- Load CIE observer (CMF) data
- Load illuminant spectral data
- Handle wavelength downsampling and range restriction
- Manage loaded datasets in memory

**Interface:**
```python
class SpectrumDataLoader:
    def __init__(self, wavelengths=None)
    
    def load_csv(self, path: str) -> List[List[float]]
    def load_observer(self, path: str) -> Dict[str, np.ndarray]
    def load_illuminant(self, path: str) -> Dict[str, np.ndarray]
    def load_reference_data(self)
    def get_observer(self, wavelengths=None, observer="10") -> Dict[str, np.ndarray]
    def get_illuminant(self, wavelengths=None, illuminant="D65") -> Dict[str, np.ndarray]
    def downsample_nearest(self, X, Xp, Yp) -> np.ndarray
    def restrict_to_X_range(self, X, Xp, Yp) -> Tuple[np.ndarray, np.ndarray]
```

### ColorScience
**Purpose**: Concrete implementation of color science calculations

**Key Responsibilities:**
- Perform SPD-to-XYZ conversions
- Implement chromatic adaptation
- Convert between color spaces
- Handle spectral interpolation and resampling

**Interface:**
```python
class ColorScience(ColorScienceBase):
    def __init__(self, wavelengths=None, load=True)
    
    # Core conversion methods
    def spectrum_to_xyz(self, spd, wavelengths=None, illuminant="D65/10") -> Tuple[float, float, float]
    def xyz_to_lab(self, X, Y, Z, illuminant=WhitePoint.D65_10) -> Tuple[float, float, float]
    def xyz_to_rgb(self, X, Y, Z, out_255=True) -> Tuple[float, float, float]
    def lab_to_xyz(self, L, a, b, illuminant=WhitePoint.D65_10) -> Tuple[float, float, float]
    def rgb_to_xyz(self, r, g, b) -> Tuple[float, float, float]
    
    # Chromatic adaptation
    def adapt_xyz(self, X, Y, Z, Ws, Wd, method="bradford") -> Tuple[float, float, float]
    
    # Utility methods
    def upsample_interpolate(self, X, Xp, Yp) -> np.ndarray
```

### WhitePoint
**Purpose**: Standard CIE white points and illuminants

**Interface:**
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

## Design Patterns

### Spectral Resolution Handling
- **Problem**: Device measures at 10nm intervals, reference data at 1nm
- **Solution**: Interpolation and resampling using scipy
- **Implementation**: `interpolate_spectrum()` method

### Data Loading Strategy
- **Separation of Concerns**: Spectrum datasets loading is handled by `SpectrumDataLoader` class
- **Lazy Loading**: Reference data loaded on first use via `load_reference_data()`
- **Caching**: Loaded data cached in `SpectrumDataLoader` for performance
- **Fallback**: Graceful handling of missing data files

### Color Space Conversions
- **XYZ as Intermediate**: All conversions go through XYZ
- **Illuminant Awareness**: Proper handling of different illuminants
- **Chromatic Adaptation**: Bradford transform for illuminant changes

## Key Algorithms

### SPD to XYZ Conversion
1. Use `SpectrumDataLoader` to get CIE observer data (2° or 10°)
2. Use `SpectrumDataLoader` to get illuminant spectral data
3. Interpolate/resample to match wavelengths using `upsample_interpolate()`
4. Apply color matching functions
5. Calculate XYZ tristimulus values

### Chromatic Adaptation
1. Calculate adaptation matrices
2. Apply Bradford transform
3. Convert between illuminants

### Color Space Conversions
- XYZ ↔ LAB: Using illuminant-specific white points
- XYZ ↔ RGB: Using sRGB transformation matrix
- RGB ↔ LAB: Via XYZ intermediate

## Open Questions

1. **Observer Selection**: Should the application automatically choose 2° vs 10° observer based on measurement conditions?
   1. Default is 10°, D65
   2. User can chose different observer and/or illuminant

2. **Illuminant Database**: How should we handle the growing database of illuminants and make them easily discoverable?
   1. Should be a separate class that manages this data (move it out of color science)

3. **Precision vs Performance**: What precision should be maintained in calculations vs computational speed?
   1. Maximum precision preferred

4. **Custom Observers**: Should users be able to load custom observer data for specialized applications?
   1. Yes

5. **Spectral Range**: How should we handle measurements outside the standard 380-780nm range?
   1. This is CMF and illuminant spectrum dependent. 
   2. Perform calculations on matched wavelengths - missing wavelengths are 0 (not included at all)
   3. If user provides broader spd with matching cmf/illuminant - it is fine
   4. don't handle it explicitly

6. **Interpolation Methods**: Should we support different interpolation methods (linear, cubic, spline) for spectral data?
   1. Only spline

7. **Color Space Support**: Should we add support for additional color spaces (LUV, Hunter Lab, etc.)?
   1. Yes

8. **Validation**: What validation should be performed on input spectral data?
   1. Check if values make sense - fail if they don't
   2. Check if wavelength interval is consistent - issue a warning

9.  **Error Propagation**: How should we handle and report errors in color calculations?
    1.  let caller code catch exceptions

10. **Reference Data Updates**: How should we handle updates to CIE reference data?
    1.  whatever is in csv files is the truth

