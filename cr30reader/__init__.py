"""
CR30Reader - Color Chart Reader for CR30 Colorimeter

A Python application for reading color charts using the CR30 colorimeter device,
designed for printer characterization and color management workflows.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .driver import CR30Reader
from .color_science import ColorScience
from .protocol import CR30Protocol

__all__ = ["CR30Reader", "ColorScience", "CR30Protocol"]

