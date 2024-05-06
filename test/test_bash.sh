#!/bin/bash

# Source: https://stackoverflow.com/questions/73653045/how-to-make-a-head-request-to-docker-hub-api-to-get-the-manifest

get_manifest() {

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
apio="application/vnd.oci.image.index.v1+json"
apiol="application/vnd.oci.image.manifest.v1+json"
apid="application/vnd.docker.distribution.manifest.v2+json"
apidl="application/vnd.docker.distribution.manifest.list.v2+json"
token=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${repo}:pull" \
        | jq -r '.token')
curl -H "Accept: ${apio}" -H "Accept: ${apiol}" -H "Accept: ${apid}" -H "Accept: ${apidl}" \
     -H "Authorization: Bearer $token" \
     -I -s "https://registry-1.docker.io/v2/${repo}/manifests/${tag}"

}


# Define Counter
counter=1

# Loop
while true
do
   timestamp=$(date +"%Y%m%d-%H:%M:%S")
   digest=$(get_manifest "library/nginx" "latest")

   hash=$(echo "$digest" | grep "docker-content-digest" | sed -E "s|docker-content-digest:\s*?(.*)|\1|g")

   echo "$digest"
   #echo "$hash"

   #hash=$(./build/regclient/bin/regctl manifest head -p "linux/amd64" "docker.io/library/nginx:latest")
   echo "Counter: ${counter} - Time: ${timestamp} - Hash: ${hash}"
   #./bin/regctl version


   sleep 2

   # Increment Counter
   counter=$((counter+1))
done
