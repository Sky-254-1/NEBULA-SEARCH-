#!/usr/bin/env python
"""Run full test suite and capture output to file."""
import sys
import os

os.chdir(r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend")

import pytest

# Run full test suite
result = pytest.main(['tests/', '-v', '--tb=short', '-x'])

# Write summary
with open("full_test_output.txt", "w") as f:
    f.write(f"Test result: {'PASSED' if result == 0 else 'FAILED'}\n")
    f.write(f"Exit code: {result}\n")

print(f"Tests completed with exit code: {result}")
