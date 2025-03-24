#!/bin/bash

# create a virtual environment
echo "creating venv..."
python -m venv .venv

# cctivate the virtual environment
echo "activating venv..."
source .venv/bin/activate

# install dependencies
echo "installing dependencies..."
pip install -r requirements.txt

# create the executable (with --noconsole)
echo "creating executable..."
pyinstaller --onefile --noconsole src/main.py --name simplex

# deactivate the virtual environment
echo "Deactivating venv..."
deactivate

echo "Done! Executable is in the 'dist' folder."
