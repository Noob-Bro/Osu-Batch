@echo off
setlocal
cd /d "%~dp0"
set "OSUBATCH_PY=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%OSUBATCH_PY%" (
    "%OSUBATCH_PY%" bootstrap.py %*
) else (
    py -3 bootstrap.py %*
)
if errorlevel 1 (
    echo.
    echo Startup failed. Install Python 3.12 or newer, then try again.
    pause
)

