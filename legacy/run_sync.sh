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

# Sync All Architectures
skopeo sync --scoped --src docker --dest docker --all docker.io/library/alpine:latest ${DESTINATION_REGISTRY_HOSTNAME}

# For temporary Images Transfer
#skopeo sync --scoped --src yaml --dest docker --dest-cert-dir "${DESTINATION_REGISTRY_LETSENCRYPT_CERTIFICATES}" sync.yml ${DESTINATION_REGISTRY_HOSTNAME}

# List all Images that have been uplodaded locally
skopeo inspect --raw docker://${DESTINATION_REGISTRY_HOSTNAME}/library/alpine | jq


# Or direct API call to registry ?
#https://${DESTINATION_REGISTRY_HOSTNAME}/v2/docker.io/library/nginx/manifests/latest

# Check if image is multi arch or not
# https://stackoverflow.com/questions/75252938/is-there-a-way-to-check-if-a-manifest-in-a-docker-registry-is-multi-arch-or-not

# List available tags for an image
# https://${DESTINATION_REGISTRY_HOSTNAME}/v2/docker.io/library/nginx/tags/list

# List available repositories
# https://${DESTINATION_REGISTRY_HOSTNAME}/v2/_catalog

# Some good Documentation
# https://www.christopherbiscardi.com/post/building-a-docker-registry
# https://distribution.github.io/distribution/spec/api/

# Different types of manifests
# https://distribution.github.io/distribution/spec/manifest-v2-2/


# See also these notes:
# https://stackoverflow.com/questions/57316115/get-manifest-of-a-public-docker-image-hosted-on-docker-hub-using-the-docker-regi


# This seems to work out of the box
./build/regclient/bin/regctl manifest get --host ${DESTINATION_REGISTRY_HOSTNAME} "alpine:latest" --format '{{jsonPretty .}}'
./build/regclient/bin/regctl manifest get --host ${DESTINATION_REGISTRY_HOSTNAME} "alpine@sha256:5d0da60400afb021f2d8dbfec8b7d26457e77eb8825cba90eba84319133f0efe" --format '{{jsonPretty .}}'


./build/regclient/bin/regctl manifest get --host ${DESTINATION_REGISTRY_HOSTNAME} "alpine:latest" --format '{{jsonPretty .}}'
./build/regclient/bin/regctl manifest get --host ${DESTINATION_REGISTRY_HOSTNAME} "alpine@sha256:5d0da60400afb021f2d8dbfec8b7d26457e77eb8825cba90eba84319133f0efe" --format "{{printPretty .}}"

# Try to get only the head
./build/regclient/bin/regctl manifest head --host "docker.io" "library/alpine:latest"
