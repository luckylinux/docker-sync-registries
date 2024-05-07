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

# Login to the required Registries
Login needs to be done manually and for each APP separately.

Typically this includes running the following commands for the DESTINATION REGISTRY as well as ALL SOURCE REGISTRIES:
- `skopeo login`
- `regctl login`

When using the APPs within a Container, the easiest is to Enter into the Container and execute these commands natively:
```
# Enter the Container Shell
podman exec -it container-registry-tools /bin/bash
```

Then setup all the required logins:
```
# Setup Login for Docker Hub
skopeo login docker.io
regctl login docker.io

# Setup Login for Destination Registry
skopeo login docker.MYDOMAIN.TLD
regctl login docker.MYDOMAIN.TLD
```