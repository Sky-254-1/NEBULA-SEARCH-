"""Test runner script for backend."""
import sys
import os

# Change to backend directory
os.chdir(r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend")
sys.path.insert(0, ".")

import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(["tests/", "--tb=short", "-q", "--cov=app", "--cov-report=term-missing"]))
