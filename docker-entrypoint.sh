#!/bin/bash

# Change to app folder
cd /opt/app

# Execute Docker-Entrypoint
echo "Launching docker-entrypoint.sh"

# set timezone using environment
ln -snf /usr/share/zoneinfo/"${TIMEZONE:-UTC}" /etc/localtime

# Infinite loop to Troubleshoot
echo "ENABLE_INFINITE_LOOP = ${ENABLE_INFINITE_LOOP}"

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

# Launch App
python -u ./app.py
