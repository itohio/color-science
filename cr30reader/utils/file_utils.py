"""
File Utility Functions

Common file-related utility functions.
"""

import os
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import datetime


class FileUtils:
    """Utility functions for file operations."""
    
    @staticmethod
    def ensure_directory(path: str) -> None:
        """Ensure a directory exists, creating it if necessary."""
        Path(path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_timestamp() -> str:
        """Get a timestamp string for file naming."""
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def save_json(data: Dict[str, Any], file_path: str) -> None:
        """Save data to a JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """Load data from a JSON file."""
        with open(file_path, 'r') as f:
            return json.load(f)
    
    @staticmethod
    def save_csv(data: List[Dict[str, Any]], file_path: str) -> None:
        """Save data to a CSV file."""
        if not data:
            return
        
        fieldnames = data[0].keys()
        with open(file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    @staticmethod
    def load_csv(file_path: str) -> List[Dict[str, Any]]:
        """Load data from a CSV file."""
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    @staticmethod
    def backup_file(file_path: str) -> str:
        """Create a backup of a file with timestamp."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        timestamp = FileUtils.get_timestamp()
        backup_path = path.with_suffix(f".{timestamp}{path.suffix}")
        
        import shutil
        shutil.copy2(file_path, backup_path)
        return str(backup_path)
    
    @staticmethod
    def find_files(pattern: str, directory: str = ".") -> List[str]:
        """Find files matching a pattern in a directory."""
        import glob
        return glob.glob(os.path.join(directory, pattern))
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """Get the size of a file in bytes."""
        return os.path.getsize(file_path)
    
    @staticmethod
    def get_file_modified_time(file_path: str) -> datetime.datetime:
        """Get the modification time of a file."""
        timestamp = os.path.getmtime(file_path)
        return datetime.datetime.fromtimestamp(timestamp)
    
    @staticmethod
    def is_file_newer(file1: str, file2: str) -> bool:
        """Check if file1 is newer than file2."""
        time1 = FileUtils.get_file_modified_time(file1)
        time2 = FileUtils.get_file_modified_time(file2)
        return time1 > time2
    
    @staticmethod
    def create_measurement_log(measurements: List[Dict[str, Any]], 
                             output_path: str) -> None:
        """Create a measurement log file."""
        log_data = {
            "timestamp": FileUtils.get_timestamp(),
            "measurements": measurements,
            "count": len(measurements)
        }
        FileUtils.save_json(log_data, output_path)
    
    @staticmethod
    def export_measurements_csv(measurements: List[Dict[str, Any]], 
                              output_path: str) -> None:
        """Export measurements to CSV format."""
        FileUtils.save_csv(measurements, output_path)
    
    @staticmethod
    def create_summary_report(measurements: List[Dict[str, Any]], 
                            output_path: str) -> None:
        """Create a summary report of measurements."""
        if not measurements:
            return
        
        # Calculate statistics
        xyz_values = [m.get('xyz', [0, 0, 0]) for m in measurements if 'xyz' in m]
        lab_values = [m.get('lab', [0, 0, 0]) for m in measurements if 'lab' in m]
        
        report = {
            "timestamp": FileUtils.get_timestamp(),
            "total_measurements": len(measurements),
            "xyz_statistics": {
                "min": [min(xyz[i] for xyz in xyz_values) for i in range(3)],
                "max": [max(xyz[i] for xyz in xyz_values) for i in range(3)],
                "mean": [sum(xyz[i] for xyz in xyz_values) / len(xyz_values) for i in range(3)]
            } if xyz_values else {},
            "lab_statistics": {
                "min": [min(lab[i] for lab in lab_values) for i in range(3)],
                "max": [max(lab[i] for lab in lab_values) for i in range(3)],
                "mean": [sum(lab[i] for lab in lab_values) / len(lab_values) for i in range(3)]
            } if lab_values else {},
            "measurements": measurements
        }
        
        FileUtils.save_json(report, output_path)
    
    @staticmethod
    def validate_ti_file(file_path: str) -> bool:
        """Validate a TI file format."""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Check for TI file markers
            if not any(line.strip().startswith('CTI') for line in lines[:10]):
                return False
            
            # Check for required sections
            has_data_format = any('BEGIN_DATA_FORMAT' in line for line in lines)
            has_data = any('BEGIN_DATA' in line for line in lines)
            
            return has_data_format and has_data
        except Exception:
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """Get information about a file."""
        path = Path(file_path)
        if not path.exists():
            return {"exists": False}
        
        stat = path.stat()
        return {
            "exists": True,
            "size": stat.st_size,
            "modified": datetime.datetime.fromtimestamp(stat.st_mtime),
            "created": datetime.datetime.fromtimestamp(stat.st_ctime),
            "extension": path.suffix,
            "name": path.name,
            "stem": path.stem
        }

