#!/usr/bin/env python
"""Run full test suite without stopping at first failure."""
import sys
import os

os.chdir(r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend")

import pytest

# Run full test suite without -x
result = pytest.main(['tests/', '-v', '--tb=short'])

# Write summary
with open("full_test_no_stop_output.txt", "w") as f:
    f.write(f"Test result: {'PASSED' if result == 0 else 'FAILED'}\n")
    f.write(f"Exit code: {result}\n")

print(f"Tests completed with exit code: {result}")
