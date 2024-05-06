#!/bin/bash

# Change to app folder
cd /opt/app

# Start the main process and save its PID
# Use exec to replace the shell script process with the main process
exec /opt/app/app.sh &
pid=$!

# Trap the SIGTERM signal and forward it to the main process
trap 'kill -SIGTERM $pid; wait $pid' SIGTERM

# Wait for the main process to complete
wait $pidh
