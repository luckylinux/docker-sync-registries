# NOTE: in case the mirror only has a given architecture, podman-compose up -d or podman pull will get that image (typically amd64), even if the local architecture is e.g. arm/v7 or arm64/v8.

# In order to fix (and to be on the safe side) this one must EXPLICITELY do:

# Raspberry Pi 2
podman pull --platform "linux/arm/v7" ghcr.io/home-assistant/home-assistant:stable
# Or possibly add platform: "linux/arm/v7" in compose.yml

# Rock 5B / Raspberry Pi 4
podman pull --platform "linux/arm64/v8" ghcr.io/home-assistant/home-assistant:stable
# Or possibly add platform: "linux/arm64/v8" in compose.yml
