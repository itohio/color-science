"""
Unit tests for argyll package.

Tests for TIFormat, TIReader, TIWriter, and dataclass construction.
"""

import unittest
import tempfile
import os
from pathlib import Path
from cr30reader.argyll import (
    TIFormat,
    TIReader,
    TIWriter,
    TIPatch,
    TIFile,
    CHTPatch,
    CHTFile
)


class TestDataclassConstruction(unittest.TestCase):
    """Tests for easy dataclass construction."""
    
    def test_tipatch_construction(self):
        """Test TIPatch can be easily constructed."""
        # Minimal construction
        patch1 = TIPatch(name="A1")
        self.assertEqual(patch1.name, "A1")
        self.assertIsNone(patch1.xyz)
        self.assertIsNone(patch1.lab)
        
        # With XYZ
        patch2 = TIPatch(name="A2", xyz=(10.0, 20.0, 30.0))
        self.assertEqual(patch2.name, "A2")
        self.assertEqual(patch2.xyz, (10.0, 20.0, 30.0))
        self.assertIsNone(patch2.lab)
        
        # With both XYZ and LAB
        patch3 = TIPatch(
            name="A3",
            xyz=(72.94, 77.43, 83.01),
            lab=(93.45, 0.52, -0.32)
        )
        self.assertEqual(patch3.name, "A3")
        self.assertEqual(patch3.xyz, (72.94, 77.43, 83.01))
        self.assertEqual(patch3.lab, (93.45, 0.52, -0.32))
    
    def test_tifile_construction(self):
        """Test TIFile can be easily constructed."""
        patches = [
            TIPatch(name="1", xyz=(10.0, 20.0, 30.0)),
            TIPatch(name="2", xyz=(40.0, 50.0, 60.0))
        ]
        ti_file = TIFile(
            patches=patches,
            metadata={"number_of_sets": 2},
            file_type="TI2"
        )
        self.assertEqual(len(ti_file.patches), 2)
        self.assertEqual(ti_file.file_type, "TI2")
        self.assertEqual(ti_file.metadata["number_of_sets"], 2)
    
    def test_chtpatch_construction(self):
        """Test CHTPatch can be easily constructed."""
        # Minimal
        patch1 = CHTPatch(name="A1")
        self.assertEqual(patch1.name, "A1")
        self.assertIsNone(patch1.expected_xyz)
        self.assertIsNone(patch1.position)
        
        # With expected XYZ
        patch2 = CHTPatch(
            name="A2",
            expected_xyz=(73.91, 77.10, 61.07)
        )
        self.assertEqual(patch2.name, "A2")
        self.assertEqual(patch2.expected_xyz, (73.91, 77.10, 61.07))
        
        # With position
        patch3 = CHTPatch(
            name="A3",
            expected_xyz=(46.79, 48.66, 39.28),
            position=(88.5, 88.5)
        )
        self.assertEqual(patch3.position, (88.5, 88.5))
    
    def test_chtfile_construction(self):
        """Test CHTFile can be easily constructed."""
        patches = [
            CHTPatch(name="A1", expected_xyz=(73.91, 77.10, 61.07)),
            CHTPatch(name="A2", expected_xyz=(46.79, 48.66, 39.28))
        ]
        cht_file = CHTFile(
            patches=patches,
            metadata={"boxes": 25},
            box_shrink=8.0,
            ref_rotation=0.0
        )
        self.assertEqual(len(cht_file.patches), 2)
        self.assertEqual(cht_file.box_shrink, 8.0)
        self.assertEqual(cht_file.ref_rotation, 0.0)


