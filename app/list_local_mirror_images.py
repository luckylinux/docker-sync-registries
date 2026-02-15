#!/usr/bin/env python3

# Import Library
from docker_sync_registries.utils import SyncRegistries

# Main Method (execution as a Script)
if __name__ == "__main__":
    # Initialize Object
    app = SyncRegistries()

    # Find Old Images
    app.find_old_images()
