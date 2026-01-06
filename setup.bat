@echo off
echo ================================================
echo ClashFish Setup - Installing Dependencies
echo ================================================
echo.
echo This will install all required Python packages...
echo.

pip install -r requirements_clashfish.txt

echo.
echo ================================================
echo Setup Complete!
echo ================================================
echo.
echo You can now run ClashFish by:
echo 1. Double-clicking "start_clashfish.bat"
echo 2. Or running: python api_server.py
echo.
pause
