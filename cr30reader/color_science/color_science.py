"""
Color Science Implementation

Comprehensive spectral color calculator for different measurement modes.
Handles different resolutions between device (10nm) and reference data (1nm).
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any
import os
from .white_points import WhitePoint


class SpectrumDataLoader:
    """Loads and manages CIE observer and illuminant spectral datasets from CSV files."""
    
    def __init__(self, wavelengths=None):
        """Initialize the data loader with optional target wavelengths."""
        self.wavelengths = wavelengths
        self._observers = None
        self._illuminants = None
    
    def load_csv(self, path):
        """Load CSV data from file."""
        # Try to load from data directory first
        data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        data_path = os.path.join(data_dir, path)
        
        if os.path.exists(data_path):
            file_path = data_path
        else:
            # Fallback to original path
            file_path = path
        
        with open(file_path) as f:
            return [
                [float(j) if j != "NaN" else 0.0 for j in i.strip().split(",")]
                for i in f.readlines()
                if len(i) > 2
            ]
    
    def load_illuminant(self, path):
        """Load illuminant data from CSV file."""
        data = self.load_csv(path)
        if self.wavelengths:
            return {
                'wavelengths': np.array(self.wavelengths),
                'values': self.downsample_nearest(self.wavelengths, [i[0] for i in data], [i[1] for i in data]),
            }
        return {
            'wavelengths': np.array([i[0] for i in data]),
            'values': np.array([i[1] for i in data])
        }
    
    def load_observer(self, path):
        """Load observer data from CSV file."""
        data = self.load_csv(path)
        if self.wavelengths:
            return {
                'wavelengths': np.array(self.wavelengths),
                'x_bar': self.downsample_nearest(self.wavelengths, [i[0] for i in data], [i[1] for i in data]),
                'y_bar': self.downsample_nearest(self.wavelengths, [i[0] for i in data], [i[2] for i in data]),
                'z_bar': self.downsample_nearest(self.wavelengths, [i[0] for i in data], [i[3] for i in data]),
            }
        return {
            "wavelengths": np.array([i[0] for i in data]),
            "x_bar": np.array([i[1] for i in data]),
            "y_bar": np.array([i[2] for i in data]),
            "z_bar": np.array([i[3] for i in data]),
        }
    
    def downsample_nearest(self, X, Xp, Yp):
        """Downsamples Yp from Xp to X discarding non-existent X."""
        X  = np.array(X, dtype=float)
        Xp = np.array(Xp, dtype=float)
        Yp = np.array(Yp, dtype=float)
        Y = np.zeros_like(X)
        for i, Xi in enumerate(X):
            idx = np.argmin(np.abs(Xp - Xi))
            Y[i] = Yp[idx]
        return Y
    
    def restrict_to_X_range(self, X, Xp, Yp):
        """Restricts Xp and Yp to lie within the min/max of X."""
        X  = np.array(X,  dtype=float)
        Xp = np.array(Xp, dtype=float)
        Yp = np.array(Yp, dtype=float)
        Xmin, Xmax = np.min(X), np.max(X)
        mask = (Xp >= Xmin) & (Xp <= Xmax)
        return Xp[mask], Yp[mask]
    
    def load_reference_data(self):
        """Load CMF and illuminant data from CSV files."""
        self._observers = self._load_cmf_data()
        self._illuminants = self._load_illuminants()
    
    def _load_cmf_data(self):
        """Load CIE color matching functions."""
        return {
            '10': self.load_observer("CIE_xyz_1964_10deg.csv"),
            '2': self.load_observer("CIE_xyz_1931_2deg.csv"),
        }
    
    def _load_illuminants(self):
        """Load standard illuminant data."""
        return {
            'D65': self.load_illuminant("CIE_std_illum_D65.csv"),
            'D50': self.load_illuminant("CIE_std_illum_D50.csv"),
            'A': self.load_illuminant("CIE_std_illum_A_1nm.csv"),
        }
    
    def get_observer(self, wavelengths=None, observer="10"):
        """Get color matching function data."""
        if '/' in observer:
            observer = observer.split('/')[1]
        elif observer is None:
            observer = '10'
        cmf = self._observers[observer]
        if wavelengths is None:
            return cmf
        _cmf = {}
        _cmf["wavelengths"], _cmf["x_bar"] = self.restrict_to_X_range(wavelengths, cmf["wavelengths"], cmf["x_bar"])
        _, _cmf["y_bar"] = self.restrict_to_X_range(wavelengths, cmf["wavelengths"], cmf["y_bar"])
        _, _cmf["z_bar"] = self.restrict_to_X_range(wavelengths, cmf["wavelengths"], cmf["z_bar"])
        return _cmf
    
    def get_illuminant(self, wavelengths=None, illuminant="D65"):
        """Get illuminant data."""
        if '/' in illuminant:
            illuminant = illuminant.split('/')[0]
        elif illuminant is None:
            illuminant = 'D65'
        spd = self._illuminants[illuminant]
        if wavelengths is None:
            return spd
        _spd = {}
        _spd["wavelengths"], _spd["values"] = self.restrict_to_X_range(wavelengths, spd["wavelengths"], spd["values"])
        return _spd


class ColorScienceBase(ABC):
    """Abstract base class for color science calculations."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    def spectrum_to_xyz(self, spd, wavelengths=None, illuminant="D65/10"):
        """Convert spectral power distribution to XYZ."""
        pass
    
    @abstractmethod
    def adapt_xyz(self, X, Y, Z, Ws, Wd, method="bradford"):
        """Chromatic adaptation of XYZ values."""
        pass
    
    @abstractmethod
    def xyz_to_lab(self, X, Y, Z, illuminant=WhitePoint.D65_10):
        """Convert XYZ to LAB color space."""
        pass
    
    @abstractmethod
    def xyz_to_rgb(self, X, Y, Z, out_255=True):
        """Convert XYZ to RGB."""
        pass
    
    @abstractmethod
    def lab_to_xyz(self, L, a, b, illuminant=WhitePoint.D65_10):
        """Convert LAB to XYZ color space."""
        pass
    
    @abstractmethod
    def rgb_to_xyz(self, r, g, b):
        """Convert RGB to XYZ."""
        pass

    def rgb_to_lab(self, r, g, b, illuminant=None):
        """Convert sRGB → CIE LAB by chaining rgb_to_xyz → xyz_to_lab."""
        X, Y, Z = self.rgb_to_xyz(r, g, b)
        L, a, b = self.xyz_to_lab(X, Y, Z, illuminant=illuminant)
        return L, a, b

    def lab_to_rgb(self, L, a, b, illuminant=None, out_255=True):
        """Convert CIE LAB → sRGB by chaining lab_to_xyz → xyz_to_rgb."""
        X, Y, Z = self.lab_to_xyz(L, a, b, illuminant=illuminant)
        r, g, b = self.xyz_to_rgb(X, Y, Z, out_255=out_255)
        return r, g, b

    def calculate_k_s(self, reflectance):
        """Calculate Kubelka-Munk function from reflectance."""
        R = np.array(reflectance) / 100.0  # Convert to 0-1 range
        # Avoid division by zero
        R = np.clip(R, 0.01, 0.99)
        k_s = (1 - R)**2 / (2 * R)
        return k_s


