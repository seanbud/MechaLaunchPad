#!/bin/bash

# Configuration
VENV_DIR="venv"
REQUIREMENTS="requirements.txt"

echo "Checking environment..."

# 1. Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in ./$VENV_DIR..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
    fi
fi

# 2. Activate virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment."
    exit 1
fi

# 3. Upgrade pip and install requirements
echo "Verifying dependencies..."
python3 -m pip install --upgrade pip > /dev/null
pip install -r $REQUIREMENTS

# 4. Launch Application
echo "Starting MechaLaunchPad..."
python3 -m app

# 5. Deactivate on exit
deactivate