class TestTIFormat(unittest.TestCase):
    """Tests for TIFormat validation and detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_validate_ti2_valid(self):
        """Test validation of valid TI2 file."""
        file_path = os.path.join(self.temp_dir, "test.ti2")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("CTI2\n")
            f.write("NUMBER_OF_SETS 1\n")
        
        self.assertTrue(TIFormat.validate_ti2(file_path))
    
    def test_validate_ti2_invalid(self):
        """Test validation of invalid TI2 file."""
        file_path = os.path.join(self.temp_dir, "test.ti2")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("CTI3\n")  # Wrong header
        
        self.assertFalse(TIFormat.validate_ti2(file_path))
    
    def test_validate_ti2_nonexistent(self):
        """Test validation of nonexistent file."""
        self.assertFalse(TIFormat.validate_ti2("nonexistent.ti2"))
    
    def test_validate_cht_valid(self):
        """Test validation of valid CHT file."""
        file_path = os.path.join(self.temp_dir, "test.cht")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("BOXES 25\n")
            f.write("EXPECTED XYZ 24\n")
        
        self.assertTrue(TIFormat.validate_cht(file_path))
    
    def test_validate_cht_invalid(self):
        """Test validation of invalid CHT file."""
        file_path = os.path.join(self.temp_dir, "test.cht")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("INVALID\n")
        
        self.assertFalse(TIFormat.validate_cht(file_path))
    
    def test_detect_format_ti2(self):
        """Test format detection for TI2."""
        file_path = os.path.join(self.temp_dir, "test.ti2")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("CTI2\n")
        
        format_type = TIFormat.detect_format(file_path)
        self.assertEqual(format_type, "TI2")
    
    def test_detect_format_cht(self):
        """Test format detection for CHT."""
        file_path = os.path.join(self.temp_dir, "test.cht")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("BOXES 25\n")
        
        format_type = TIFormat.detect_format(file_path)
        self.assertEqual(format_type, "CHT")


class TestTIReader(unittest.TestCase):
    """Tests for TIReader."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reader = TIReader()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_sample_ti2(self, file_path: str):
        """Create a sample TI2 file for testing."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("CTI2\n")
            f.write("NUMBER_OF_SETS 2\n")
            f.write("NUMBER_OF_FIELDS 4\n")
            f.write("BEGIN_DATA_FORMAT\n")
            f.write("SAMPLE_ID XYZ_X XYZ_Y XYZ_Z\n")
            f.write("END_DATA_FORMAT\n")
            f.write("BEGIN_DATA\n")
            f.write("1 10.0 20.0 30.0\n")
            f.write("2 40.0 50.0 60.0\n")
            f.write("END_DATA\n")
    
    def create_sample_cht(self, file_path: str):
        """Create a sample CHT file for testing."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("BOXES 25\n")
            f.write("BOX_SHRINK 8.0\n")
            f.write("REF_ROTATION 0.0\n")
            f.write("EXPECTED XYZ 2\n")
            f.write("A1 73.91 77.10 61.07\n")
            f.write("A2 46.79 48.66 39.28\n")
    
    def test_read_ti2(self):
        """Test reading a TI2 file."""
        file_path = os.path.join(self.temp_dir, "test.ti2")
        self.create_sample_ti2(file_path)
        
        ti_file = self.reader.read_ti2(file_path)
        
        self.assertEqual(ti_file.file_type, "TI2")
        self.assertEqual(len(ti_file.patches), 2)
        self.assertEqual(ti_file.patches[0].name, "1")
        self.assertEqual(ti_file.patches[0].xyz, (10.0, 20.0, 30.0))
        self.assertEqual(ti_file.patches[1].name, "2")
        self.assertEqual(ti_file.patches[1].xyz, (40.0, 50.0, 60.0))
        self.assertEqual(ti_file.metadata["number_of_sets"], 2)
        self.assertEqual(ti_file.metadata["number_of_fields"], 4)
    
    def test_read_ti2_nonexistent(self):
        """Test reading nonexistent TI2 file."""
        with self.assertRaises(FileNotFoundError):
            self.reader.read_ti2("nonexistent.ti2")
    
    def test_read_ti2_invalid_format(self):
        """Test reading invalid TI2 file."""
        file_path = os.path.join(self.temp_dir, "test.ti2")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("INVALID\n")
        
        with self.assertRaises(ValueError):
            self.reader.read_ti2(file_path)
    
    def test_read_ti2_with_comments(self):
        """Test reading TI2 file with comments."""
        file_path = os.path.join(self.temp_dir, "test.ti2")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("CTI2\n")
            f.write("# This is a comment\n")
            f.write("NUMBER_OF_SETS 1\n")
            f.write("BEGIN_DATA_FORMAT\n")
            f.write("SAMPLE_ID XYZ_X XYZ_Y XYZ_Z\n")
            f.write("# Another comment\n")
            f.write("END_DATA_FORMAT\n")
            f.write("BEGIN_DATA\n")
            f.write("# Comment in data section\n")
            f.write("1 10.0 20.0 30.0\n")
            f.write("END_DATA\n")
        
        ti_file = self.reader.read_ti2(file_path)
        self.assertEqual(len(ti_file.patches), 1)
        self.assertEqual(ti_file.patches[0].name, "1")
    
    def test_read_cht(self):
        """Test reading a CHT file."""
        file_path = os.path.join(self.temp_dir, "test.cht")
        self.create_sample_cht(file_path)
        
        cht_file = self.reader.read_cht(file_path)
        
        self.assertEqual(len(cht_file.patches), 2)
        self.assertEqual(cht_file.patches[0].name, "A1")
        self.assertEqual(cht_file.patches[0].expected_xyz, (73.91, 77.10, 61.07))
        self.assertEqual(cht_file.patches[1].name, "A2")
        self.assertEqual(cht_file.patches[1].expected_xyz, (46.79, 48.66, 39.28))
        self.assertEqual(cht_file.box_shrink, 8.0)
        self.assertEqual(cht_file.ref_rotation, 0.0)
        self.assertEqual(cht_file.metadata["boxes"], 25)
        self.assertEqual(cht_file.metadata["expected_patch_count"], 2)
    
    def test_read_cht_nonexistent(self):
        """Test reading nonexistent CHT file."""
        with self.assertRaises(FileNotFoundError):
            self.reader.read_cht("nonexistent.cht")
    
    def test_read_cht_invalid_format(self):
        """Test reading invalid CHT file."""
        file_path = os.path.join(self.temp_dir, "test.cht")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("INVALID\n")
        
        with self.assertRaises(ValueError):
            self.reader.read_cht(file_path)
    
    def test_read_cht_with_xlist_ylist(self):
        """Test reading CHT file with XLIST and YLIST sections."""
        file_path = os.path.join(self.temp_dir, "test.cht")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("BOXES 25\n")
            f.write("XLIST 4\n")
            f.write("11.0 1.0 1.0\n")
            f.write("99.5 1.0 1.0\n")
            f.write("113.0 1.0 1.0\n")
            f.write("201.5 1.0 1.0\n")
            f.write("YLIST 2\n")
            f.write("11.0 1.0 1.0\n")
            f.write("99.5 1.0 1.0\n")
            f.write("EXPECTED XYZ 1\n")
            f.write("A1 73.91 77.10 61.07\n")
        
        cht_file = self.reader.read_cht(file_path)
        self.assertEqual(len(cht_file.patches), 1)
        self.assertEqual(cht_file.patches[0].name, "A1")


