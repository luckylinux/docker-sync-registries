#!/bin/bash

# Determine toolpath if not set already
relativepath="./" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing $scriptpath/$relativepath); fi

# Load configuration
source $toolpath/.env

# For Production
skopeo sync --scoped --src yaml --dest docker --dest-cert-dir "${DESTINATION_REGISTRY_LETSENCRYPT_CERTIFICATES}" sync.yml ${DESTINATION_REGISTRY_HOSTNAME}


# For ARM Devices
skopeo sync --scoped --src docker --dest docker --override-arch arm --override-variant v7 docker.io/library/debian:latest ${DESTINATION_REGISTRY_HOSTNAME}

# For temporary Images Transfer
#skopeo sync --scoped --src yaml --dest docker --dest-cert-dir "${DESTINATION_REGISTRY_LETSENCRYPT_CERTIFICATES}" sync.yml ${DESTINATION_REGISTRY_HOSTNAME}
