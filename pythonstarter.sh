#!/bin/bash

# Check if Brew is installed
if ! command -v brew &> /dev/null
then
    echo "Brew is not installed. Installing Brew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Brew is already installed."
fi

# Check if Python3 is installed and update if necessary
if ! command -v python3 &> /dev/null
then
    echo "Python3 is not installed. Installing Python3..."
    brew install python3
else
    echo "Python3 is already installed."
    current_version=$(python3 -V | awk '{print $2}')
    latest_version=$(brew info python3 | awk '/^python@/ {print $3; exit}')
    if [ "$current_version" != "$latest_version" ]
    then
        echo "Updating Python3 to the latest version..."
        brew upgrade python3
    else
        echo "Python3 is up to date."
    fi
fi

# Check if Pip3 is installed and update if necessary
if ! command -v pip3 &> /dev/null
then
    echo "Pip3 is not installed. Installing Pip3..."
    python3 -m ensurepip --upgrade
else
    echo "Pip3 is already installed."
    pip3 install --upgrade pip
    echo "Pip3 has been updated to the latest version."
fi

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing required packages in the virtual environment..."
pip install -r requirements.txt

echo "Virtual environment setup complete!"

echo "$(tput setaf 1)Please make sure you have created a Private App with the required scopes for company deletion.$(tput sgr0)"

if [ ! -f ".env" ] || [ -z "$(grep -E '^HUBSPOT_TOKEN=.+' .env)" ]
then
    echo "$(tput setaf 1)It seems you have not set your HubSpot API token in the .env file or the .env file is missing.$(tput sgr0)"
    echo "$(tput setaf 4)Please enter your HubSpot Private App API token:$(tput sgr0)"
    read HUBSPOT_TOKEN
    echo "HUBSPOT_TOKEN=$HUBSPOT_TOKEN" > .env
else
    echo "$(tput setaf 2)HUBSPOT_TOKEN is already set in the .env file.$(tput sgr0)"
fi

echo "You are set to go!" 

echo "$(tput setaf 4)The virtual environment is now activated. To deactivate it, run 'deactivate'$(tput sgr0)"

