@echo off
cd /d "D:\Visual Studio 2017\tv_viewer_project"
python organize_project.py
if %errorlevel% neq 0 (
    echo Python script failed. Trying alternative...
    python -c "exec(open('organize_project.py').read())"
)
echo.
echo Done! Press any key to close...
pause > nul
