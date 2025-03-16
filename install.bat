@echo off
echo installing dependencies...
pip install -r requirements.txt

echo creating executable...
pyinstaller --onefile --noconsole src\main.py --name simplex.exe

echo Done! Executable is in the "dist" folder
pause
