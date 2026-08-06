import sys
import os
import subprocess

backend_dir = r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend"
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

result = subprocess.run([sys.executable, "-m", "pytest", "tests/e2e/test_e2e_auth.py", "-v", "--tb=short", "-rN"], capture_output=True, text=True)

# Write output to file
with open("test_output.txt", "w") as f:
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\nSTDERR:\n")
    f.write(result.stderr)
    f.write(f"\nReturn code: {result.returncode}\n")

print(f"Tests completed with return code {result.returncode}")
print(f"Output written to test_output.txt")

sys.exit(result.returncode)
