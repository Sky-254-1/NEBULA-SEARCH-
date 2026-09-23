import subprocess, sys, os
os.chdir(r"c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\frontend")
r = subprocess.run(
    "npm test -- --run --reporter=verbose",
    capture_output=True, text=True, shell=True
)
with open("vitest_results.txt", "w", encoding="utf-8") as f:
    f.write(r.stdout + "\n" + r.stderr)
print("Exit:", r.returncode)
