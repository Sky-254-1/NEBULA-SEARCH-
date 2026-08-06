import sys
import os

backend_dir = r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend"
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

import pytest

sys.exit(pytest.main(["tests/e2e/test_e2e_auth.py", "-v"]))
