#!/usr/bin/env python3
"""
Post-Build Validation Script for TV Viewer

This script performs comprehensive validation after each build to ensure
the application is stable and ready for release. Run this before every
version update or release.

Usage:
    python tests/validate_build.py
    python tests/validate_build.py --verbose
    python tests/validate_build.py --quick  # Skip slow tests

Exit codes:
    0 - All validations passed
    1 - Critical failures (app won't start)
    2 - Non-critical failures (app works but has issues)
"""

import sys
import os
import time
import argparse
import importlib
import traceback
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Severity(Enum):
    CRITICAL = "CRITICAL"  # App won't start
    HIGH = "HIGH"          # Major feature broken
    MEDIUM = "MEDIUM"      # Feature degraded
    LOW = "LOW"            # Minor issue


@dataclass
class ValidationResult:
    name: str
    passed: bool
    severity: Severity
    message: str
    duration_ms: float = 0


class BuildValidator:
    """Comprehensive build validation for TV Viewer."""
    
    def __init__(self, verbose: bool = False, quick: bool = False):
        self.verbose = verbose
        self.quick = quick
        self.results: List[ValidationResult] = []
    
    def log(self, msg: str):
        if self.verbose:
            print(f"  {msg}")
    
    def run_all(self) -> int:
        """Run all validations and return exit code."""
        print("=" * 60)
        print("TV Viewer - Post-Build Validation")
        print("=" * 60)
        print()
        
        # Critical validations (must pass for app to work)
        self._run_validation("Python Version", self._check_python_version, Severity.CRITICAL)
        self._run_validation("Required Imports", self._check_required_imports, Severity.CRITICAL)
        self._run_validation("Config Module", self._check_config, Severity.CRITICAL)
        self._run_validation("Core Modules", self._check_core_modules, Severity.CRITICAL)
        self._run_validation("UI Modules", self._check_ui_modules, Severity.CRITICAL)
        self._run_validation("Utils Modules", self._check_utils_modules, Severity.CRITICAL)
        
        # High priority validations
        self._run_validation("Required Files", self._check_required_files, Severity.HIGH)
        self._run_validation("Requirements Check", self._check_requirements_function, Severity.HIGH)
        self._run_validation("Logger System", self._check_logger, Severity.HIGH)
        
        # Medium priority validations
        self._run_validation("Constants Defined", self._check_constants, Severity.MEDIUM)
        self._run_validation("Channel Manager", self._check_channel_manager, Severity.MEDIUM)
        
        if not self.quick:
            self._run_validation("Stream Checker", self._check_stream_checker, Severity.MEDIUM)
            self._run_validation("Repository Handler", self._check_repository_handler, Severity.MEDIUM)
        
        # Low priority validations
        self._run_validation("Optional Dependencies", self._check_optional_deps, Severity.LOW)
        self._run_validation("Documentation", self._check_documentation, Severity.LOW)
        
        # Print summary
        return self._print_summary()
    
    def _run_validation(self, name: str, func, severity: Severity):
        """Run a single validation and record result."""
        start = time.time()
        try:
            passed, message = func()
            duration = (time.time() - start) * 1000
            self.results.append(ValidationResult(name, passed, severity, message, duration))
        except Exception as e:
            duration = (time.time() - start) * 1000
            self.results.append(ValidationResult(
                name, False, severity, f"Exception: {str(e)}", duration
            ))
            if self.verbose:
                traceback.print_exc()
    
    def _check_python_version(self) -> Tuple[bool, str]:
        """Check Python version is compatible."""
        major, minor = sys.version_info[:2]
        if major < 3 or (major == 3 and minor < 9):
            return False, f"Python 3.9+ required, got {major}.{minor}"
        return True, f"Python {major}.{minor}"
    
    def _check_required_imports(self) -> Tuple[bool, str]:
        """Check all required packages can be imported."""
        required = ['tkinter', 'customtkinter', 'PIL', 'aiohttp', 'requests']
        missing = []
        
        for pkg in required:
            try:
                importlib.import_module(pkg)
                self.log(f"✓ {pkg}")
            except ImportError:
                missing.append(pkg)
                self.log(f"✗ {pkg} - MISSING")
        
        if missing:
            return False, f"Missing: {', '.join(missing)}"
        return True, f"All {len(required)} packages available"
    
    def _check_config(self) -> Tuple[bool, str]:
        """Check config module loads correctly."""
        try:
            import config
            required_attrs = ['APP_NAME', 'APP_VERSION', 'BASE_DIR', 'CHANNELS_FILE']
            missing = [a for a in required_attrs if not hasattr(config, a)]
            
            if missing:
                return False, f"Missing config attributes: {missing}"
            
            self.log(f"APP_NAME: {config.APP_NAME}")
            self.log(f"APP_VERSION: {config.APP_VERSION}")
            return True, f"v{config.APP_VERSION}"
        except Exception as e:
            return False, str(e)
    
    def _check_core_modules(self) -> Tuple[bool, str]:
        """Check core modules import correctly."""
        modules = [
            'core.channel_manager',
            'core.stream_checker',
            'core.repository'
        ]
        failed = []
        
        for mod in modules:
            try:
                importlib.import_module(mod)
                self.log(f"✓ {mod}")
            except Exception as e:
                failed.append(f"{mod}: {e}")
                self.log(f"✗ {mod}")
        
        if failed:
            return False, "; ".join(failed)
        return True, f"All {len(modules)} core modules OK"
    
    def _check_ui_modules(self) -> Tuple[bool, str]:
        """Check UI modules import correctly."""
        modules = [
            'ui.constants',
            'ui.main_window',
            'ui.player_window',
            'ui.scan_animation'
        ]
        failed = []
        
        for mod in modules:
            try:
                importlib.import_module(mod)
                self.log(f"✓ {mod}")
            except Exception as e:
                failed.append(f"{mod}: {e}")
                self.log(f"✗ {mod}")
        
        if failed:
            return False, "; ".join(failed)
        return True, f"All {len(modules)} UI modules OK"
    
    def _check_utils_modules(self) -> Tuple[bool, str]:
        """Check utils modules import correctly."""
        modules = [
            'utils.helpers',
            'utils.thumbnail',
            'utils.logger',
            'utils.channel_lookup'
        ]
        failed = []
        
        for mod in modules:
            try:
                importlib.import_module(mod)
                self.log(f"✓ {mod}")
            except Exception as e:
                failed.append(f"{mod}: {e}")
                self.log(f"✗ {mod}")
        
        if failed:
            return False, "; ".join(failed)
        return True, f"All {len(modules)} utils modules OK"
    
    def _check_required_files(self) -> Tuple[bool, str]:
        """Check required files exist."""
        import config
        
        files = [
            ('main.py', True),
            ('config.py', True),
            ('requirements.txt', True),
            ('README.md', True),
            ('CHANGELOG.md', True),
            (config.CHANNELS_FILE, False),  # May not exist on first run
        ]
        
        missing_required = []
        missing_optional = []
        
        for filepath, required in files:
            full_path = os.path.join(config.BASE_DIR, filepath) if not os.path.isabs(filepath) else filepath
            exists = os.path.exists(full_path)
            
            if not exists and required:
                missing_required.append(filepath)
            elif not exists:
                missing_optional.append(filepath)
            
            self.log(f"{'✓' if exists else '✗'} {filepath}")
        
        if missing_required:
            return False, f"Missing required: {missing_required}"
        if missing_optional:
            return True, f"OK (optional missing: {missing_optional})"
        return True, "All files present"
    
    def _check_requirements_function(self) -> Tuple[bool, str]:
        """Check the requirements check function works."""
        try:
            # Import main module's check function
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # Test the check logic directly
            from main import check_requirements
            success, missing, warnings = check_requirements()
            
            if not success:
                return False, f"Missing requirements: {missing}"
            
            if warnings:
                return True, f"OK with warnings: {len(warnings)}"
            return True, "All requirements satisfied"
        except Exception as e:
            return False, f"Function error: {e}"
    
    def _check_logger(self) -> Tuple[bool, str]:
        """Check logging system works."""
        try:
            from utils.logger import get_logger, get_log_file_path
            
            logger = get_logger("test_validation")
            log_path = get_log_file_path()
            
            # Test logging
            logger.info("Build validation test log entry")
            
            if not os.path.exists(os.path.dirname(log_path)):
                return False, "Log directory not created"
            
            return True, f"Logging to {os.path.basename(log_path)}"
        except Exception as e:
            return False, str(e)
    
    def _check_constants(self) -> Tuple[bool, str]:
        """Check UI constants are properly defined."""
        try:
            from ui.constants import FluentColors, FluentSpacing
            
            required_colors = ['ACCENT', 'BG_MICA', 'TEXT_PRIMARY', 'SUCCESS', 'ERROR']
            missing = [c for c in required_colors if not hasattr(FluentColors, c)]
            
            if missing:
                return False, f"Missing colors: {missing}"
            
            return True, f"FluentColors has {len(dir(FluentColors))} attributes"
        except Exception as e:
            return False, str(e)
    
    def _check_channel_manager(self) -> Tuple[bool, str]:
        """Check channel manager can be instantiated."""
        try:
            from core.channel_manager import ChannelManager
            
            # Just test instantiation, don't load channels
            manager = ChannelManager()
            
            # Check required methods exist
            required_methods = ['load_cached_channels', 'save_channels', 'get_channels_by_group']
            missing = [m for m in required_methods if not hasattr(manager, m)]
            
            if missing:
                return False, f"Missing methods: {missing}"
            
            return True, "ChannelManager OK"
        except Exception as e:
            return False, str(e)
    
    def _check_stream_checker(self) -> Tuple[bool, str]:
        """Check stream checker can be instantiated."""
        try:
            from core.stream_checker import StreamChecker
            
            checker = StreamChecker()
            
            if not hasattr(checker, 'start_background_check'):
                return False, "Missing start_background_check method"
            if not hasattr(checker, 'stop'):
                return False, "Missing stop method"
            
            return True, "StreamChecker OK"
        except Exception as e:
            return False, str(e)
    
    def _check_repository_handler(self) -> Tuple[bool, str]:
        """Check repository handler can be instantiated."""
        try:
            from core.repository import RepositoryHandler
            
            handler = RepositoryHandler()
            
            if not hasattr(handler, 'fetch_repository'):
                return False, "Missing fetch_repository method"
            
            return True, f"RepositoryHandler OK ({len(handler.repositories)} repos)"
        except Exception as e:
            return False, str(e)
    
    def _check_optional_deps(self) -> Tuple[bool, str]:
        """Check optional dependencies."""
        optional = {
            'vlc': 'Video playback',
            'pychromecast': 'Google Cast'
        }
        
        available = []
        missing = []
        
        for pkg, desc in optional.items():
            try:
                importlib.import_module(pkg)
                available.append(pkg)
                self.log(f"✓ {pkg} ({desc})")
            except ImportError:
                missing.append(f"{pkg} ({desc})")
                self.log(f"✗ {pkg} - optional")
        
        if missing:
            return True, f"Available: {len(available)}, Optional missing: {len(missing)}"
        return True, f"All {len(optional)} optional deps available"
    
    def _check_documentation(self) -> Tuple[bool, str]:
        """Check documentation files exist and have content."""
        import config
        
        docs = ['README.md', 'CHANGELOG.md', 'SUPPORT_GUIDE.md', 'ARCHITECTURE.md']
        issues = []
        
        for doc in docs:
            path = os.path.join(config.BASE_DIR, doc)
            if not os.path.exists(path):
                issues.append(f"{doc} missing")
            elif os.path.getsize(path) < 100:
                issues.append(f"{doc} too small")
            else:
                self.log(f"✓ {doc}")
        
        if issues:
            return True, f"Issues: {', '.join(issues)}"  # Not critical
        return True, f"All {len(docs)} docs present"
    
    def _print_summary(self) -> int:
        """Print validation summary and return exit code."""
        print()
        print("=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60)
        
        # Group by severity
        by_severity: Dict[Severity, List[ValidationResult]] = {}
        for result in self.results:
            by_severity.setdefault(result.severity, []).append(result)
        
        # Print results
        passed_count = 0
        failed_count = 0
        critical_failed = False
        high_failed = False
        
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            results = by_severity.get(severity, [])
            if not results:
                continue
            
            print(f"\n{severity.value}:")
            for r in results:
                status = "[PASS]" if r.passed else "[FAIL]"
                print(f"  {status} {r.name}: {r.message} ({r.duration_ms:.0f}ms)")
                
                if r.passed:
                    passed_count += 1
                else:
                    failed_count += 1
                    if severity == Severity.CRITICAL:
                        critical_failed = True
                    elif severity == Severity.HIGH:
                        high_failed = True
        
        # Summary
        print()
        print("=" * 60)
        total = passed_count + failed_count
        print(f"TOTAL: {passed_count}/{total} passed, {failed_count} failed")
        
        if critical_failed:
            print("\n❌ CRITICAL FAILURES - Application will not start!")
            return 1
        elif high_failed:
            print("\n⚠️ HIGH PRIORITY FAILURES - Major features broken!")
            return 2
        elif failed_count > 0:
            print("\n⚠️ Some non-critical issues found")
            return 0
        else:
            print("\n[OK] All validations passed!")
            return 0


def main():
    parser = argparse.ArgumentParser(description="TV Viewer Post-Build Validation")
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--quick', '-q', action='store_true', help='Skip slow tests')
    args = parser.parse_args()
    
    validator = BuildValidator(verbose=args.verbose, quick=args.quick)
    exit_code = validator.run_all()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
