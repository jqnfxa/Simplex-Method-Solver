#!/bin/bash

# check for Python 3.12
if ! command -v python3.12 &> /dev/null; then
    echo "[-] error: Python 3.12 is not installed."
    exit 1
fi

# create a virtual environment
echo "creating venv..."
python3.12 -m venv .venv

# cctivate the virtual environment
echo "activating venv..."
source .venv/bin/activate

# install dependencies
echo "installing dependencies..."
pip install -r requirements.txt

# create the executable (with --noconsole)
echo "creating executable..."
pyinstaller --onefile --noconsole main.py

# deactivate the virtual environment (optional, but good practice)
echo "Deactivating virtual environment..."
deactivate

echo "Done! Executable is in the 'dist' folder."
