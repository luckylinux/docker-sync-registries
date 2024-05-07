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
eval "$(shdotenv --env ${toolpath}/.env || echo \"exit $?\")"

# Get list of Images already stored in the Local Mirror
mapfile -t images < <( ${engine} exec ${LOCAL_APPS_CONTAINER_NAME} regctl repo ls ${DESTINATION_REGISTRY_HOSTNAME} )

# Initialize Previous Repository Name
previousreponame=""

# Iterate over these Images
for image in "${images[@]}"
do
   # Imagename

   # Split Path
   readarray -td"/" imagepath <<<"${image}"

   # Get Number of elements in Path
   numelements=${#imagepath[@]}

   # Get Repository
   #repository="${imagepath[0]}"
   repository=$(echo "${image}" | cut -d/ -f 1)

   # Get ImageName
   #imagearray="${imagepath[@]:1}"
   #imagename=$(IFS="/" ; echo "${imagearray[*]}")
   #imagename=""
   #counter=0
   #for i in "${imagearray[@]}"
   #do
   #   if [[ counter -eq 0 ]]
   #   then
   #      imagename="${i}"
   #   else
   #      imagename="${imagename}\///${i}"
   #   fi
   #
   #   counter=$((counter+1))
   #done
   namespace=$(echo "${image}" | cut -d/ -f 2)
   imagename=$(echo "${image}" | cut -d/ -f 3)

   # Split Tag
   #imagename=$(echo $imagenametag | sed -E "s|([0-9a-zA-Z]+):?([0-9a-zA-Z]+)?|\1|g")
   #imagetag=$(echo $imagenametag | sed -E "s|([0-9a-zA-Z]+):?([0-9a-zA-Z]+)?|\1|g")

   # Get Tags
   mapfile -t tags < <( ${engine} exec ${LOCAL_APPS_CONTAINER_NAME} regctl tag ls ${DESTINATION_REGISTRY_HOSTNAME}/${image} )

   # Echo
   if [[ "${previousreponame}" != "${repository}" ]]
   then
       echo  "${repository}:"
       echo  "    images:"
   fi
   echo -e "        ${namespace}/${imagename}:"
   for tag in "${tags[@]}"
   do
      echo -e "            - \"${tag}\""
   done

   # Store Previous value of Repository
   previousreponame="${repository}"
done
