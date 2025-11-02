# Unit Tests for cr30reader

This directory contains unit tests for the `cr30reader` package.

## Test Structure

- `test_color_science.py` - Tests for color science functionality:
  - `SpectrumDataLoader` - Data loading and downsampling
  - `ColorScience` - Color space conversions (XYZ, LAB, RGB)
  - `WhitePoint` - White point references
  
- `test_protocol.py` - Tests for protocol package:
  - `CR30Packet` - Packet structure and validation
  - `PacketBuilder` - Packet construction
  - `PacketParser` - Packet parsing and SPD chunk accumulation
  - Integration tests using real example data from `reverse-engineer-c30/*.ipynb`

- `test_argyll.py` - Tests for argyll package:
  - `TIFormat` - Format validation and detection
  - `TIReader` - TI2 and CHT file reading
  - `TIWriter` - TI3 file writing
  - Dataclass construction (TIPatch, TIFile, CHTPatch, CHTFile)
  - Round-trip operations (read, modify, write, read)
  - Tests using example files from the project

## Running Tests

### Using pytest (recommended):

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_color_science.py -v
pytest tests/test_argyll.py -v

# Run with coverage
pytest tests/ --cov=cr30reader --cov-report=html

# Run specific test class
pytest tests/test_protocol.py::TestCR30Packet -v
```

### Using unittest:

```bash
# Run all tests
python -m unittest discover tests/

# Run specific test file
python -m unittest tests.test_color_science

# Run specific test
python -m unittest tests.test_color_science.TestColorScience.test_xyz_to_lab
```

### Using Docker (as per repository rules):

```bash
# Run tests in Docker container
docker run --rm -v $(pwd):/app -w /app python:3.11 pytest tests/ -v
```

## Test Data

The protocol tests use example packet data extracted from:
- `reverse-engineer-c30/protocol.ipynb` - Communication examples
- `reverse-engineer-c30/packets.ipynb` - Packet structure examples

These include real device communication packets and SPD measurement data.

The argyll tests use example files from:
- `ColorChecker24/original/ColorChecker24.ti2` - Example TI2 files
- `SpyderCheckr24/front.cht` - Example CHT files

These include real ArgyllCMS chart files for validation.

## Test Coverage

The tests cover:

1. **Color Science:**
   - Data loading and downsampling
   - Spectrum to XYZ conversion
   - XYZ to LAB/RGB conversions
   - Color space round-trips
   - Chromatic adaptation
   - White point handling

2. **Protocol:**
   - Packet creation and parsing
   - Checksum calculation and verification
   - Device info parsing
   - Measurement header parsing
   - SPD chunk accumulation
   - Stateful parser operations

3. **Argyll:**
   - TI2 file reading with various formats
   - CHT file reading with expected XYZ data
   - TI3 file writing with XYZ and LAB data
   - Format validation and detection
   - Easy dataclass construction
   - Round-trip operations (TI2 → TI3)
   - Error handling for invalid files

## Notes

- Tests follow table-driven test patterns where appropriate
- Error handling is tested for invalid inputs
- Round-trip conversions verify correctness
- Real packet examples ensure compatibility with actual device communication

