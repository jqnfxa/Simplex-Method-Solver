@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Creating executable...
pyinstaller --onefile main.py

echo Done! Executable is in the "dist" folder
pause