"""
CR30Reader Main Entry Point

This module allows cr30reader to be executed as a package:
python -m cr30reader

For GUI: python -m cr30reader gui
For CLI: python -m cr30reader cli
"""

import sys
import asyncio

def run_gui():
    """Run the GUI application."""
    from cr30reader.gui import main
    main()

def run_cli():
    """Run the CLI application."""
    from cr30reader.cli import main as cli_main
    asyncio.run(cli_main())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "gui":
            run_gui()
        elif command == "cli":
            run_cli()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python -m cr30reader [gui|cli]")
            sys.exit(1)
    else:
        # Default to CLI for backwards compatibility
        run_cli()
