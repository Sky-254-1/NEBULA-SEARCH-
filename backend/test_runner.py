"""Test runner script for backend."""
import sys
import os

# Change to backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ".")

import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(["tests/", "--tb=short", "-q", "--cov=app", "--cov-report=term-missing"]))
