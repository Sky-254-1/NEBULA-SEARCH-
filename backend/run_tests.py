#!/usr/bin/env python
"""Run backend tests with coverage."""

import subprocess
import sys

def run():
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "--tb=short",
        "-q",
        "--cov=app",
        "--cov-report=term-missing"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    print(f"\nExit code: {result.returncode}")
    return result.returncode

if __name__ == "__main__":
    sys.exit(run())
