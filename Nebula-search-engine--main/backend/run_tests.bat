@echo off
cd /d "c:\Users\KNP LIBRARY\Downloads\Nebula Search\Nebula-search-engine--main\backend"
python run_tests.py > test_results.txt 2>&1
echo Done. Check test_results.txt
pause
