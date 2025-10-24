"""Root conftest.py for pytest configuration."""

import sys
from pathlib import Path

# Add src directory to Python path so tests can import modules
# This runs at conftest import time, before any test collection
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
