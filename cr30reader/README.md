# CR30Reader - Color Chart Reader for CR30 Colorimeter

A Python application for reading color charts using the CR30 colorimeter device, designed for printer characterization and color management workflows.

## Features

- **CR30 Protocol Support**: Complete reverse-engineered protocol for CR30 colorimeter communication
- **Color Science**: Accurate spectral-to-color space conversion (XYZ, LAB, RGB)
- **Chart Reading**: Support for TI1/TI2/TI3 file formats compatible with ArgyllCMS
- **Printer Characterization**: Tools for creating ICC profiles and color correction
- **Async Communication**: Non-blocking serial communication with the device

## Architecture

The application is organized into separate modules for maintainability:

- **`protocol/`**: CR30 device communication and protocol handling
- **`color_science/`**: Color space conversions and spectral calculations  
- **`driver/`**: High-level device interface and measurement orchestration
- **`argyll/`**: ArgyllCMS file format support (TI2/CHT read, TI3 write)
- **`utils/`**: Common utilities and helpers

## Installation

### Using Poetry (recommended):

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Using pip:

```bash
pip install -r requirements.txt
```

### Note on tkinter:
On Linux systems, you may need to install the `python3-tk` package:
```bash
sudo apt-get install python3-tk  # Debian/Ubuntu
sudo yum install python3-tkinter  # RHEL/CentOS
```

## Usage

### Running the Application

With Poetry:
```bash
poetry run run      # Run GUI application
poetry run test     # Run tests
```

Or using Python:
```bash
python -m cr30reader gui   # Run GUI
python -m cr30reader cli    # Run CLI
```

### Basic Measurement
```python
from cr30reader.driver import CR30Reader

reader = CR30Reader(port='COM3')
await reader.connect()
xyz = await reader.measure()
print(f"XYZ: {xyz}")
await reader.disconnect()
```

### Chart Reading
```python
from cr30reader.driver import CR30Reader
from cr30reader.argyll import TIReader, TIWriter

reader = CR30Reader(port='COM3')
ti_reader = TIReader()
ti_writer = TIWriter()

# Read a TI2 or CHT chart file
ti_file = ti_reader.read_ti2("ColorChecker24.ti2")

# After measurements, write as TI3
ti_writer.write_ti3(ti_file, "results.ti3")
```

### Color Space Conversion
```python
from cr30reader.color_science import ColorScience

cs = ColorScience()
xyz = (72.94, 77.43, 83.01)
lab = cs.xyz_to_lab(*xyz)
rgb = cs.xyz_to_rgb(*xyz)
```

## Requirements

- Python 3.8+
- pyserial-asyncio
- numpy
- matplotlib (for visualization)

## License

MIT License
