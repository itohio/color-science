"""
Test runner entry point.

This allows running tests via: python -m cr30reader.tests
"""

import sys
from pathlib import Path

def main():
    """Main entry point for test runner."""
    import pytest
    
    # Get the tests directory
    tests_dir = Path(__file__).parent
    
    # Run pytest with the tests directory
    args = [str(tests_dir)] + sys.argv[1:] if len(sys.argv) > 1 else [str(tests_dir)]
    sys.exit(pytest.main(args))

if __name__ == "__main__":
    main()

