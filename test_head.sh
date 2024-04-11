#!/bin/bash

# Define Counter
counter=1

while true
do
   timestamp=$(date +"%Y%m%d-%H:%M:%S")
   hash=$(./build/regclient/bin/regctl manifest head -p "linux/amd64" "docker.io/library/nginx:latest")
   echo "Counter: ${counter} - Time: ${timestamp} - Hash: ${hash}"
   #./bin/regctl version

   # Increment Counter
   counter=$((counter+1))
done
