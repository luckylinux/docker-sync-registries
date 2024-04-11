#!/bin/bash

## Save Current Path
currentpath=$(pwd)

# Install required Python Packages
sudo apt-get install -y python3-pip python3-venv

## Create a new Python venv
python3 -m venv venv

## Activate venv
source venv/bin/activate

## Install requirements (upgrade if needed)
pip3 install -r requirements.txt
pip3 install --upgrade -r requirements.txt

# Install go
sudo apt-get install -y golang-1.21 golang-go

# Build RegClient
mkdir -p build/regclient
if [[ ! -f "build/regclient/Makefile" ]]
then
    # Clone Repository
    git clone https://github.com/regclient/regclient.git build/regclient
else
    # Update Repository
    git pull
fi
cd build/regclient
make
./bin/regctl version
