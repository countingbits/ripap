#!/bin/bash

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# Install Python3 and pip if not already installed
echo "Checking for Python 3 installation..."
if ! command -v python3 &> /dev/null; then
    echo "Python 3 not found. Installing Python 3..."
    sudo apt-get install -y python3
else
    echo "Python 3 is already installed."
fi

if ! command -v pip3 &> /dev/null; then
    echo "pip for Python 3 not found. Installing pip..."
    sudo apt-get install -y python3-pip
else
    echo "pip for Python 3 is already installed."
fi

# Optional Git installation
echo "Do you want to install git? (y/n)"
read REPLY
if [ "$REPLY" != "${REPLY#[Yy]}" ] ;then
    echo "Installing git..."
    sudo apt-get install -y git
fi

# Option to clone from a Git repository
echo "Do you want to clone and install from the git repository? (y/n)"
read REPLY
if [ "$REPLY" != "${REPLY#[Yy]}" ] ;then
    echo "Cloning repository..."
    git clone https://github.com/countingbits/ripap.git
    echo "Running setup from cloned repository..."
    cd ripap
    python3 apinstall.py install
else
    echo "Skipping git clone and installation."
fi # This closes the if statement for cloning from git repository.

# Proceed with local installation if Git cloning is skipped
echo "Do you want to proceed with local installation? (y/n)"
read REPLY
if [ "$REPLY" != "${REPLY#[Yy]}" ]; then
    echo "Please enter the path to the local setup file:"
    read FILE_PATH
    if [ -f "$FILE_PATH" ]; then
        echo "Running setup from local file..."
        python3 "$FILE_PATH"
    else
        echo "File not found. Please check the path and try again."
    fi
fi

echo "Setup completed successfully."
exit 0
