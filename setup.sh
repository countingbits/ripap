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

echo "Do you want to clone and install from the git repository? (y/n)"
read REPLY
if [ "$REPLY" != "${REPLY#[Yy]}" ] ;then
    if [ -d "ripap" ]; then
        echo "'ripap' directory already exists. Use existing directory or delete and re-clone? (use/del)"
        read CLONE_REPLY
        if [ "$CLONE_REPLY" == "del" ]; then
            rm -rf ripap
            echo "Removed 'ripap' directory. Cloning again..."
            git clone https://github.com/your/ripap.git
        else
            echo "Using existing 'ripap' directory."
        fi
    else
        echo "Cloning repository..."
        git clone https://github.com/your/ripap.git
    fi
    echo "Running setup from cloned repository..."
    cd ripap
    
    python3 apinstall.py
fi

exit 0
