import subprocess, sys, os, shutil
os.chdir(os.path.dirname(os.path.abspath(__file__)))
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
r = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/",
     "--cov=app",
     "--cov-report=term-missing",
     "--cov-report=xml",
     "--cov-report=html",
     "-v", "--tb=short", "--no-header", "--cache-clear"],
    capture_output=True, text=True, env=env
)
with open("coverage_run.txt", "w", encoding="utf-8") as f:
    f.write("=== STDOUT ===\n" + r.stdout + "\n=== STDERR ===\n" + r.stderr)
print("Exit:", r.returncode)
# Extract summary
lines = r.stdout.splitlines()
for line in lines:
    if line.startswith("TOTAL") or "coverage:" in line.lower() or line.startswith("Required"):
        print(line)
