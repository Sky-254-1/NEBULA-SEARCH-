import subprocess, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
r = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q", "--no-header"],
    capture_output=True, text=True
)
with open("pytest_results.txt", "w", encoding="utf-8") as f:
    f.write(r.stdout + "\n" + r.stderr)
print("Exit:", r.returncode)
print("Lines:", len(r.stdout.splitlines()))
