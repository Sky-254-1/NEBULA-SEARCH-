import sys
import os
import subprocess

backend_dir = r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend"
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

test_files = [
    "tests/e2e/test_e2e_auth.py",
    "tests/e2e/test_e2e_documents.py", 
    "tests/e2e/test_e2e_search.py"
]

all_results = []
total_passed = 0
total_failed = 0

for test_file in test_files:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short", "-rN"], 
        capture_output=True, 
        text=True
    )
    
    all_results.append({
        "file": test_file,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    })
    
    # Count passed/failed
    stdout = result.stdout
    if "passed" in stdout:
        passed = int(stdout.split("passed")[0].strip().split()[-1])
        total_passed += passed
    if "failed" in stdout:
        failed = int(stdout.split("failed")[0].strip().split()[-1])
        total_failed += failed
    
    print(f"{test_file}: {'PASSED' if result.returncode == 0 else 'FAILED'} ({passed if 'passed' in stdout else 0} passed, {failed if 'failed' in stdout else 0} failed)")

# Write combined output
with open("all_e2e_test_output.txt", "w") as f:
    for result in all_results:
        f.write(f"\n{'='*60}\n")
        f.write(f"File: {result['file']}\n")
        f.write(f"{'='*60}\n")
        f.write(result["stdout"])
        if result["stderr"]:
            f.write("\nSTDERR:\n")
            f.write(result["stderr"])
        f.write(f"\nReturn code: {result['returncode']}\n")

print(f"\n{'='*60}")
print(f"SUMMARY: {total_passed} passed, {total_failed} failed")
print(f"{'='*60}")
