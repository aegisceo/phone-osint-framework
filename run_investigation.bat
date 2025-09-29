@echo off

REM Phone OSINT Investigation Runner for Windows
REM Usage: run_investigation.bat +1234567890

SET PHONE_NUMBER=%1

IF "%PHONE_NUMBER%"=="" (
    echo Usage: %0 ^<phone_number^>
    echo Example: %0 +1234567890
    exit /b 1
)

echo =====================================
echo Phone OSINT Investigation Framework
echo =====================================
echo Target: %PHONE_NUMBER%
echo Time: %date% %time%
echo =====================================

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the investigation
python phone_osint_master.py %PHONE_NUMBER%

REM Check if report was generated
FOR /F "delims=" %%i IN ('dir /b /od results\*\investigation_report.html') DO SET LATEST_RESULT=%%i

IF EXIST "results\%LATEST_RESULT%" (
    echo.
    echo Opening report in browser...
    start "" "results\%LATEST_RESULT%"
) ELSE (
    echo Error: Report generation failed
)