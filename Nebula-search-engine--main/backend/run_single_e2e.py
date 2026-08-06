#!/usr/bin/env python
"""Run a single e2e test file and write output to file."""
import sys
import os

# Ensure we have sys imported
import sys

os.chdir(r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend")

test_file = sys.argv[1] if len(sys.argv) > 1 else "tests/e2e/test_e2e_auth.py"
output_file = sys.argv[2] if len(sys.argv) > 2 else "test_output.txt"

import pytest

# Capture output
from io import StringIO
old_stdout = sys.stdout
sys.stdout = StringIO()

result = pytest.main([test_file, "-v", "--tb=short"])

output = sys.stdout.getvalue()
sys.stdout = old_stdout

# Write to file
with open(output_file, "w") as f:
    f.write(f"Test file: {test_file}\n")
    f.write(f"Result code: {result}\n")
    f.write(f"Output:\n{output}\n")

print(f"Done. Output written to {output_file}")