class ColorScience(ColorScienceBase):
    """Comprehensive spectral color calculator for different measurement modes."""
    
    # Chromatic adaptation matrices
    _CAT_MATRICES = {
        "bradford": np.array([
            [ 0.8951,  0.2664, -0.1614],
            [-0.7502,  1.7135,  0.0367],
            [ 0.0389, -0.0685,  1.0296]
        ]),
        "cat02": np.array([
            [ 0.7328,  0.4296, -0.1624],
            [-0.7036,  1.6975,  0.0061],
            [ 0.0030,  0.0136,  0.9834]
        ]),
        # Classic von Kries (Hunt–Pointer–Estevez) cone model
        "kries": np.array([
            [ 0.4002,  0.7075, -0.0807],
            [-0.2280,  1.1500,  0.0612],
            [ 0.0000,  0.0000,  0.9184]
        ])
    }
    
    def __init__(self, wavelengths=None, load=True):
        self.wavelengths = wavelengths
        self._data_loader = SpectrumDataLoader(wavelengths=wavelengths)
        if load:
            self._data_loader.load_reference_data()
    
    def upsample_interpolate(self, X, Xp, Yp):
        """Interpolates low-resolution data (Xp, Yp) onto a new high-resolution X grid."""
        X  = np.array(X, dtype=float)
        Xp = np.array(Xp, dtype=float)
        Yp = np.array(Yp, dtype=float)
        Y = np.interp(X, Xp, Yp)
        return Y

    def spectrum_to_xyz(self, spd, wavelengths=None, illuminant="D65/10"):
        """Convert a spectral power distribution to CIE XYZ tristimulus values."""
        
        if self.wavelengths or self.wavelengths == wavelengths:
            wavelengths = np.array(self.wavelengths)
            cmf = self._data_loader.get_observer(observer=illuminant)
            illuminant = self._data_loader.get_illuminant(illuminant=illuminant) if illuminant is not None else None
        elif wavelengths:
            cmf = self._data_loader.get_observer(wavelengths, observer=illuminant)
            spd = self.upsample_interpolate(cmf["wavelengths"], wavelengths, spd)
            wavelengths = np.array(cmf["wavelengths"])
            illuminant = self._data_loader.get_illuminant(wavelengths, illuminant=illuminant) if illuminant is not None else None
        else:
            raise Exception("wavelengths missing!")

        if len(wavelengths) != len(spd):
            raise Exception("wavelengths and spd lengths must match")

        spd = np.array(spd) / 100
        cmf_x = np.array(cmf["x_bar"])
        cmf_y = np.array(cmf["y_bar"])
        cmf_z = np.array(cmf["z_bar"])
        
        # Calculate wavelength interval (assuming uniform spacing)
        if len(wavelengths) > 1:
            delta_lambda = wavelengths[1] - wavelengths[0]
        else:
            delta_lambda = 1.0
        
        # Case 1: Reflective object (illuminant provided)
        if illuminant is not None:
            illuminant = np.array(illuminant["values"])
            k = 100.0 / np.sum(illuminant * cmf_y * delta_lambda)
            X = k * np.sum(illuminant * spd * cmf_x * delta_lambda)
            Y = k * np.sum(illuminant * spd * cmf_y * delta_lambda)
            Z = k * np.sum(illuminant * spd * cmf_z * delta_lambda)
        # Case 2: Emissive spectrum (no illuminant)
        else:
            k = 100.0 / np.sum(spd * cmf_y * delta_lambda)
            X = k * np.sum(spd * cmf_x * delta_lambda)
            Y = k * np.sum(spd * cmf_y * delta_lambda)
            Z = k * np.sum(spd * cmf_z * delta_lambda)

        return float(X), float(Y), float(Z)

    def adapt_xyz(self, X, Y, Z, Ws, Wd, method="bradford"):
        """Adapt XYZ from source white Ws to destination white Wd."""
        method = method.lower()
        if method not in self._CAT_MATRICES:
            raise ValueError(f"Unknown adaptation method '{method}'. "
                            "Use 'bradford', 'cat02', or 'kries'.")

        M = self._CAT_MATRICES[method]
        M_inv = np.linalg.inv(M)

        XYZ = np.array([X, Y, Z])
        src_cone = M @ Ws
        dst_cone = M @ Wd
        XYZ_cone = M @ XYZ

        # Von Kries scaling
        scale = dst_cone / src_cone
        adapted_cone = XYZ_cone * scale

        # Convert back to XYZ
        XYZ_adapted = M_inv @ adapted_cone
        return float(XYZ_adapted[0]), float(XYZ_adapted[1]), float(XYZ_adapted[2])

    def xyz_to_lab(self, X, Y, Z, illuminant=WhitePoint.D65_10):
        """Convert CIE XYZ to CIE LAB color space."""
        if illuminant is None:
            Xn, Yn, Zn = WhitePoint.D65_10
        elif isinstance(illuminant, (tuple, list)):
            Xn, Yn, Zn = illuminant
        else:
            raise ValueError("reference_white must be a tuple of (Xn, Yn, Zn)")
        
        # Normalize by reference white
        xr = X / Xn
        yr = Y / Yn
        zr = Z / Zn
        
        # Apply the f(t) function
        def f(t):
            delta = 6/29
            if t > delta**3:
                return np.cbrt(t)
            else:
                return t / (3 * delta**2) + 4/29
        
        def f_vectorized(t):
            delta = 6/29
            return np.where(t > delta**3, 
                        np.cbrt(t), 
                        t / (3 * delta**2) + 4/29)
        
        if isinstance(xr, np.ndarray):
            fx = f_vectorized(xr)
            fy = f_vectorized(yr)
            fz = f_vectorized(zr)
        else:
            fx = f(xr)
            fy = f(yr)
            fz = f(zr)
        
        # Calculate LAB values
        L = 116 * fy - 16
        a = 500 * (fx - fy)
        b = 200 * (fy - fz)
        
        return float(L), float(a), float(b)

    def xyz_to_rgb(self, X, Y, Z, out_255=True):
        """Convert CIE XYZ (D65) to sRGB."""
        xyz = np.array([X, Y, Z], dtype=float)

        # XYZ → sRGB matrix, D65
        M_inv = np.array([
            [ 3.2404542, -1.5371385, -0.4985314],
            [-0.9692660,  1.8760108,  0.0415560],
            [ 0.0556434, -0.2040259,  1.0572252]
        ])

        rgb_lin = M_inv @ xyz

        # Gamma correction
        def gamma(c):
            return np.where(c <= 0.0031308,
                            12.92 * c,
                            1.055 * (c ** (1 / 2.4)) - 0.055)

        rgb = gamma(rgb_lin)
        rgb = np.clip(rgb, 0, 1)

        if out_255:
            rgb = (rgb * 255).round().astype(int)
        return tuple(float(i) for i in rgb)

    def lab_to_xyz(self, L, a, b, illuminant=WhitePoint.D65_10):
        """Convert CIE LAB to CIE XYZ color space."""
        if illuminant is None:
            Xn, Yn, Zn = WhitePoint.D65_10
        elif isinstance(illuminant, (tuple, list)):
            Xn, Yn, Zn = illuminant
        else:
            raise ValueError("illuminant must be (Xn,Yn,Zn) tuple")

        def f_inv(ft):
            delta = 6/29
            return np.where(
                ft > delta,
                ft**3,
                3 * delta**2 * (ft - 4/29)
            )

        fy = (L + 16) / 116
        fx = fy + (a / 500)
        fz = fy - (b / 200)

        xr = f_inv(fx)
        yr = f_inv(fy)
        zr = f_inv(fz)

        X = xr * Xn
        Y = yr * Yn
        Z = zr * Zn

        return float(X), float(Y), float(Z)

    def rgb_to_xyz(self, r, g, b):
        """Convert sRGB (0–255 or 0–1) to CIE XYZ (D65)."""
        rgb = np.array([r, g, b], dtype=float)
        if rgb.max() > 1.0:
            rgb /= 255.0

        def inv_gamma(c):
            return np.where(c <= 0.04045,
                            c / 12.92,
                            ((c + 0.055) / 1.055) ** 2.4)

        rgb_lin = inv_gamma(rgb)

        M = np.array([
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041]
        ])

        X, Y, Z = M @ rgb_lin
        return float(X), float(Y), float(Z)

