#!/usr/bin/env python3
"""
CR30Reader GUI Application

A graphical user interface for the CR30 colorimeter using tkinter.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import asyncio
import threading
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np

from .driver import CR30Reader
from .argyll import TIReader, TIWriter, TIFile, CHTFile
from .utils import FileUtils, ColorUtils


class CR30GUI:
    """Main GUI application for CR30Reader."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CR30Reader - Color Chart Reader")
        self.root.geometry("1200x800")
        
        # Device connection
        self.reader: Optional[CR30Reader] = None
        self.ti_reader = TIReader()
        self.ti_writer = TIWriter()
        
        # Measurement data
        self.current_measurement: Optional[Dict[str, Any]] = None
        self.measurement_history: List[Dict[str, Any]] = []
        self.current_chart_data = None
        
        # GUI components
        self.setup_gui()
        
        # Async event loop
        self.loop = None
        self.loop_thread = None
        
    def setup_gui(self):
        """Setup the GUI components."""
        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.setup_connection_tab()
        self.setup_measurement_tab()
        self.setup_chart_tab()
        self.setup_visualization_tab()
        self.setup_history_tab()
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_connection_tab(self):
        """Setup the connection tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Connection")
        
        # Connection settings
        settings_frame = ttk.LabelFrame(frame, text="Connection Settings")
        settings_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(settings_frame, text="Port:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.port_var = tk.StringVar(value="COM3")
        port_entry = ttk.Entry(settings_frame, textvariable=self.port_var, width=20)
        port_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(settings_frame, text="Baud Rate:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.baudrate_var = tk.StringVar(value="19200")
        baudrate_combo = ttk.Combobox(settings_frame, textvariable=self.baudrate_var, 
                                     values=["9600", "19200", "38400", "115200"], width=10)
        baudrate_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Connection buttons
        button_frame = ttk.Frame(settings_frame)
        button_frame.grid(row=1, column=0, columnspan=4, pady=10)
        
        self.connect_btn = ttk.Button(button_frame, text="Connect", command=self.connect_device)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = ttk.Button(button_frame, text="Disconnect", command=self.disconnect_device, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        self.calibrate_black_btn = ttk.Button(button_frame, text="Calibrate Black", command=self.calibrate_black, state=tk.DISABLED)
        self.calibrate_black_btn.pack(side=tk.LEFT, padx=5)
        
        self.calibrate_white_btn = ttk.Button(button_frame, text="Calibrate White", command=self.calibrate_white, state=tk.DISABLED)
        self.calibrate_white_btn.pack(side=tk.LEFT, padx=5)
        
        # Device info
        info_frame = ttk.LabelFrame(frame, text="Device Information")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.device_info = scrolledtext.ScrolledText(info_frame, height=10, state=tk.DISABLED)
        self.device_info.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_measurement_tab(self):
        """Setup the measurement tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Measurement")
        
        # Measurement controls
        control_frame = ttk.LabelFrame(frame, text="Measurement Controls")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.measure_btn = ttk.Button(control_frame, text="Measure Color", command=self.measure_color, state=tk.DISABLED)
        self.measure_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.measure_avg_btn = ttk.Button(control_frame, text="Measure Average (3x)", command=self.measure_average, state=tk.DISABLED)
        self.measure_avg_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.save_measurement_btn = ttk.Button(control_frame, text="Save Measurement", command=self.save_measurement, state=tk.DISABLED)
        self.save_measurement_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Measurement results
        results_frame = ttk.LabelFrame(frame, text="Measurement Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for results
        results_notebook = ttk.Notebook(results_frame)
        results_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Color values tab
        values_frame = ttk.Frame(results_notebook)
        results_notebook.add(values_frame, text="Color Values")
        
        self.color_values = scrolledtext.ScrolledText(values_frame, height=15, state=tk.DISABLED)
        self.color_values.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Spectral data tab
        spectral_frame = ttk.Frame(results_notebook)
        results_notebook.add(spectral_frame, text="Spectral Data")
        
        self.spectral_data = scrolledtext.ScrolledText(spectral_frame, height=15, state=tk.DISABLED)
        self.spectral_data.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_chart_tab(self):
        """Setup the chart reading tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Chart Reading")
        
        # Chart controls
        control_frame = ttk.LabelFrame(frame, text="Chart Reading Controls")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(control_frame, text="Chart File:").pack(side=tk.LEFT, padx=5)
        self.chart_file_var = tk.StringVar()
        chart_entry = ttk.Entry(control_frame, textvariable=self.chart_file_var, width=50)
        chart_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Browse", command=self.browse_chart_file).pack(side=tk.LEFT, padx=5)
        
        self.read_chart_btn = ttk.Button(control_frame, text="Read Chart", command=self.read_chart, state=tk.DISABLED)
        self.read_chart_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_ti3_btn = ttk.Button(control_frame, text="Save as TI3", command=self.save_as_ti3, state=tk.DISABLED)
        self.save_ti3_btn.pack(side=tk.LEFT, padx=5)
        
        # Chart progress
        progress_frame = ttk.Frame(control_frame)
        progress_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(progress_frame, text="Progress:").pack(side=tk.LEFT)
        self.progress_var = tk.StringVar(value="0/0")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack(side=tk.LEFT, padx=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, padx=5)
        
        # Chart results
        results_frame = ttk.LabelFrame(frame, text="Chart Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chart_results = scrolledtext.ScrolledText(results_frame, height=20, state=tk.DISABLED)
        self.chart_results.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def setup_visualization_tab(self):
        """Setup the visualization tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Visualization")
        
        # Create matplotlib figure
        self.fig = Figure(figsize=(12, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Visualization controls
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(control_frame, text="Plot Spectrum", command=self.plot_spectrum).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Plot Chromaticity", command=self.plot_chromaticity).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Clear Plot", command=self.clear_plot).pack(side=tk.LEFT, padx=5)
    
    def setup_history_tab(self):
        """Setup the measurement history tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="History")
        
        # History controls
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Clear History", command=self.clear_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Save History", command=self.save_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Load History", command=self.load_history).pack(side=tk.LEFT, padx=5)
        
        # History list
        list_frame = ttk.LabelFrame(frame, text="Measurement History")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview for history
        columns = ("Timestamp", "XYZ", "LAB", "RGB")
        self.history_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=150)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.history_tree.bind("<<TreeviewSelect>>", self.on_history_select)
    
    def start_async_loop(self):
        """Start the async event loop in a separate thread."""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        
        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()
    
    def run_async(self, coro):
        """Run an async coroutine in the GUI thread."""
        if not self.loop:
            self.start_async_loop()
        
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()
    
    def connect_device(self):
        """Connect to the CR30 device."""
        try:
            port = self.port_var.get()
            baudrate = int(self.baudrate_var.get())
            
            self.reader = CR30Reader(port=port, baudrate=baudrate, verbose=True)
            self.run_async(self.reader.connect())
            
            # Update UI
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self.calibrate_black_btn.config(state=tk.NORMAL)
            self.calibrate_white_btn.config(state=tk.NORMAL)
            self.measure_btn.config(state=tk.NORMAL)
            self.measure_avg_btn.config(state=tk.NORMAL)
            self.read_chart_btn.config(state=tk.NORMAL)
            self.save_ti3_btn.config(state=tk.NORMAL)
            
            # Update device info
            info = f"Device: {self.reader.name} {self.reader.model}\n"
            info += f"Serial: {self.reader.serial_number}\n"
            info += f"Firmware: {self.reader.fw_version}\n"
            info += f"Build: {self.reader.fw_build}\n"
            info += f"Port: {port}\n"
            info += f"Baud Rate: {baudrate}\n"
            
            self.device_info.config(state=tk.NORMAL)
            self.device_info.delete(1.0, tk.END)
            self.device_info.insert(1.0, info)
            self.device_info.config(state=tk.DISABLED)
            
            self.status_var.set("Connected")
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect: {e}")
    
    def disconnect_device(self):
        """Disconnect from the device."""
        try:
            if self.reader:
                self.run_async(self.reader.disconnect())
                self.reader = None
                self.chart_reader = None
            
            # Update UI
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.calibrate_black_btn.config(state=tk.DISABLED)
            self.calibrate_white_btn.config(state=tk.DISABLED)
            self.measure_btn.config(state=tk.DISABLED)
            self.measure_avg_btn.config(state=tk.DISABLED)
            self.read_chart_btn.config(state=tk.DISABLED)
            self.save_ti3_btn.config(state=tk.DISABLED)
            
            self.device_info.config(state=tk.NORMAL)
            self.device_info.delete(1.0, tk.END)
            self.device_info.config(state=tk.DISABLED)
            
            self.status_var.set("Disconnected")
            
        except Exception as e:
            messagebox.showerror("Disconnect Error", f"Failed to disconnect: {e}")
    
    def calibrate_black(self):
        """Perform black calibration."""
        try:
            self.status_var.set("Performing black calibration...")
            result = self.run_async(self.reader.calibrate_black())
            if result["success"]:
                messagebox.showinfo("Calibration", "Black calibration successful!")
            else:
                messagebox.showerror("Calibration", "Black calibration failed!")
            self.status_var.set("Ready")
        except Exception as e:
            messagebox.showerror("Calibration Error", f"Black calibration failed: {e}")
            self.status_var.set("Ready")
    
    def calibrate_white(self):
        """Perform white calibration."""
        try:
            self.status_var.set("Performing white calibration...")
            result = self.run_async(self.reader.calibrate_white())
            if result["success"]:
                messagebox.showinfo("Calibration", "White calibration successful!")
            else:
                messagebox.showerror("Calibration", "White calibration failed!")
            self.status_var.set("Ready")
        except Exception as e:
            messagebox.showerror("Calibration Error", f"White calibration failed: {e}")
            self.status_var.set("Ready")
    
    def measure_color(self):
        """Measure a single color."""
        try:
            self.status_var.set("Measuring color...")
            result = self.run_async(self.reader.get_measurement_result(wait=30))
            
            self.current_measurement = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "xyz": result.xyz,
                "lab": result.lab,
                "rgb": result.rgb,
                "spd": result.spd,
                "wavelengths": result.wavelengths
            }
            
            self.update_measurement_display()
            self.add_to_history(self.current_measurement)
            self.save_measurement_btn.config(state=tk.NORMAL)
            
            self.status_var.set("Measurement complete")
            
        except Exception as e:
            messagebox.showerror("Measurement Error", f"Measurement failed: {e}")
            self.status_var.set("Ready")
    
    def measure_average(self):
        """Measure average of multiple samples."""
        try:
            self.status_var.set("Measuring average (3 samples)...")
            xyz = self.run_async(self.reader.measure_avg(space='XYZ', count=3, delay=0.5))
            lab = self.reader.science.xyz_to_lab(*xyz)
            rgb = self.reader.science.xyz_to_rgb(*xyz)
            
            self.current_measurement = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "xyz": xyz,
                "lab": lab,
                "rgb": rgb,
                "spd": [],  # No SPD data for average
                "wavelengths": []
            }
            
            self.update_measurement_display()
            self.add_to_history(self.current_measurement)
            self.save_measurement_btn.config(state=tk.NORMAL)
            
            self.status_var.set("Average measurement complete")
            
        except Exception as e:
            messagebox.showerror("Measurement Error", f"Average measurement failed: {e}")
            self.status_var.set("Ready")
    
    def update_measurement_display(self):
        """Update the measurement display."""
        if not self.current_measurement:
            return
        
        # Update color values
        values_text = f"Timestamp: {self.current_measurement['timestamp']}\n\n"
        values_text += f"XYZ: {self.current_measurement['xyz'][0]:.3f}, {self.current_measurement['xyz'][1]:.3f}, {self.current_measurement['xyz'][2]:.3f}\n"
        values_text += f"LAB: {self.current_measurement['lab'][0]:.3f}, {self.current_measurement['lab'][1]:.3f}, {self.current_measurement['lab'][2]:.3f}\n"
        values_text += f"RGB: {self.current_measurement['rgb'][0]}, {self.current_measurement['rgb'][1]}, {self.current_measurement['rgb'][2]}\n"
        values_text += f"Hex: {ColorUtils.rgb_to_hex(self.current_measurement['rgb'])}\n"
        
        self.color_values.config(state=tk.NORMAL)
        self.color_values.delete(1.0, tk.END)
        self.color_values.insert(1.0, values_text)
        self.color_values.config(state=tk.DISABLED)
        
        # Update spectral data
        if self.current_measurement['spd']:
            spectral_text = f"Spectral Power Distribution ({len(self.current_measurement['spd'])} bands)\n\n"
            for i, (wavelength, reflectance) in enumerate(zip(self.current_measurement['wavelengths'], self.current_measurement['spd'])):
                spectral_text += f"{wavelength:.0f}nm: {reflectance:.3f}\n"
        else:
            spectral_text = "No spectral data available"
        
        self.spectral_data.config(state=tk.NORMAL)
        self.spectral_data.delete(1.0, tk.END)
        self.spectral_data.insert(1.0, spectral_text)
        self.spectral_data.config(state=tk.DISABLED)
    
    def add_to_history(self, measurement):
        """Add measurement to history."""
        self.measurement_history.append(measurement)
        
        # Add to treeview
        xyz_str = f"{measurement['xyz'][0]:.2f}, {measurement['xyz'][1]:.2f}, {measurement['xyz'][2]:.2f}"
        lab_str = f"{measurement['lab'][0]:.2f}, {measurement['lab'][1]:.2f}, {measurement['lab'][2]:.2f}"
        rgb_str = f"{measurement['rgb'][0]}, {measurement['rgb'][1]}, {measurement['rgb'][2]}"
        
        self.history_tree.insert("", tk.END, values=(
            measurement['timestamp'],
            xyz_str,
            lab_str,
            rgb_str
        ))
    
    def on_history_select(self, event):
        """Handle history selection."""
        selection = self.history_tree.selection()
        if selection:
            item = self.history_tree.item(selection[0])
            index = self.history_tree.index(selection[0])
            if index < len(self.measurement_history):
                self.current_measurement = self.measurement_history[index]
                self.update_measurement_display()
    
    def save_measurement(self):
        """Save current measurement to file."""
        if not self.current_measurement:
            messagebox.showwarning("No Measurement", "No measurement to save")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                FileUtils.save_json(self.current_measurement, filename)
                messagebox.showinfo("Save", f"Measurement saved to {filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save: {e}")
    
    def browse_chart_file(self):
        """Browse for chart file."""
        filename = filedialog.askopenfilename(
            filetypes=[("TI2 files", "*.ti2"), ("CHT files", "*.cht"), ("All files", "*.*")]
        )
        if filename:
            self.chart_file_var.set(filename)
    
    def read_chart(self):
        """Read a color chart file (TI2 or CHT)."""
        chart_file = self.chart_file_var.get()
        if not chart_file or not Path(chart_file).exists():
            messagebox.showerror("File Error", "Please select a valid chart file")
            return
        
        try:
            self.status_var.set("Reading chart file...")
            path = Path(chart_file)
            
            if path.suffix.lower() == '.ti2':
                chart_data = self.ti_reader.read_ti2(chart_file)
                file_type = 'TI2'
                
                # Display results
                results_text = f"Chart: {chart_file}\n"
                results_text += f"Type: {file_type}\n"
                results_text += f"Patches: {len(chart_data.patches)}\n\n"
                
                for i, patch in enumerate(chart_data.patches):
                    if patch.xyz:
                        lab_str = f"{patch.lab[0]:.3f}, {patch.lab[1]:.3f}, {patch.lab[2]:.3f}" if patch.lab else "N/A"
                        results_text += f"Patch {i+1}: {patch.name}\n"
                        results_text += f"  XYZ: {patch.xyz[0]:.3f}, {patch.xyz[1]:.3f}, {patch.xyz[2]:.3f}\n"
                        results_text += f"  LAB: {lab_str}\n\n"
                
            elif path.suffix.lower() == '.cht':
                chart_data = self.ti_reader.read_cht(chart_file)
                file_type = 'CHT'
                
                # Display results
                results_text = f"Chart: {chart_file}\n"
                results_text += f"Type: {file_type}\n"
                results_text += f"Patches: {len(chart_data.patches)}\n"
                results_text += f"Box Shrink: {chart_data.box_shrink}\n"
                results_text += f"Ref Rotation: {chart_data.ref_rotation}\n\n"
                results_text += "Note: Chart measurement workflow must be handled externally.\n\n"
                
                for i, patch in enumerate(chart_data.patches):
                    if patch.expected_xyz:
                        results_text += f"Patch {i+1}: {patch.name}\n"
                        results_text += f"  Expected XYZ: {patch.expected_xyz[0]:.3f}, {patch.expected_xyz[1]:.3f}, {patch.expected_xyz[2]:.3f}\n\n"
            else:
                messagebox.showerror("File Error", f"Unsupported file format: {path.suffix}. Expected .ti2 or .cht")
                self.status_var.set("Ready")
                return
            
            self.chart_results.config(state=tk.NORMAL)
            self.chart_results.delete(1.0, tk.END)
            self.chart_results.insert(1.0, results_text)
            self.chart_results.config(state=tk.DISABLED)
            
            # Store chart data for saving
            self.current_chart_data = chart_data
            
            self.status_var.set("Chart file reading complete")
            
        except Exception as e:
            messagebox.showerror("Chart Error", f"Chart reading failed: {e}")
            self.status_var.set("Ready")
    
    def save_as_ti3(self):
        """Save current chart data as TI3 file."""
        if not hasattr(self, 'current_chart_data'):
            messagebox.showwarning("No Chart", "Please read a chart file first")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".ti3",
            filetypes=[("TI3 files", "*.ti3"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Convert to TIFile if needed
                if isinstance(self.current_chart_data, CHTFile):
                    messagebox.showwarning("CHT File", "Cannot save CHT file as TI3. Please measure patches first.")
                    return
                
                chart_file = self.current_chart_data
                if not isinstance(chart_file, TIFile):
                    messagebox.showerror("Error", "Invalid chart data type")
                    return
                
                # Ensure all patches have LAB values
                if not all(patch.lab for patch in chart_file.patches if patch.xyz):
                    # Calculate LAB from XYZ
                    for patch in chart_file.patches:
                        if patch.xyz and not patch.lab:
                            patch.lab = self.reader.science.xyz_to_lab(*patch.xyz)
                
                self.ti_writer.write_ti3(chart_file, filename)
                messagebox.showinfo("Save", f"Chart saved to {filename}")
                
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save: {e}")
    
    def plot_spectrum(self):
        """Plot the spectral data."""
        if not self.current_measurement or not self.current_measurement['spd']:
            messagebox.showwarning("No Data", "No spectral data to plot")
            return
        
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        wavelengths = self.current_measurement['wavelengths']
        spd = self.current_measurement['spd']
        
        ax.plot(wavelengths, spd, 'b-', linewidth=2, label='Spectral Power Distribution')
        ax.set_xlabel('Wavelength (nm)')
        ax.set_ylabel('Reflectance (%)')
        ax.set_title('Spectral Power Distribution')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        self.canvas.draw()
    
    def plot_chromaticity(self):
        """Plot the chromaticity diagram."""
        if not self.current_measurement:
            messagebox.showwarning("No Data", "No measurement data to plot")
            return
        
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        # Convert XYZ to xy chromaticity
        xyz = self.current_measurement['xyz']
        x, y = ColorUtils.xyz_to_xy(xyz)
        
        # Plot the point
        ax.plot(x, y, 'ro', markersize=10, label='Measured Color')
        ax.set_xlabel('x')
        ax.set_ylabel('y')
        ax.set_title('Chromaticity Diagram')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Set reasonable limits
        ax.set_xlim(0, 0.8)
        ax.set_ylim(0, 0.9)
        
        self.canvas.draw()
    
    def clear_plot(self):
        """Clear the plot."""
        self.fig.clear()
        self.canvas.draw()
    
    def clear_history(self):
        """Clear measurement history."""
        self.measurement_history.clear()
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
    
    def save_history(self):
        """Save measurement history to file."""
        if not self.measurement_history:
            messagebox.showwarning("No History", "No measurements to save")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                FileUtils.save_json(self.measurement_history, filename)
                messagebox.showinfo("Save", f"History saved to {filename}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save: {e}")
    
    def load_history(self):
        """Load measurement history from file."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.measurement_history = FileUtils.load_json(filename)
                
                # Update treeview
                for item in self.history_tree.get_children():
                    self.history_tree.delete(item)
                
                for measurement in self.measurement_history:
                    xyz_str = f"{measurement['xyz'][0]:.2f}, {measurement['xyz'][1]:.2f}, {measurement['xyz'][2]:.2f}"
                    lab_str = f"{measurement['lab'][0]:.2f}, {measurement['lab'][1]:.2f}, {measurement['lab'][2]:.2f}"
                    rgb_str = f"{measurement['rgb'][0]}, {measurement['rgb'][1]}, {measurement['rgb'][2]}"
                    
                    self.history_tree.insert("", tk.END, values=(
                        measurement['timestamp'],
                        xyz_str,
                        lab_str,
                        rgb_str
                    ))
                
                messagebox.showinfo("Load", f"History loaded from {filename}")
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load: {e}")
    
    def run(self):
        """Run the GUI application."""
        self.root.mainloop()


def main():
    """Main entry point for GUI application."""
    app = CR30GUI()
    app.run()


if __name__ == "__main__":
    main()

