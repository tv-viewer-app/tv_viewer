@echo off
echo Installing PowerShell Core...
echo.

REM Try winget first
winget install --id Microsoft.PowerShell --source winget --accept-package-agreements --accept-source-agreements

if %errorlevel% neq 0 (
    echo.
    echo Winget failed. Please install manually from:
    echo https://aka.ms/powershell
    echo.
    echo Or download the MSI installer from:
    echo https://github.com/PowerShell/PowerShell/releases
    echo.
    pause
    exit /b 1
)

echo.
echo PowerShell Core installed successfully!
echo Please restart your terminal/Copilot CLI session.
pause
