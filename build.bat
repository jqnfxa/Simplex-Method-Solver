@echo off
setlocal enabledelayedexpansion

REM Create virtual environment
echo Creating virtual environment...
python -m venv .venv

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Build executable
echo Creating executable...
pyinstaller --onefile --noconsole src\main.py --name simplex.exe

echo Done! Executable is in the "dist" folder
pause
