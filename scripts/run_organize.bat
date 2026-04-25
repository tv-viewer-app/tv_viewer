@echo off
cd /d "%~dp0.."
python organize_project.py
if %errorlevel% neq 0 (
    echo Python script failed. Trying alternative...
    python -c "exec(open('organize_project.py').read())"
)
echo.
echo Done! Press any key to close...
pause > nul
