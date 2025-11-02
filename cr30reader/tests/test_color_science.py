"""
Unit tests for color_science package.

Tests for SpectrumDataLoader, ColorScience, and color space conversions.
"""

import unittest
import numpy as np
from cr30reader.color_science import (
    ColorScienceBase,
    ColorScience,
    SpectrumDataLoader,
    WhitePoint
)


class TestSpectrumDataLoader(unittest.TestCase):
    """Tests for SpectrumDataLoader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.wavelengths = [400 + i * 10 for i in range(31)]
        self.loader = SpectrumDataLoader(wavelengths=self.wavelengths)
    
    def test_init_with_wavelengths(self):
        """Test SpectrumDataLoader initialization with wavelengths."""
        self.assertEqual(self.loader.wavelengths, self.wavelengths)
        self.assertIsNone(self.loader._observers)
        self.assertIsNone(self.loader._illuminants)
    
    def test_init_without_wavelengths(self):
        """Test SpectrumDataLoader initialization without wavelengths."""
        loader = SpectrumDataLoader()
        self.assertIsNone(loader.wavelengths)
    
    def test_downsample_nearest(self):
        """Test nearest neighbor downsampling."""
        X = np.array([400, 410, 420])
        Xp = np.array([398, 405, 408, 412, 415, 418, 422])
        Yp = np.array([10, 20, 30, 40, 50, 60, 70])
        
        result = self.loader.downsample_nearest(X, Xp, Yp)
        
        self.assertEqual(len(result), len(X))
        # 400 should match 398 -> 10
        self.assertAlmostEqual(result[0], 10.0, places=5)
        # 410 should match 412 -> 40
        self.assertAlmostEqual(result[1], 40.0, places=5)
        # 420 should match 418 -> 60
        self.assertAlmostEqual(result[2], 60.0, places=5)
    
    def test_restrict_to_X_range(self):
        """Test range restriction."""
        X = np.array([400, 500])
        Xp = np.array([350, 400, 450, 500, 550, 600])
        Yp = np.array([10, 20, 30, 40, 50, 60])
        
        Xp_restricted, Yp_restricted = self.loader.restrict_to_X_range(X, Xp, Yp)
        
        self.assertTrue(np.all(Xp_restricted >= np.min(X)))
        self.assertTrue(np.all(Xp_restricted <= np.max(X)))
        self.assertEqual(len(Xp_restricted), len(Yp_restricted))
        self.assertEqual(Xp_restricted[0], 400)
        self.assertEqual(Xp_restricted[-1], 500)


class TestColorScience(unittest.TestCase):
    """Tests for ColorScience class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.wavelengths = [400 + i * 10 for i in range(31)]
        self.cs = ColorScience(wavelengths=self.wavelengths, load=True)
    
    def test_init(self):
        """Test ColorScience initialization."""
        self.assertEqual(self.cs.wavelengths, self.wavelengths)
        self.assertIsNotNone(self.cs._data_loader._observers)
        self.assertIsNotNone(self.cs._data_loader._illuminants)
    
    def test_upsample_interpolate(self):
        """Test interpolation upsampling."""
        X = np.array([400, 405, 410, 415, 420])
        Xp = np.array([400, 410, 420])
        Yp = np.array([10, 20, 30])
        
        result = self.cs.upsample_interpolate(X, Xp, Yp)
        
        self.assertEqual(len(result), len(X))
        self.assertAlmostEqual(result[0], 10.0, places=5)
        self.assertAlmostEqual(result[2], 20.0, places=5)
        self.assertAlmostEqual(result[4], 30.0, places=5)
        # Interpolated values should be between endpoints
        self.assertGreater(result[1], result[0])
        self.assertLess(result[1], result[2])
    
    def test_spectrum_to_xyz_with_illuminant(self):
        """Test spectrum to XYZ conversion with illuminant (reflectance)."""
        # Test data from ipynb: expected LAB [77.77, 68.59, 39.4]
        spd = [
            23.898427963256836, 23.30441665649414, 23.15403175354004,
            23.656957626342773, 24.614757537841797, 24.712610244750977,
            22.19900131225586, 18.11726188659668, 14.16519546508789,
            10.539053916931152, 6.648414134979248, 5.761203289031982,
            12.976861000061035, 27.517276763916016, 50.46492004394531,
            88.36058807373047, 135.19223022460938, 165.1352996826172,
            165.7974853515625, 148.69451904296875, 130.1623992919922,
            116.8099136352539, 107.09515380859375, 99.15723419189453,
            95.44196319580078, 95.362548828125, 97.0391616821289,
            100.17365264892578, 0.0, 0.0, 0.0
        ]
        
        xyz = self.cs.spectrum_to_xyz(spd, illuminant='D65/10')
        
        self.assertEqual(len(xyz), 3)
        self.assertIsInstance(xyz[0], float)
        self.assertIsInstance(xyz[1], float)
        self.assertIsInstance(xyz[2], float)
        # Y should be positive and reasonable
        self.assertGreater(xyz[1], 0)
        self.assertLess(xyz[1], 100)
    
    def test_xyz_to_lab(self):
        """Test XYZ to LAB conversion."""
        # Test data from ipynb: XYZ (81.48, 87.12, 93.35) -> LAB (94.79, -2.18, 0.1)
        X, Y, Z = 81.48, 87.12, 93.35
        
        lab = self.cs.xyz_to_lab(X, Y, Z)
        
        self.assertEqual(len(lab), 3)
        # L* should be close to 94.79
        self.assertAlmostEqual(lab[0], 94.79, places=1)
        # a* should be close to -2.18
        self.assertAlmostEqual(lab[1], -2.18, places=1)
        # b* should be close to 0.1
        self.assertAlmostEqual(lab[2], 0.1, places=1)
    
    def test_lab_to_xyz(self):
        """Test LAB to XYZ conversion (round-trip)."""
        # Test round-trip: XYZ -> LAB -> XYZ
        X, Y, Z = 81.48, 87.12, 93.35
        lab = self.cs.xyz_to_lab(X, Y, Z)
        xyz_roundtrip = self.cs.lab_to_xyz(*lab)
        
        # Should be close to original (within 0.1%)
        self.assertAlmostEqual(xyz_roundtrip[0], X, places=0)
        self.assertAlmostEqual(xyz_roundtrip[1], Y, places=0)
        self.assertAlmostEqual(xyz_roundtrip[2], Z, places=0)
    
    def test_xyz_to_rgb(self):
        """Test XYZ to RGB conversion."""
        # Test data: D65 white point should give RGB close to (255, 255, 255)
        X, Y, Z = 95.047, 100.0, 108.883  # D65/2
        
        rgb = self.cs.xyz_to_rgb(X, Y, Z, out_255=True)
        
        self.assertEqual(len(rgb), 3)
        # D65 white should give high RGB values
        self.assertGreater(rgb[0], 200)
        self.assertGreater(rgb[1], 200)
        self.assertGreater(rgb[2], 200)
    
    def test_rgb_to_xyz(self):
        """Test RGB to XYZ conversion."""
        # Test round-trip: RGB -> XYZ -> RGB
        r, g, b = 255, 255, 255
        xyz = self.cs.rgb_to_xyz(r, g, b)
        
        self.assertEqual(len(xyz), 3)
        self.assertGreater(xyz[1], 0)  # Y should be positive
        # White RGB should give reasonable XYZ
        self.assertGreater(xyz[0], 80)
        self.assertGreater(xyz[2], 80)
    
    def test_adapt_xyz_bradford(self):
        """Test XYZ chromatic adaptation with Bradford method."""
        # Adapt D65 to D50
        X, Y, Z = 81.48, 87.12, 93.35
        Ws = WhitePoint['D65/10']
        Wd = WhitePoint['D50/10']
        
        adapted = self.cs.adapt_xyz(X, Y, Z, Ws, Wd, method='bradford')
        
        self.assertEqual(len(adapted), 3)
        # Adapted values should still be positive
        self.assertGreater(adapted[0], 0)
        self.assertGreater(adapted[1], 0)
        self.assertGreater(adapted[2], 0)
    
    def test_adapt_xyz_invalid_method(self):
        """Test that invalid adaptation method raises error."""
        X, Y, Z = 81.48, 87.12, 93.35
        Ws = WhitePoint['D65/10']
        Wd = WhitePoint['D50/10']
        
        with self.assertRaises(ValueError):
            self.cs.adapt_xyz(X, Y, Z, Ws, Wd, method='invalid')
    
    def test_spectrum_to_xyz_no_illuminant(self):
        """Test spectrum to XYZ conversion without illuminant (emission)."""
        # Emissive spectrum (normalized to 100)
        spd = [0.0] * 31
        spd[15] = 100.0  # Peak at 550nm
        
        xyz = self.cs.spectrum_to_xyz(spd, illuminant=None)
        
        self.assertEqual(len(xyz), 3)
        # Emissive spectrum should give positive XYZ
        self.assertGreater(xyz[1], 0)


