#!/usr/bin/env python
"""Run e2e tests separately to capture individual failures."""
import subprocess
import sys
import os

os.chdir(r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend")

test_files = [
    ("e2e_auth", "tests/e2e/test_e2e_auth.py"),
    ("e2e_documents", "tests/e2e/test_e2e_documents.py"),
    ("e2e_search", "tests/e2e/test_e2e_search.py"),
]

for name, test_file in test_files:
    print(f"\n{'='*60}")
    print(f"Running {name}...")
    print(f"{'='*60}\n")
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        test_file, "-v", "--tb=short"
    ], capture_output=False, text=True)
    
    print(f"\n{name} finished with exit code: {result.returncode}")
