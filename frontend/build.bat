@echo off
cd /d "%~dp0"
echo Building frontend...
call npm.cmd run build
echo Frontend build complete.
pause
