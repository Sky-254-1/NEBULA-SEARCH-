import subprocess, sys, os, shutil
os.chdir(r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend")
for root, dirs, files in os.walk("app"):
    for d in list(dirs):
        if d == "__pycache__":
            try:
                shutil.rmtree(os.path.join(root, d))
                dirs.remove(d)
            except Exception:
                pass
for root, dirs, files in os.walk("tests"):
    for d in list(dirs):
        if d == "__pycache__":
            try:
                shutil.rmtree(os.path.join(root, d))
                dirs.remove(d)
            except Exception:
                pass
env = os.environ.copy()
env["PYTHONPATH"] = "."
env["PYTHONDONTWRITEBYTECODE"] = "1"
# Only run the new test file first to ensure it works
r = subprocess.run(
    [sys.executable, "-m", "pytest",
     "tests/test_coverage_deployment.py",
     "--cov=app",
     "--cov-report=term-missing",
     "--cov-report=xml",
     "-v", "--tb=short", "--no-header", "--cache-clear"],
    capture_output=True, text=True, env=env
)
with open("coverage_boost.txt", "w", encoding="utf-8") as f:
    f.write("=== STDOUT ===\n" + r.stdout + "\n=== STDERR ===\n" + r.stderr)
print("Exit:", r.returncode)
# Extract relevant lines
lines = r.stdout.splitlines() + r.stderr.splitlines()
for line in lines:
    if "TOTAL" in line or "PASSED" in line or "FAILED" in line or "ERROR" in line or "coverage:" in line.lower() or "=====" in line:
        print(line[:300])
