@echo off
cd /d "%~dp0"
python run_tests.py > test_results.txt 2>&1
echo Done. Check test_results.txt
pause
