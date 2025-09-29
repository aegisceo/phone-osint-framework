@echo off
echo =====================================
echo Phone OSINT Framework Setup
echo =====================================
echo.

echo [1/5] Creating virtual environment...
python -m venv venv

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/5] Installing Python dependencies...
pip install -r requirements.txt

echo [4/5] Creating directory structure...
if not exist "results" mkdir results
if not exist "cache" mkdir cache
if not exist "logs" mkdir logs
if not exist "data" mkdir data

echo [5/5] Testing API configuration...
python test_apis.py

echo.
echo =====================================
echo Setup complete!
echo.
echo To run an investigation:
echo   run_investigation.bat +1234567890
echo.
echo To use the web interface:
echo   python web_interface.py
echo   Then open http://localhost:5000
echo =====================================

pause