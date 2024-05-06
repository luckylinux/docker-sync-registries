#!/bin/bash

# Architecture to use
TARGETPLATFORM=$(uname -m)

# Whether to build Regclient from Source or to Download a Precompiled Binary
BUILD_REGCLIENT="no"

# Save Current Path
currentpath=$(pwd)

# Install required Python Packages
sudo apt-get install -y python3-pip python3-venv

# Create a new Python venv
python3 -m venv venv

## Activate venv
source venv/bin/activate

## Install requirements (upgrade if needed)
pip3 install -r app/requirements.txt
pip3 install --upgrade -r app/requirements.txt

# Install RegClient
if [[ "${BUILD_REGCLIENT}" == "yes" ]]
then
   # Install go
   sudo apt-get install -y golang-1.21 golang-go

   # Build RegClient from Source
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
   #./bin/regctl version
else
   # Install Precompiled Binary
   mkdir -p ./opt/
fi

# Install Crane
# ...

# Install Skopeo
sudo apt-get install -y skopeo