class TestTIWriter(unittest.TestCase):
    """Tests for TIWriter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.writer = TIWriter()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_write_ti3(self):
        """Test writing a TI3 file."""
        patches = [
            TIPatch(name="1", xyz=(10.0, 20.0, 30.0), lab=(50.0, 1.0, 2.0)),
            TIPatch(name="2", xyz=(40.0, 50.0, 60.0), lab=(60.0, 3.0, 4.0))
        ]
        ti_file = TIFile(
            patches=patches,
            metadata={},
            file_type="TI3"
        )
        
        output_path = os.path.join(self.temp_dir, "output.ti3")
        self.writer.write_ti3(ti_file, output_path)
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_path))
        
        # Read and verify contents
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("CTI3", content)
        self.assertIn("NUMBER_OF_SETS 1", content)
        self.assertIn("NUMBER_OF_FIELDS 7", content)
        self.assertIn("SAMPLE_ID XYZ_X XYZ_Y XYZ_Z LAB_L LAB_A LAB_B", content)
        self.assertIn("1 10.000000 20.000000 30.000000 50.000000 1.000000 2.000000", content)
        self.assertIn("2 40.000000 50.000000 60.000000 60.000000 3.000000 4.000000", content)
    
    def test_write_ti3_empty_patches(self):
        """Test writing TI3 file with no patches raises error."""
        ti_file = TIFile(patches=[], metadata={}, file_type="TI3")
        
        output_path = os.path.join(self.temp_dir, "output.ti3")
        with self.assertRaises(ValueError) as context:
            self.writer.write_ti3(ti_file, output_path)
        
        self.assertIn("at least one patch", str(context.exception))
    
    def test_write_ti3_missing_xyz(self):
        """Test writing TI3 file with missing XYZ raises error."""
        patches = [TIPatch(name="1", lab=(50.0, 1.0, 2.0))]
        ti_file = TIFile(patches=patches, metadata={}, file_type="TI3")
        
        output_path = os.path.join(self.temp_dir, "output.ti3")
        with self.assertRaises(ValueError) as context:
            self.writer.write_ti3(ti_file, output_path)
        
        self.assertIn("missing XYZ data", str(context.exception))
    
    def test_write_ti3_missing_lab(self):
        """Test writing TI3 file with missing LAB raises error."""
        patches = [TIPatch(name="1", xyz=(10.0, 20.0, 30.0))]
        ti_file = TIFile(patches=patches, metadata={}, file_type="TI3")
        
        output_path = os.path.join(self.temp_dir, "output.ti3")
        with self.assertRaises(ValueError) as context:
            self.writer.write_ti3(ti_file, output_path)
        
        self.assertIn("missing LAB data", str(context.exception))
    
    def test_write_ti3_creates_directory(self):
        """Test that write_ti3 creates parent directories if needed."""
        subdir = os.path.join(self.temp_dir, "subdir")
        output_path = os.path.join(subdir, "output.ti3")
        
        patches = [
            TIPatch(name="1", xyz=(10.0, 20.0, 30.0), lab=(50.0, 1.0, 2.0))
        ]
        ti_file = TIFile(patches=patches, metadata={}, file_type="TI3")
        
        self.writer.write_ti3(ti_file, output_path)
        
        self.assertTrue(os.path.exists(output_path))


class TestRoundTrip(unittest.TestCase):
    """Tests for round-trip operations (read, modify, write, read)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reader = TIReader()
        self.writer = TIWriter()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_ti2_to_ti3_round_trip(self):
        """Test reading TI2, adding LAB, writing TI3, then reading it back."""
        # Create TI2 file
        ti2_path = os.path.join(self.temp_dir, "input.ti2")
        with open(ti2_path, 'w', encoding='utf-8') as f:
            f.write("CTI2\n")
            f.write("NUMBER_OF_SETS 2\n")
            f.write("NUMBER_OF_FIELDS 4\n")
            f.write("BEGIN_DATA_FORMAT\n")
            f.write("SAMPLE_ID XYZ_X XYZ_Y XYZ_Z\n")
            f.write("END_DATA_FORMAT\n")
            f.write("BEGIN_DATA\n")
            f.write("1 10.0 20.0 30.0\n")
            f.write("2 40.0 50.0 60.0\n")
            f.write("END_DATA\n")
        
        # Read TI2
        ti_file = self.reader.read_ti2(ti2_path)
        self.assertEqual(len(ti_file.patches), 2)
        
        # Add LAB values (simulating color science calculation)
        ti_file.patches[0].lab = (50.0, 1.0, 2.0)
        ti_file.patches[1].lab = (60.0, 3.0, 4.0)
        ti_file.file_type = "TI3"
        
        # Write TI3
        ti3_path = os.path.join(self.temp_dir, "output.ti3")
        self.writer.write_ti3(ti_file, ti3_path)
        
        # Verify TI3 can be read (basic format check)
        self.assertTrue(os.path.exists(ti3_path))
        with open(ti3_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("CTI3", content)
            self.assertIn("1 10.000000 20.000000 30.000000 50.000000 1.000000 2.000000", content)
    
    def test_programmatic_construction_and_write(self):
        """Test constructing TIFile programmatically and writing it."""
        # Construct patches easily
        patches = [
            TIPatch(
                name="A1",
                xyz=(73.91, 77.10, 61.07),
                lab=(93.45, 0.52, -0.32)
            ),
            TIPatch(
                name="A2",
                xyz=(46.79, 48.66, 39.28),
                lab=(75.23, -2.45, 5.67)
            ),
        ]
        
        # Construct TIFile
        ti_file = TIFile(
            patches=patches,
            metadata={"number_of_sets": 2},
            file_type="TI3"
        )
        
        # Write it
        output_path = os.path.join(self.temp_dir, "constructed.ti3")
        self.writer.write_ti3(ti_file, output_path)
        
        # Verify
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("A1", content)
            self.assertIn("A2", content)
            self.assertIn("73.910000", content)
            self.assertIn("93.450000", content)


class TestExampleFiles(unittest.TestCase):
    """Tests using real example files from the project."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.reader = TIReader()
        self.writer = TIWriter()
        self.temp_dir = tempfile.mkdtemp()
        
        # Try to find example files relative to cr30reader
        self.base_path = Path(__file__).parent.parent.parent
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_read_example_ti2_if_exists(self):
        """Test reading an example TI2 file if it exists."""
        # Look for ColorChecker24.ti2 in parent directories
        example_paths = [
            self.base_path / "ColorChecker24" / "original" / "ColorChecker24.ti2",
            self.base_path / "SpyderCheckr24" / "front.ti2",
        ]
        
        for example_path in example_paths:
            if example_path.exists():
                ti_file = self.reader.read_ti2(str(example_path))
                self.assertGreater(len(ti_file.patches), 0)
                self.assertEqual(ti_file.file_type, "TI2")
                # Verify patches have XYZ data
                for patch in ti_file.patches:
                    if patch.xyz:
                        self.assertEqual(len(patch.xyz), 3)
                return
        
        # If no example file found, skip test
        self.skipTest("No example TI2 file found")
    
    def test_read_example_cht_if_exists(self):
        """Test reading an example CHT file if it exists."""
        example_paths = [
            self.base_path / "SpyderCheckr24" / "front.cht",
            self.base_path / "SpyderCheckr24" / "SpyderChecker24.cht",
        ]
        
        for example_path in example_paths:
            if example_path.exists():
                cht_file = self.reader.read_cht(str(example_path))
                self.assertGreater(len(cht_file.patches), 0)
                # Verify patches have expected XYZ
                for patch in cht_file.patches:
                    if patch.expected_xyz:
                        self.assertEqual(len(patch.expected_xyz), 3)
                return
        
        # If no example file found, skip test
        self.skipTest("No example CHT file found")


if __name__ == '__main__':
    unittest.main()

