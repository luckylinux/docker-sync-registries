#!/bin/bash

# Change to app folder
cd "/opt/app" || exit

# File must be in /etc/supercronic/XXX
mapfile -t files < <( find "/etc/supercronic" -type f )

# Execute Supercronic Crontabs
for file in "${files[@]}"
do
   # Run Supercronic & Redirect Output of Children processes to Docker Log:
   # https://stackoverflow.com/questions/55444469/redirecting-script-output-to-docker-logs
   supercronic -split-logs "${file}" 1> /proc/1/fd/1 2> /proc/1/fd/2 &
done

# set timezone using environment
ln -snf "/usr/share/zoneinfo/${TIMEZONE:-UTC}" "/etc/localtime"

# Launch App
python -u "./sync.py"

# Infinite loop to Troubleshoot
# Also needed if the Main Script/App doesn't have a looping itself, preventing the Container from Stopping
if [[ -v ENABLE_INFINITE_LOOP ]]
then
   if [[ "${ENABLE_INFINITE_LOOP}" == "yes" ]]
   then
       echo "Starting Infinite Loop"
       while true
       do
          sleep 5
       done
   fi
fi
