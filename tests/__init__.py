"""
TV Viewer - Automated Validation Suite

This module provides comprehensive validation tests that run after every build
to ensure software stability and quality before release.

Usage:
    python -m pytest tests/ -v
    python tests/validate_build.py  # Quick validation script
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
