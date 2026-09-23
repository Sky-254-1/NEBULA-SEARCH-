cd "%~dp0"
python -m pytest tests/ -v --tb=short > test_output.txt 2>&1
echo Done.
