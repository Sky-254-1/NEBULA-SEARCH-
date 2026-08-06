#!/usr/bin/env python
"""Run full test suite and capture output."""
import sys
import os

os.chdir(r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend")

import pytest

# Run full test suite - note: pytest.ini ignores e2e tests
result = pytest.main(['tests/', '-v', '--tb=short', '--disable-warnings'])

# Write summary
with open("full_test_v2_output.txt", "w") as f:
    f.write(f"Test result: {'PASSED' if result == 0 else 'FAILED'}\n")
    f.write(f"Exit code: {result}\n")

print(f"Tests completed with exit code: {result}")
