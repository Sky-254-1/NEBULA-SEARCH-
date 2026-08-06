#!/usr/bin/env python
"""Run e2e tests and write output to file."""
import subprocess
import sys
import os

os.chdir(r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend")

test_files = [
    ("tests/e2e/test_e2e_auth.py", "auth"),
    ("tests/e2e/test_e2e_documents.py", "documents"),
    ("tests/e2e/test_e2e_search.py", "search"),
]

with open("e2e_results.txt", "w") as f:
    for test_file, name in test_files:
        f.write(f"\n{'='*60}\n")
        f.write(f"Running {name}...\n")
        f.write(f"{'='*60}\n\n")
        
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            test_file, "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        f.write(result.stdout)
        f.write(result.stderr)
        f.write(f"\nReturn code: {result.returncode}\n")

print("Done. Results written to e2e_results.txt")
