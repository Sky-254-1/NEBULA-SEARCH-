#!/usr/bin/env python3
"""
Environment Validation Script

A standalone script to validate environment configuration before application startup.

Usage:
    python validate_env.py [--quiet] [--exit-early]

Options:
    --quiet       Suppress output (exit codes still work)
    --exit-early  Exit immediately on first error (for CI/CD)
"""

import os
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Validate environment configuration for Nebula Search"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output (exit codes still work)"
    )
    parser.add_argument(
        "--exit-early",
        action="store_true",
        help="Exit immediately on first error (for CI/CD)"
    )
    args = parser.parse_args()
    
    # Add parent directory to path for imports
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    
    # Only add if not already present
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    try:
        from app.config_validation import run_validations, ValidationError
    except ImportError as e:
        if not args.quiet:
            print(f"Failed to import validation module: {e}", file=sys.stderr)
        return 1
    
    try:
        if not args.quiet:
            print("Validating environment configuration...")
            print("-" * 50)
        
        result = run_validations()
        
        if not args.quiet:
            print("-" * 50)
            if result:
                print("✓ Environment validation passed.")
            else:
                print("⚠ Environment validation completed with warnings.")
        
        return 0 if result else 1
        
    except ValidationError as e:
        if not args.quiet:
            print("-" * 50, file=sys.stderr)
            print("✗ Environment validation failed:", file=sys.stderr)
            print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        if not args.quiet:
            print("-" * 50, file=sys.stderr)
            print(f"✗ Unexpected error during validation: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
