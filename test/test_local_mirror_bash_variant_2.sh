#!/bin/bash

# Source: https://stackoverflow.com/questions/57316115/get-manifest-of-a-public-docker-image-hosted-on-docker-hub-using-the-docker-regi

# Determine toolpath if not set already
relativepath="../" # Define relative path to go from this script to the root level of the tool
if [[ ! -v toolpath ]]; then scriptpath=$(cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd ); toolpath=$(realpath --canonicalize-missing $scriptpath/$relativepath); fi

# Load the Environment Variables into THIS Script
eval "$(shdotenv --env ${toolpath}/.env || echo \"exit $?\")"

# Define Function
hub_manifest() {
ref=${1}
#sha="${ref#*@}"
#if [ "$sha" = "$ref" ]; then
#  sha=""
#fi
#wosha="${ref%%@*}"
#repo="${wosha%:*}"
repo=${ref}

tag=${2}
#if [ "$tag" = "$wosha" ]; then
#  tag="latest"
#fi



#ref="${1:-library/ubuntu:latest}"
#sha="${ref#*@}"
#if [ "$sha" = "$ref" ]; then
#  sha=""
#fi
#wosha="${ref%%@*}"
#repo="${wosha%:*}"
#tag="${wosha##*:}"
#if [ "$tag" = "$wosha" ]; then
#  tag="latest"
#fi
api="application/vnd.docker.distribution.manifest.v2+json"
apil="application/vnd.docker.distribution.manifest.list.v2+json"
#token=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${repo}:pull" \
#        | jq -r '.token')
curl -H "Accept: ${api}" -H "Accept: ${apil}" \
     -H "Authorization: Bearer $token" \
     -s "https://${DESTINATION_REGISTRY_HOSTNAME}/v2/${repo}/manifests/${sha:-$tag}" | jq .
}

# Define Counter
counter=1

# Loop
while true
do
   timestamp=$(date +"%Y%m%d-%H:%M:%S")
   manifest=$(hub_manifest "docker.io/library/nginx" "latest")

   echo $manifest

   #hash=$(echo "$digest" | grep "docker-content-digest" | sed -E "s|docker-content-digest:\s*?(.*)|\1|g")

   #echo "$digest"
   #echo "$hash"

   #hash=$(./build/regclient/bin/regctl manifest head -p "linux/amd64" "docker.io/library/nginx:latest")
   echo "Counter: ${counter} - Time: ${timestamp} - Hash: ${hash}"
   #./bin/regctl version


   sleep 2

   # Increment Counter
   counter=$((counter+1))
done

