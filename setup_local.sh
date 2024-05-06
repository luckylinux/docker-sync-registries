#!/bin/bash

# Determine toolpath if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing ${scriptpath}/${relativepath}); fi

# Load Configuration
libpath=$(readlink --canonicalize-missing "${toolpath}/includes")
source ${libpath}/functions.sh



# Optional argument
engine=${1-"podman"}



# Check if Engine Exists
engine_exists "${engine}"
if [[ $? -ne 0 ]]
then
    # Error
    echo "[CRITICAL] Neither Podman nor Docker could be found and/or the specified Engine <$engine> was not valid."
    echo "ABORTING !"
    exit 9
fi


# Load the Environment Variables into THIS Script
eval "$(shdotenv --env .env || echo \"exit $?\")"

# Architecture to use
TARGETPLATFORM=$(uname -m)

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


if [[ "${LOCAL_APPS_RUN_INSIDE_CONTAINER}" == "true" ]]
then
   # Run APPS from inside Container

   # Terminate and Remove Existing Containers if Any
   ${engine} stop --ignore ${LOCAL_APPS_CONTAINER_NAME}
   ${engine} rm --ignore ${LOCAL_APPS_CONTAINER_NAME}

   # Run Image with Infinite Loop to prevent it from automatically terminating
   ${engine} run --privileged -d --name=${LOCAL_APPS_CONTAINER_NAME} --env-file "./.env" -v "./regctl:/etc/regctl" -v "./containers:/etc/containers" -v "./supercronic:/etc/supercronic" localhost:5000/local/"${LOCAL_APPS_CONTAINER_IMAGE}"
else
   # Install APPs Locally

   # Install RegClient
   if [[ "${LOCAL_BUILD_REGCLIENT}" == "true" ]]
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

      # ...
   fi

   # Install Crane
   # ...

   # Install Skopeo
   sudo apt-get install -y skopeo
fi
