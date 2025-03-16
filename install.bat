@echo off
python3.12 --version > nul 2>&1
if errorlevel 1 (
    echo [-] error: Python 3.12 is not found.  Please install Python 3.12 and ensure it's in your PATH.
    pause
    exit /b 1
)

echo creating venv...
python3.12 -m venv .venv

echo activating venv...
.venv\Scripts\activate

echo installing dependencies...
pip install -r requirements.txt

echo creating executable...
pyinstaller --onefile --noconsole src\main.py --name simplex.exe

echo deactivating venv...
deactivate

echo Done! Executable is in the "dist" folder
pause
