#!/usr/bin/env python
"""Save e2e test output to file."""
import sys
import os
import subprocess

os.chdir(r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend")

result = subprocess.run([
    sys.executable, "-m", "pytest", 
    "tests/e2e/", "-v", "--tb=short"
], capture_output=True, text=True)

# Write both stdout and stderr to file
with open("e2e_full_output.txt", "w") as f:
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\n\nSTDERR:\n")
    f.write(result.stderr)
    f.write(f"\n\nReturn code: {result.returncode}\n")

print(f"Tests completed. Return code: {result.returncode}")
print(f"Output saved to e2e_full_output.txt")
