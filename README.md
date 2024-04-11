# docker-sync-registries
A tool to sync Docker/Podman Images Registries using skopeo without incurring in Dockerhub Ratelimit Error

# Setup
```
## Create a new Python venv
python -m venv venv

## Activate venv
source venv/bin/activate

## Install requirements (upgrade if needed)
pip install -r requirements.txt
pip install --upgrade -r requirements.txt
```

# Define Variables
Some parameters will need to be defined in the `.env` file.

To do so:
```
# Copy Example File
cp .env.example .env

# Modify using your preferred Text Editor
nano .env
```

# Define Images to be Synchronized
The Images to be Synchronized are listed in `conf.d`.

To do so:
```
# Copy Example Folder
cp -r conf.d.example conf.d

# Modify using your preferred Text Editor 
nano conf.d/sync.yml
```
