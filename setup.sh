#!/bin/bash

## Save Current Path
currentpath=$(pwd)

## Create a new Python venv
python -m venv venv

## Activate venv
source venv/bin/activate

## Install requirements (upgrade if needed)
pip install -r requirements.txt
pip install --upgrade -r requirements.txt

# Install go
sudo apt-get install -y golang-1.21 golang-go

# Build RegClient
mkdir -p build/regclient
if [[ ! -d "build/regclient" ]]
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
