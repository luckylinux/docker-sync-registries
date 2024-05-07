#!/bin/bash

# Source: https://stackoverflow.com/questions/73653045/how-to-make-a-head-request-to-docker-hub-api-to-get-the-manifest

# Determine toolpath if not set already
relativepath="../" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing $scriptpath/$relativepath); fi

# Load the Environment Variables into THIS Script
eval "$(shdotenv --env ${toolpath}/.env || echo \"exit $?\")"



get_manifest() {

namespace=${1}

ref=${2}
#sha="${ref#*@}"
#if [ "$sha" = "$ref" ]; then
#  sha=""
#fi
#wosha="${ref%%@*}"
#repo="${wosha%:*}"
repo=${ref}

tag=${3}


# Different Types of Manifest
# Source: https://distribution.github.io/distribution/spec/manifest-v2-2/
# application/vnd.docker.distribution.manifest.v2+json: New image manifest format (schemaVersion = 2)
# application/vnd.docker.distribution.manifest.list.v2+json: Manifest list, aka “fat manifest”
# application/vnd.docker.container.image.v1+json: Container config JSON
# application/vnd.docker.image.rootfs.diff.tar.gzip: “Layer”, as a gzipped tar
# application/vnd.docker.image.rootfs.foreign.diff.tar.gzip: “Layer”, as a gzipped tar that should never be pushed
# application/vnd.docker.plugin.v1+json: Plugin config JSON


apia="application/vnd.docker.distribution.manifest.list.v2+json"
apib="application/vnd.docker.distribution.manifest.v2+json"
#apia=""
#apib=""
apic="application/vnd.oci.image.index.v1+json"
apid="application/vnd.oci.image.manifest.v1+json"
#apic=""
#apid=""
#apie="application/vnd.docker.container.image.v1+json"
#apif="application/vnd.docker.plugin.v1+json"
apie=""
apif=""
#apig="application/vnd.docker.image.rootfs.diff.tar.gzip"
#apih="application/vnd.docker.image.rootfs.foreign.diff.tar.gzip"
apig=""
apih=""


url="https://${DESTINATION_REGISTRY_HOSTNAME}/v2/${namespace}/${repo}/manifests/${tag}"

echo "Querying URL: $url"

#if [ "$tag" = "$wosha" ]; then
#  tag="latest"
#fi
#apio="application/vnd.oci.image.index.v1+json"
#apiol="application/vnd.oci.image.manifest.v1+json"
#apid="application/vnd.docker.distribution.manifest.v2+json"
#apidl="application/vnd.docker.distribution.manifest.list.v2+json"
#token=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${repo}:pull" \
#        | jq -r '.token')
#curl -H "Accept: ${apio}" -H "Accept: ${apiol}" -H "Accept: ${apid}" -H "Accept: ${apidl}" \
#     -H "Authorization: Bearer $token" \
#     -I -s "https://${DESTINATION_REGISTRY_HOSTNAME}/v2/${repo}/manifests/${tag}"
#curl -H "Accept: ${apio}" -H "Accept: ${apiol}" -H "Accept: ${apid}" -H "Accept: ${apidl}" \
#     -I -s "https://${DESTINATION_REGISTRY_HOSTNAME}/v2/${repo}/manifests/${tag}"
#curl -H "Accept: ${apio}" -H "Accept: ${apiol}" -H "Accept: ${apid}" -H "Accept: ${apidl}" \
#     -I -s "https://${DESTINATION_REGISTRY_HOSTNAME}/v2/namespaces/${namespace}/repositories/${repo}/tags/${tag}"
curl -H "Accept: ${apia}" -H "Accept: ${apib}" -H "Accept: ${apic}" -H "Accept: ${apid}" -H "Accept: ${apie}" -H "Accept: ${apif}" -H "Accept: ${apig}" -H "Accept: ${apih}" \
     -s "${url}" | jq .

}


# Define Counter
counter=1

# Loop
while true
do
   timestamp=$(date +"%Y%m%d-%H:%M:%S")
   digest1=$(get_manifest "docker.io" "library/nginx" "latest")
   digest2=$(get_manifest "docker.io" "library/nginx" "sha256:f04a6b017dc91ea174c360a5135150245079de4acb9d9662d9e8a4ef093a4de1")

   #hash=$(echo "$digest" | grep "docker-content-digest" | sed -E "s|docker-content-digest:\s*?(.*)|\1|g")

   echo "$digest1"
   echo -e "\n\n\n\n\n\n"
   echo "$digest2"
   #echo "$hash"

   #hash=$(./build/regclient/bin/regctl manifest head -p "linux/amd64" "docker.io/library/nginx:latest")
   #echo "Counter: ${counter} - Time: ${timestamp} - Hash: ${hash}"
   #./bin/regctl version


   sleep 10

   # Increment Counter
   counter=$((counter+1))
done


