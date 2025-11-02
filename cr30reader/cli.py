#!/usr/bin/env python3
"""
CR30Reader Command Line Interface

A command-line tool for reading color charts with the CR30 colorimeter.
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import time

from .driver import CR30Reader
from .argyll import TIReader, TIWriter, TIFile
from .utils import FileUtils, ColorUtils


class CR30CLI:
    """Command-line interface for CR30Reader."""
    
    def __init__(self):
        self.reader: Optional[CR30Reader] = None
        self.ti_reader = TIReader()
        self.ti_writer = TIWriter()
    
    async def connect(self, port: str, baudrate: int = 19200, verbose: bool = False):
        """Connect to the CR30 device."""
        self.reader = CR30Reader(port=port, baudrate=baudrate, verbose=verbose)
        await self.reader.connect()
        print(f"Connected to CR30 on {port}")
        print(f"Device: {self.reader.name} {self.reader.model}")
        print(f"Serial: {self.reader.serial_number}")
        print(f"Firmware: {self.reader.fw_version}")
    
    async def disconnect(self):
        """Disconnect from the device."""
        if self.reader:
            await self.reader.disconnect()
            print("Disconnected from CR30")
    
    async def calibrate(self, white: bool = False):
        """Perform calibration."""
        if not self.reader:
            raise RuntimeError("Not connected to device")
        
        cal_type = "white" if white else "black"
        print(f"Performing {cal_type} calibration...")
        print(f"Place device on {cal_type} calibration tile and press Enter")
        input()
        
        result = await self.reader.calibrate(white=white)
        if result["success"]:
            print(f"{cal_type.capitalize()} calibration successful!")
        else:
            print(f"{cal_type.capitalize()} calibration failed!")
            sys.exit(1)
    
    async def measure_single(self, output_file: Optional[str] = None, 
                           format: str = "json", wait: float = 30) -> Dict[str, Any]:
        """Measure a single color patch."""
        if not self.reader:
            raise RuntimeError("Not connected to device")
        
        print("Place device on sample and press button...")
        result = await self.reader.get_measurement_result(wait=wait)
        
        data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "xyz": result.xyz,
            "lab": result.lab,
            "rgb": result.rgb,
            "spd": result.spd,
            "wavelengths": result.wavelengths
        }
        
        if output_file:
            if format == "json":
                FileUtils.save_json(data, output_file)
            elif format == "csv":
                FileUtils.save_csv([data], output_file)
            print(f"Results saved to {output_file}")
        
        return data
    
    async def read_chart(self, chart_file: str, output_file: Optional[str] = None,
                        auto: bool = False, delay: float = 0.5) -> Dict[str, Any]:
        """
        Read a color chart from TI2 or CHT file.
        
        Note: Chart reading workflow (device measurements) must be handled externally.
        This method only handles file I/O operations.
        """
        if not self.reader:
            raise RuntimeError("Not connected to device")
        
        print(f"Reading chart: {chart_file}")
        
        # Determine file type and read
        path = Path(chart_file)
        if path.suffix.lower() == '.ti2':
            chart_data = self.ti_reader.read_ti2(chart_file)
            file_type = 'TI2'
        elif path.suffix.lower() == '.cht':
            chart_data = self.ti_reader.read_cht(chart_file)
            file_type = 'CHT'
            # For CHT files, just read and return structure
            # Measurement workflow must be handled externally
            print(f"Loaded CHT file with {len(chart_data.patches)} patches")
            print("Note: Chart measurement workflow must be handled externally")
            return {
                "chart_file": chart_file,
                "file_type": file_type,
                "patches_count": len(chart_data.patches),
                "message": "CHT file loaded. Measurement workflow must be handled externally."
            }
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}. Expected .ti2 or .cht")
        
        # Create summary for TI2 files
        measurements = []
        for patch in chart_data.patches:
            if patch.xyz:
                # Calculate LAB if not present and reader is available
                lab = patch.lab
                if not lab and patch.xyz and self.reader:
                    lab = self.reader.science.xyz_to_lab(*patch.xyz)
                    patch.lab = lab
                
                measurements.append({
                    "name": patch.name,
                    "xyz": patch.xyz,
                    "lab": lab,
                })
        
        summary = {
            "chart_file": chart_file,
            "file_type": file_type,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "patches_measured": len(measurements),
            "measurements": measurements
        }
        
        if output_file:
            # Write as TI3 (calculate LAB if needed)
            if all(patch.xyz for patch in chart_data.patches):
                # Ensure all patches have LAB values
                if self.reader:
                    for patch in chart_data.patches:
                        if patch.xyz and not patch.lab:
                            patch.lab = self.reader.science.xyz_to_lab(*patch.xyz)
                
                chart_data.file_type = 'TI3'
                self.ti_writer.write_ti3(chart_data, output_file)
                print(f"Chart results saved to {output_file} as TI3")
            else:
                # Save as JSON if no XYZ data
                FileUtils.save_json(summary, output_file)
                print(f"Chart results saved to {output_file} as JSON")
        
        return summary
    
    async def batch_measure(self, count: int, output_file: Optional[str] = None,
                          delay: float = 1.0) -> List[Dict[str, Any]]:
        """Perform batch measurements."""
        if not self.reader:
            raise RuntimeError("Not connected to device")
        
        print(f"Performing {count} measurements...")
        measurements = []
        
        for i in range(count):
            print(f"Measurement {i+1}/{count}")
            print("Place device on sample and press button...")
            
            result = await self.reader.get_measurement_result(wait=30)
            measurement = {
                "number": i + 1,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "xyz": result.xyz,
                "lab": result.lab,
                "rgb": result.rgb,
                "spd": result.spd,
                "wavelengths": result.wavelengths
            }
            measurements.append(measurement)
            
            if i < count - 1:
                print(f"Waiting {delay} seconds...")
                await asyncio.sleep(delay)
        
        print(measurements)

        if output_file:
            if format == "json":
                FileUtils.save_json(measurements, output_file)
            elif format == "csv":
                FileUtils.save_csv(measurements, output_file)
            print(f"Batch measurements saved to {output_file}")
        
        return measurements
    
    def print_measurement(self, data: Dict[str, Any]):
        """Print measurement results in a formatted way."""
        print("\n" + "="*50)
        print("MEASUREMENT RESULTS")
        print("="*50)
        
        if "xyz" in data:
            print(f"XYZ: {data['xyz'][0]:.3f}, {data['xyz'][1]:.3f}, {data['xyz'][2]:.3f}")
        
        if "lab" in data:
            print(f"LAB: {data['lab'][0]:.3f}, {data['lab'][1]:.3f}, {data['lab'][2]:.3f}")
        
        if "rgb" in data:
            print(f"RGB: {data['rgb'][0]}, {data['rgb'][1]}, {data['rgb'][2]}")
            print(f"Hex: {ColorUtils.rgb_to_hex(data['rgb'])}")
        
        if "spd" in data and data["spd"]:
            print(f"SPD: {len(data['spd'])} wavelength bands")
            print(f"Range: {data['wavelengths'][0]:.0f}nm - {data['wavelengths'][-1]:.0f}nm")
        
        print("="*50)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="CR30Reader - Color Chart Reader for CR30 Colorimeter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Connect and measure a single sample
  cr30reader --port COM3 measure --output sample.json
  
  # Read a color chart
  cr30reader --port COM3 chart --input ColorChecker24.ti2 --output results.ti3
  
  # Perform batch measurements
  cr30reader --port COM3 batch --count 5 --output batch.json
  
  # Calibrate device
  cr30reader --port COM3 calibrate --white
        """
    )
    
    # Global options
    parser.add_argument("--port", default="COM3", help="Serial port (default: COM3)")
    parser.add_argument("--baudrate", type=int, default=19200, help="Baud rate (default: 19200)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--format", choices=["json", "csv"], default="csv", help="Output format")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Measure command
    measure_parser = subparsers.add_parser("measure", help="Measure a single color patch")
    measure_parser.add_argument("--wait", type=float, default=30, help="Wait time for button press (seconds)")
    
    # Chart command
    chart_parser = subparsers.add_parser("chart", help="Read a color chart (TI2 or CHT file)")
    chart_parser.add_argument("--input", "-i", required=True, help="Input TI2 or CHT chart file")
    chart_parser.add_argument("--auto", action="store_true", help="Automatic measurement (no user interaction)")
    chart_parser.add_argument("--delay", type=float, default=0.5, help="Delay between measurements (seconds)")
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Perform batch measurements")
    batch_parser.add_argument("--count", type=int, required=True, help="Number of measurements")
    batch_parser.add_argument("--delay", type=float, default=1.0, help="Delay between measurements (seconds)")
    
    # Calibrate command
    calibrate_parser = subparsers.add_parser("calibrate", help="Calibrate the device")
    calibrate_parser.add_argument("--white", action="store_true", help="White calibration (default: black)")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show device information")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = CR30CLI()
    
    try:
        # Connect to device (except for info command)
        if args.command != "info":
            await cli.connect(args.port, args.baudrate, args.verbose)
        
        if args.command == "measure":
            data = await cli.measure_single(args.output, args.format, args.wait)
            cli.print_measurement(data)
        
        elif args.command == "chart":
            if not Path(args.input).exists():
                print(f"Error: Chart file not found: {args.input}")
                sys.exit(1)
            summary = await cli.read_chart(args.input, args.output, args.auto, args.delay)
            print(f"Chart reading complete: {summary['patches_measured']} patches measured")
        
        elif args.command == "batch":
            measurements = await cli.batch_measure(args.count, args.output, args.delay)
            print(f"Batch measurement complete: {len(measurements)} measurements")
        
        elif args.command == "calibrate":
            await cli.calibrate(args.white)
        
        elif args.command == "info":
            await cli.connect(args.port, args.baudrate, args.verbose)
            print(f"Device: {cli.reader.name} {cli.reader.model}")
            print(f"Serial: {cli.reader.serial_number}")
            print(f"Firmware: {cli.reader.fw_version}")
            print(f"Build: {cli.reader.fw_build}")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        if cli.reader:
            await cli.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

