#!/usr/bin/env python
"""Run router mount tests."""

import subprocess
import sys

# Run the tests
result = subprocess.run(
    [sys.executable, "-m", "pytest", "backend/tests/test_router_mounts.py", "-v"],
    capture_output=True,
    text=True,
)

# Print output
print("=" * 80)
print("STDOUT:")
print("=" * 80)
print(result.stdout[-8000:])

print("\n" + "=" * 80)
print("STDERR:")
print("=" * 80)
print(result.stderr[-2000:])

print("\n" + "=" * 80)
print(f"Return code: {result.returncode}")
print("=" * 80)

# Save to file
with open("router_test_result.txt", "w", encoding="utf-8") as f:
    f.write(result.stdout)
    f.write("\n\nSTDERR:\n")
    f.write(result.stderr)
    f.write(f"\n\nReturn code: {result.returncode}\n")

print("\nOutput saved to router_test_result.txt")
