#!/usr/bin/env python
"""Directly run e2e tests using pytest API."""
import sys
import os

os.chdir(r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend")

# Import pytest and run
import pytest

# Run auth tests
print("="*60)
print("Running e2e_auth...")
print("="*60)
result = pytest.main(["tests/e2e/test_e2e_auth.py", "-v", "--tb=short"])
print(f"Auth tests result: {result}")

# Run documents tests
print("\n" + "="*60)
print("Running e2e_documents...")
print("="*60)
result = pytest.main(["tests/e2e/test_e2e_documents.py", "-v", "--tb=short"])
print(f"Documents tests result: {result}")

# Run search tests
print("\n" + "="*60)
print("Running e2e_search...")
print("="*60)
result = pytest.main(["tests/e2e/test_e2e_search.py", "-v", "--tb=short"])
print(f"Search tests result: {result}")
