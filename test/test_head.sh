#!/bin/bash

# Define Counter
counter=1

while true
do
   timestamp=$(date +"%Y%m%d-%H:%M:%S")

   # Using --platform will create a GET request and you will hit RateLimit
   #hash=$(./build/regclient/bin/regctl manifest head -p "linux/amd64" "docker.io/library/nginx:latest")

   # Without --platform a HEAD request will be performed which does NOT count against RateLimit
   hash=$(./build/regclient/bin/regctl manifest head "docker.io/library/nginx:latest")
   echo "Counter: ${counter} - Time: ${timestamp} - Hash: ${hash}"
   #./bin/regctl version

   # Increment Counter
   counter=$((counter+1))
done
