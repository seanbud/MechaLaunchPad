@echo off
echo Starting MechaLaunchPad...
.\venv\Scripts\python -m app
if %errorlevel% neq 0 (
    echo.
    echo Application exited with an error.
    pause
)
