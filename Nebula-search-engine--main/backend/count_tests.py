#!/usr/bin/env python
"""Count tests in the test directory."""
import sys
import os

os.chdir(r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend")

import pytest

# Collect tests
result = pytest.main(['tests/', '--collect-only', '-q'])

# Get the collected tests
from _pytest.config import Config
from _pytest.main import Session

# Just print the count
print("Test collection complete")
