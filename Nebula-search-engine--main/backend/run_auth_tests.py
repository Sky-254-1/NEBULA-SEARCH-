#!/usr/bin/env python
"""Run e2e tests for auth module."""
import subprocess
import sys

result = subprocess.run([
    sys.executable, "-m", "pytest", 
    "tests/e2e/test_e2e_auth.py", "-v"
], cwd=r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend")

sys.exit(result.returncode)
