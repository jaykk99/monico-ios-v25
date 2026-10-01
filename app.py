"""Desktop/dev entry point: serve the Monico web UI locally.

On iOS this file is not used - Briefcase launches `monicoios.app:main()`
directly (see pyproject.toml `main_module`).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from monicoios.app import main

if __name__ == "__main__":
    app = main()
    if app is not None:  # None = headless dev mode, server already running
        app.main_loop()
