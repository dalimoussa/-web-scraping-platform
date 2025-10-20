@echo off
REM Quick launcher for the Web UI Dashboard
REM Double-click this file to start the web interface

echo Starting Japanese Officials Data Collector Web UI...
echo.
echo The web interface will open in your default browser.
echo Press Ctrl+C to stop the server.
echo.

cd /d "%~dp0"
call .venv\Scripts\activate.bat
streamlit run app.py

pause
