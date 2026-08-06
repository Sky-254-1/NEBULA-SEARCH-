#!/usr/bin/env python
"""Run e2e tests with better isolation."""
import sys
import os

os.chdir(r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend")

import pytest

# Run e2e tests with more verbose output
result = pytest.main([
    'tests/e2e/', '-v', '--tb=long', 
    '-o', 'asyncio_mode=auto',
    '-o', 'asyncio_default_fixture_loop_scope=function'
])

# Write summary
with open("e2e_isolated_output.txt", "w") as f:
    f.write(f"Test result: {'PASSED' if result == 0 else 'FAILED'}\n")
    f.write(f"Exit code: {result}\n")

print(f"Tests completed with exit code: {result}")
