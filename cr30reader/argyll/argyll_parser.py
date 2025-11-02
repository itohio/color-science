"""
ArgyllCMS File Format Parser

Provides read/write support for ArgyllCMS file formats:
- Read: TI2 (measurement data), CHT (chart definition)
- Write: TI3 (complete chart data)
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TIPatch:
    """Represents a single color patch in a TI file."""
    
    name: str
    xyz: Optional[Tuple[float, float, float]] = None
    lab: Optional[Tuple[float, float, float]] = None
    
    def __str__(self):
        return f"TIPatch(name='{self.name}', xyz={self.xyz}, lab={self.lab})"


@dataclass
class TIFile:
    """Represents a TI2 or TI3 file."""
    
    patches: List[TIPatch]
    metadata: Dict[str, Any]
    file_type: str  # 'TI2' or 'TI3'
    
    def __str__(self):
        return f"TIFile(type='{self.file_type}', patches={len(self.patches)})"


@dataclass
class CHTPatch:
    """Represents a single color patch in a CHT file."""
    
    name: str
    expected_xyz: Optional[Tuple[float, float, float]] = None
    position: Optional[Tuple[float, float]] = None
    
    def __str__(self):
        return f"CHTPatch(name='{self.name}', expected_xyz={self.expected_xyz})"


@dataclass
class CHTFile:
    """Represents a CHT chart definition file."""
    
    patches: List[CHTPatch]
    metadata: Dict[str, Any]
    box_shrink: Optional[float] = None
    ref_rotation: Optional[float] = None
    
    def __str__(self):
        return f"CHTFile(patches={len(self.patches)}, box_shrink={self.box_shrink})"


class TIFormat:
    """Shared format utilities for TI file operations."""
    
    TI2_HEADER = "CTI2"
    TI3_HEADER = "CTI3"
    CHT_BOXES_PREFIX = "BOXES"
    CHT_EXPECTED_PREFIX = "EXPECTED"
    
    @staticmethod
    def validate_ti2(file_path: str) -> bool:
        """
        Validate that a file is a valid TI2 file.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            True if valid TI2 file, False otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            with open(path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                return first_line == TIFormat.TI2_HEADER
        except Exception:
            return False
    
    @staticmethod
    def validate_cht(file_path: str) -> bool:
        """
        Validate that a file is a valid CHT file.
        
        Args:
            file_path: Path to file to validate
            
        Returns:
            True if valid CHT file, False otherwise
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            with open(path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                # CHT files typically start with BOXES or EXPECTED XYZ
                return (first_line.startswith(TIFormat.CHT_BOXES_PREFIX) or 
                        first_line.startswith(TIFormat.CHT_EXPECTED_PREFIX))
        except Exception:
            return False
    
    @staticmethod
    def detect_format(file_path: str) -> Optional[str]:
        """
        Detect file format from file path and content.
        
        Args:
            file_path: Path to file
            
        Returns:
            'TI2', 'CHT', or None if unknown
        """
        path = Path(file_path)
        
        # Try extension first
        suffix = path.suffix.lower()
        if suffix == '.ti2':
            return 'TI2'
        elif suffix == '.cht':
            return 'CHT'
        
        # Try content-based detection
        if TIFormat.validate_ti2(file_path):
            return 'TI2'
        elif TIFormat.validate_cht(file_path):
            return 'CHT'
        
        return None


class TIReader:
    """Reader for TI2 and CHT file formats."""
    
    def __init__(self):
        """Initialize the TI reader."""
        pass
    
    def read_ti2(self, file_path: str) -> TIFile:
        """
        Read a TI2 file (measurement data).
        
        Args:
            file_path: Path to TI2 file
            
        Returns:
            TIFile object with patches and metadata
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"TI2 file not found: {file_path}")
        
        if not TIFormat.validate_ti2(file_path):
            raise ValueError(f"Invalid TI2 file format: {file_path}")
        
        patches = []
        metadata = {}
        
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        data_format_fields = []
        
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith(TIFormat.TI2_HEADER):
                # Valid TI2 file header
                pass
            elif line.startswith('NUMBER_OF_SETS'):
                metadata['number_of_sets'] = int(line.split()[1])
            elif line.startswith('NUMBER_OF_FIELDS'):
                metadata['number_of_fields'] = int(line.split()[1])
            elif line.startswith('BEGIN_DATA_FORMAT'):
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('END_DATA_FORMAT'):
                    field = lines[i].strip()
                    if field and not field.startswith('#'):
                        data_format_fields.append(field)
                    i += 1
                metadata['data_format'] = data_format_fields
            elif line.startswith('BEGIN_DATA'):
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('END_DATA'):
                    data_line = lines[i].strip()
                    if data_line and not data_line.startswith('#'):
                        parts = data_line.split()
                        if len(parts) >= 4:
                            name = parts[0]
                            try:
                                xyz = (float(parts[1]), float(parts[2]), float(parts[3]))
                                patches.append(TIPatch(name=name, xyz=xyz))
                            except (ValueError, IndexError) as e:
                                raise ValueError(f"Invalid TI2 data line: {data_line}") from e
                    i += 1
                break
            
            i += 1
        
        return TIFile(patches=patches, metadata=metadata, file_type='TI2')
    
    def read_cht(self, file_path: str) -> CHTFile:
        """
        Read a CHT file (chart definition with expected values).
        
        Args:
            file_path: Path to CHT file
            
        Returns:
            CHTFile object with patches and metadata
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CHT file not found: {file_path}")
        
        if not TIFormat.validate_cht(file_path):
            raise ValueError(f"Invalid CHT file format: {file_path}")
        
        patches = []
        metadata = {}
        box_shrink = None
        ref_rotation = None
        
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        i = 0
        in_expected_xyz = False
        count = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith(TIFormat.CHT_BOXES_PREFIX):
                metadata['boxes'] = int(line.split()[1])
            elif line.startswith('BOX_SHRINK'):
                box_shrink = float(line.split()[1])
            elif line.startswith('REF_ROTATION'):
                ref_rotation = float(line.split()[1])
            elif line.startswith('XLIST'):
                # Skip XLIST section
                count_list = int(line.split()[1])
                for _ in range(count_list):
                    i += 1
                    if i >= len(lines):
                        break
            elif line.startswith('YLIST'):
                # Skip YLIST section
                count_list = int(line.split()[1])
                for _ in range(count_list):
                    i += 1
                    if i >= len(lines):
                        break
            elif line.startswith('EXPECTED XYZ'):
                in_expected_xyz = True
                count = int(line.split()[2])
                metadata['expected_patch_count'] = count
                i += 1
                continue
            
            if in_expected_xyz:
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 4:
                        name = parts[0]
                        try:
                            xyz = (float(parts[1]), float(parts[2]), float(parts[3]))
                            patches.append(CHTPatch(name=name, expected_xyz=xyz))
                            # Stop when we've read all expected patches
                            if len(patches) >= count:
                                in_expected_xyz = False
                                break
                        except (ValueError, IndexError) as e:
                            raise ValueError(f"Invalid CHT expected XYZ line: {line}") from e
                    elif line.strip() == '':
                        # Empty line might indicate end of expected XYZ section
                        if len(patches) >= count:
                            in_expected_xyz = False
            
            i += 1
        
        return CHTFile(
            patches=patches,
            metadata=metadata,
            box_shrink=box_shrink,
            ref_rotation=ref_rotation
        )


class TIWriter:
    """Writer for TI3 file format."""
    
    def __init__(self):
        """Initialize the TI writer."""
        pass
    
    def write_ti3(self, ti_file: TIFile, output_path: str) -> None:
        """
        Write a TI3 file (complete chart data).
        
        Args:
            ti_file: TIFile object with patches and measurements
            output_path: Path for output TI3 file
            
        Raises:
            ValueError: If TIFile doesn't have required data
        """
        if not ti_file.patches:
            raise ValueError("TIFile must contain at least one patch")
        
        # Check that patches have XYZ and LAB data
        for patch in ti_file.patches:
            if not patch.xyz:
                raise ValueError(f"Patch {patch.name} missing XYZ data")
            if not patch.lab:
                raise ValueError(f"Patch {patch.name} missing LAB data")
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(f"{TIFormat.TI3_HEADER}\n")
            f.write("NUMBER_OF_SETS 1\n")
            f.write("NUMBER_OF_FIELDS 7\n")
            f.write("BEGIN_DATA_FORMAT\n")
            f.write("SAMPLE_ID XYZ_X XYZ_Y XYZ_Z LAB_L LAB_A LAB_B\n")
            f.write("END_DATA_FORMAT\n")
            f.write("BEGIN_DATA\n")
            
            for patch in ti_file.patches:
                f.write(f"{patch.name} "
                       f"{patch.xyz[0]:.6f} {patch.xyz[1]:.6f} {patch.xyz[2]:.6f} "
                       f"{patch.lab[0]:.6f} {patch.lab[1]:.6f} {patch.lab[2]:.6f}\n")
            
            f.write("END_DATA\n")


# Backwards compatibility - create a combined class that delegates to TIReader and TIWriter
class ArgyllParser:
    """
    Backwards compatibility class that combines TIReader and TIWriter.
    
    For new code, use TIReader and TIWriter separately.
    """
    
    def __init__(self):
        """Initialize the parser."""
        self._reader = TIReader()
        self._writer = TIWriter()
    
    def read_ti2(self, file_path: str) -> TIFile:
        """Read a TI2 file."""
        return self._reader.read_ti2(file_path)
    
    def read_cht(self, file_path: str) -> CHTFile:
        """Read a CHT file."""
        return self._reader.read_cht(file_path)
    
    def write_ti3(self, ti_file: TIFile, output_path: str) -> None:
        """Write a TI3 file."""
        self._writer.write_ti3(ti_file, output_path)
    
    def validate_ti2(self, file_path: str) -> bool:
        """Validate a TI2 file."""
        return TIFormat.validate_ti2(file_path)
    
    def validate_cht(self, file_path: str) -> bool:
        """Validate a CHT file."""
        return TIFormat.validate_cht(file_path)