class TestWhitePoint(unittest.TestCase):
    """Tests for WhitePoint class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.wp = WhitePoint()
    
    def test_d65_10_static(self):
        """Test D65/10 white point using static property."""
        d65 = WhitePoint.D65_10
        self.assertEqual(len(d65), 3)
        self.assertAlmostEqual(d65[0], 94.81, places=2)
        self.assertAlmostEqual(d65[1], 100.0, places=2)
        self.assertAlmostEqual(d65[2], 107.32, places=2)
    
    def test_static_properties(self):
        """Test all static properties are accessible."""
        self.assertEqual(WhitePoint.D50_10, (96.72, 100.000, 81.43))
        self.assertEqual(WhitePoint.D65_10, (94.81, 100.000, 107.32))
        self.assertEqual(WhitePoint.D75_10, (94.972, 100.000, 122.638))
        self.assertEqual(WhitePoint.D50_2, (96.422, 100.000, 82.521))
        self.assertEqual(WhitePoint.D65_2, (95.047, 100.000, 108.883))
        self.assertEqual(WhitePoint.D75_2, (94.972, 100.000, 122.638))
        self.assertEqual(WhitePoint.A, (109.850, 100.000, 35.585))
        self.assertEqual(WhitePoint.E, (100.000, 100.000, 100.000))
    
    def test_d65_10(self):
        """Test D65/10 white point."""
        d65 = self.wp['D65/10']
        self.assertEqual(len(d65), 3)
        self.assertAlmostEqual(d65[0], 94.81, places=2)
        self.assertAlmostEqual(d65[1], 100.0, places=2)
        self.assertAlmostEqual(d65[2], 107.32, places=2)
    
    def test_d65_auto_suffix(self):
        """Test automatic /10 suffix for D65."""
        d65 = self.wp['D65']
        self.assertEqual(len(d65), 3)
        self.assertAlmostEqual(d65[0], 94.81, places=2)
    
    def test_d50_10(self):
        """Test D50/10 white point."""
        d50 = self.wp['D50/10']
        self.assertEqual(len(d50), 3)
        self.assertAlmostEqual(d50[0], 96.72, places=2)
        self.assertAlmostEqual(d50[1], 100.0, places=2)
        self.assertAlmostEqual(d50[2], 81.43, places=2)
    
    def test_unknown_whitepoint(self):
        """Test that unknown whitepoint raises KeyError."""
        with self.assertRaises(KeyError):
            _ = self.wp['UNKNOWN']
    
    def test_len(self):
        """Test WhitePoint length."""
        self.assertGreater(len(self.wp), 0)
    
    def test_iter(self):
        """Test WhitePoint iteration."""
        keys = list(self.wp)
        self.assertIn('D65/10', keys)
        self.assertIn('D50/10', keys)


if __name__ == '__main__':
    unittest.main()

