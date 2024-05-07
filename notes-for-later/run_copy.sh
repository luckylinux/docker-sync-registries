#!/bin/bash

# Determine toolpath if not set already
relativepath="../" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing $scriptpath/$relativepath); fi

# Load the Environment Variables into THIS Script
eval "$(shdotenv --env ${toolpath}/.env || echo \"exit $?\")"

# Define imagespath
imagespath="$HOME/containers/local/images"

# Prune old images
podman image prune -f

# List all images
#mapfile -t images < <( podman images --all --format="{{.Repository}}" )

# List images without showing intermediary images
mapfile -t images < <( podman images --format="{{.Repository}}" )

# Iterate over images
for image in "${images[@]}"
do
    # Remove Square brackets []
    source=$(echo $image | sed 's/[][]//g')
    localname="localhost/${source}"

    # Echo
    echo "Processing Image <${source}> stored locally in <${localname}>"

    # Create directory
    mkdir -p ${imagespath}/${source}

    #podman images --filter reference="docker.io/library/traefik" --format="{{.Names}}"

    mapfile -t tags < <( podman images --filter reference="${source}" --format="{{.Tag}}" )

    for tag in "${tags[@]}"
    do
        # Echo
        echo -e "\tProcessing Tag <${tag}>"

        # Get Image ID
        mapfile -t ids < <( podman images --filter reference="${source}:${tag}" --format="{{.ID}}" )

        # Only keep the first element, they are the same anyways
        id="${ids[0]}"

        # Echo
        echo -e "\tImage ID: <${id}>"

        # Save Image to tar archive
        podman image save -m -o ${imagespath}/${source}/${tag}.tar ${id}

        # Upload to local Mirror
        skopeo copy "docker-archive:${imagespath}/${source}/${tag}.tar" "docker://${DESTINATION_REGISTRY_HOSTNAME}"
    done

    exit 9
done
