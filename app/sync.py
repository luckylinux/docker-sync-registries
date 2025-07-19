#!/usr/bin/env python3

# Python Modules to interact with YAML Files
import yaml
from yaml.loader import SafeLoader

# Python Module to Load .env Files and set Environment Parameters
from dotenv import dotenv_values

# Pandas
import pandas as pd

# OS Library
import os

# Pprint Library
import pprint

# Glob Library
import glob

# Typing
from typing import Any

# Import IPython to Display
from IPython.display import display

# Subprocess Python Module
# from subprocess import Popen, PIPE, run
from subprocess import PIPE, run

# Useful Material
# https://about.gitlab.com/blog/2020/11/18/docker-hub-rate-limit-monitoring/
# https://gitlab.com/gitlab-da/unmaintained/check-docker-hub-limit/-/blob/main/check_docker_hub_limit.py?ref_type=heads

# Applications Commands
# Default System Paths
COMMAND_PODMAN = ["podman"]
COMMAND_SKOPEO = ["skopeo"]
COMMAND_REGCTL = ["regctl"]
COMMAND_REGSYNC = ["regsync"]
COMMAND_REGBOT = ["regbot"]
COMMAND_CRANE = ["crane"]

# List of CONFIG Keys / ENVIRONMENT VARIABLES that can be used to interface with this Application
CONFIG_KEYS = [
               # Destination Registry Settings
               "DESTINATION_REGISTRY_HOSTNAME",

               # Where Skopeo/Podman should Store the AUTH File with Credentials
               "REGISTRY_AUTH_FILE",

               # Use Container to run Applications Locally ?
               # Requires spinning up https://github.com/luckylinux/container-registry-tools
               # Otherwire requires installing all of the Tools/Libraries (Regclient, Skopeo, ...)
               # Must be set to "false" if running inside Container !
               "LOCAL_APPS_RUN_INSIDE_CONTAINER",

               # Settings for when running APPs inside Container
               "LOCAL_APPS_CONTAINER_IMAGE",
               "LOCAL_APPS_CONTAINER_NAME",
               "LOCAL_APPS_CONTAINER_ENGINE",

               # Settings for when running APPs Locally
               "LOCAL_APPS_REGCTL_PATH",
               "LOCAL_APPS_REGSYNC_PATH",
               "LOCAL_APPS_REGBOT_PATH",
               "LOCAL_APPS_CRANE_PATH",
               "LOCAL_APPS_SKOPEO_PATH",
               "LOCAL_APPS_PODMAN_PATH",

               # Enable Infinite Loop to Troubleshoot
               # Also needed if the Main Script/App doesn't have a looping itself, preventing the Container from Stopping
               "ENABLE_INFINITE_LOOP",

               # Debug Settings
               "DEBUG_LEVEL",
               # "DEBUG_LIST_PARSED_CONFIG",
]

# Initialize CONFIG containing ENV Variables
# CONFIG = dict()

# Load .env Environment Parameters
CONFIG = dotenv_values(".env")

# CONFIG_PATH containing the PATH to the Registries & Images Definition
CONFIG_PATH = ""


# Remove Quotes
def strip_quotes(text):
    # Declare result variable
    result = str(text)

    # Remove Single Quotes
    result.replace("'", "")

    # Remove Double Quotes
    result.replace('"', '')

    # Return Result
    return result


# Read Single Config File
def read_images_config_single(filepath='sync.d/main.yml'):
    # Declare List
    images = []

    with open(filepath, 'r') as f:
        # Open YAML File in Safe Mode
        # data = yaml.safe_load(f)
        data = list(yaml.load_all(f, Loader=SafeLoader))

        # Length of list
        length = len(data)

        # Declare Dictionary for each Image as a Template
        imageTemplate = dict(Registry="",
                             Namespace="",
                             Repository="",
                             ImageName="",
                             Tag="",
                             ShortArtifactReference="",
                             FullyQualifiedArtifactReference=""
                             )

        # Iterate over list
        for list_index in range(length):
            # Get Data of the current Iteration
            currentdata = data[list_index]

            # Iterate over currentdata
            for registry in currentdata:
                currentimages = currentdata[registry]["images"]
                for im in currentimages:
                    # Debug
                    if CONFIG["DEBUG_LEVEL"] > 3:
                        print(f"[DEBUG] Processing Image {im} under Registry {registry}")

                    # Get Tags associated with the current Image
                    tags = currentimages[im]

                    for tag in tags:
                        # Start with the Template Dictionary
                        # Must use .copy() otherwise all images will point to the LAST image that has been processed !
                        image = imageTemplate.copy()

                        # Try to exact namespace from registry
                        contents = registry.split("/")
                        if len(contents) > 1:
                            # Registry was actually in the form example.com/namespace
                            # Separate these two
                            if len(contents) > 2:
                                registry = contents[0]
                                namespace = "/".join(contents[1:None])
                                imname = im
                            else:
                                registry = contents[0]
                                namespace = contents[1]
                                imname = im
                        else:
                            # Try to determine namespace and image name alternatively
                            contents = im.split("/")
                            if len(contents) > 1:
                                if len(contents) > 2:
                                    namespace = "/".join(contents[0:-1])
                                    imname = contents[-1]
                                else:
                                    namespace = contents[0]
                                    imname = contents[1]
                            else:
                                # Couldn't find Namespace
                                # Assume it was "library" (as in Docker Hub)
                                namespace = "library"
                                imname = im

                        # Debug
                        if CONFIG["DEBUG_LEVEL"] > 3:
                            print(f"[DEBUG] Processing Image {imname} with Tag {tag} from Registry {registry} with Namespace {namespace}")
                        # print(f"Processing Image: {imname}")
                        # print(im)
                        # print(tag)

                        # Affect Properties
                        image["Registry"] = registry
                        image["Namespace"] = namespace
                        image["Repository"] = "/".join([namespace, imname])
                        image["ImageName"] = imname
                        image["Tag"] = tag
                        image["ShortArtifactReference"] = im + ":" + tag
                        image["FullyQualifiedArtifactReference"] = registry + "/" + namespace + "/" + imname + ":" + tag

                        # Append to the list
                        images.append(image)

    # Return Result
    return images


# Read all Configuration Files
def read_images_config_all():
    # Initialize Images as a List
    images = []

    # Load Synchronization Configuration
    for filepath in glob.glob(f"{CONFIG_PATH}/**/*.yml", recursive=True):
        # Get File Name from File Path
        # filename = os.path.basename(filepath)

        # Get Images defined in the Current File
        current_images = read_images_config_single(filepath)

        # Read File
        images.extend(current_images)

    # Return Result
    return images


# Configure App
def configure_app():
    # Need to be able to modify global Variables
    global CONFIG_PATH, CONFIG

    # Images Config Folder
    if (os.environ.get("CONFIG_BASE_PATH") is None) and ("CONFIG_BASE_PATH" not in CONFIG):
        # Default to build absolute Path based on Relative Path
        CONFIG_PATH = os.path.abspath("sync.d")
    else:
        if os.environ.get("CONFIG_BASE_PATH") is not None:
            # Prefer Environment Variable
            CONFIG_PATH = os.environ.get("CONFIG_BASE_PATH")
        else:
            if "CONFIG_BASE_PATH" in CONFIG:
                # Use Setting from .env File
                CONFIG_PATH = CONFIG["CONFIG_BASE_PATH"]

    # Environment Variables Override .env File
    # This is made so that compose.yml File can override .env File which is also used for local Development
    for keyname in CONFIG_KEYS:
        env_override_config(keyname)

    # Set Default Configuration
    set_default_config()

    # Debug
    # print("Final Application Configuration")
    # pprint.pprint(CONFIG)


# Override Configuration
def env_override_config(key):
    # Need to be able to modify global Variables
    # global CONFIG

    # Check if Environment Variable is set
    if os.environ.get(key) is not None:
        # If Environment Variable is set, store its value in CONFIG overriding any possible previous Value
        set_if_not_set(key=key,
                       default_value=os.environ.get(key)
                       )


# Set Variable if not Set
def set_if_not_set(key: str,
                   default_value: Any | None,
                   type_instance: type[str | int | float] = None
                   ) -> None:

    # Need to be able to modify global Variables
    # global CONFIG

    if default_value is not None:
        # Extract Type Information from Argment
        type_instance = type(default_value)

    # Debug
    # print(f"Convert Configuration Key {key} to Instance Type {type_instance}")

    # Debug
    # print(f"Current Configuration Value set to {CONFIG.get(key)}")

    # Set Variable if not Set
    if key not in CONFIG and default_value is not None:
        # Set Default Value, ensuring that it is of the correct Type
        CONFIG[key] = type_instance(default_value)
    else:
        if CONFIG[key] is not None:
            # Make sure that the current Configuration is of the correct Type
            CONFIG[key] = type_instance(CONFIG[key])

    # Debug
    # print(f"New Configuration for Key {key} with Value {CONFIG[key]} of type {type(CONFIG[key])}")


# Set Default Configuration
def set_default_config():
    # Need to be able to modify global Variables
    global CONFIG

    # Set Default DEBUG_LEVEL
    set_if_not_set(key="DEBUG_LEVEL", default_value=1)


# Setup External APPs Commands
def setup_external_apps_commands():
    # Need to be able to modify global COMMAND_XXX Variables
    global COMMAND_PODMAN, COMMAND_SKOPEO, COMMAND_REGCTL, COMMAND_REGSYNC, COMMAND_REGBOT, COMMAND_CRANE

    # Define Command for each APP
    if CONFIG["LOCAL_APPS_RUN_INSIDE_CONTAINER"] == "true":
        # Define Container Name in case of running APPs within a Container
        containerName = CONFIG["LOCAL_APPS_CONTAINER_NAME"]

        # Get Container Engine in case of running APPs within a Container
        containerEngine = CONFIG["LOCAL_APPS_CONTAINER_ENGINE"]

        # Run APPs from inside container
        COMMAND_PODMAN = [containerEngine, "exec", containerName, "podman"]
        COMMAND_SKOPEO = [containerEngine, "exec", containerName, "skopeo"]
        COMMAND_REGCTL = [containerEngine, "exec", containerName, "regctl"]
        COMMAND_REGSYNC = [containerEngine, "exec", containerName, "regsync"]
        COMMAND_REGBOT = [containerEngine, "exec", containerName, "regbot"]
        COMMAND_CRANE = [containerEngine, "exec", containerName, "crane"]
    else:
        # Override default PATHs if Custom ENV has been set and Variable is not empty
        if "LOCAL_APPS_PODMAN_PATH" in CONFIG:
            if strip_quotes(CONFIG["LOCAL_APPS_PODMAN_PATH"]) != "":
                COMMAND_PODMAN = [CONFIG["LOCAL_APPS_PODMAN_PATH"]]

        if "LOCAL_APPS_SKOPEO_PATH" in CONFIG:
            if strip_quotes(CONFIG["LOCAL_APPS_SKOPEO_PATH"]) != "":
                COMMAND_SKOPEO = [CONFIG["LOCAL_APPS_SKOPEO_PATH"]]

        if "LOCAL_APPS_REGCTL_PATH" in CONFIG:
            if strip_quotes(CONFIG["LOCAL_APPS_REGCTL_PATH"]) != "":
                COMMAND_REGCTL = [CONFIG["LOCAL_APPS_REGCTL_PATH"]]

        if "LOCAL_APPS_REGSYNC_PATH" in CONFIG:
            if strip_quotes(CONFIG["LOCAL_APPS_REGSYNC_PATH"]) != "":
                COMMAND_REGSYNC = [CONFIG["LOCAL_APPS_REGSYNC_PATH"]]

        if "LOCAL_APPS_REGBOT_PATH" in CONFIG:
            if strip_quotes(CONFIG["LOCAL_APPS_REGBOT_PATH"]) != "":
                COMMAND_REGBOT = [CONFIG["LOCAL_APPS_REGBOT_PATH"]]

        if "LOCAL_APPS_CRANE_PATH" in CONFIG:
            if strip_quotes(CONFIG["LOCAL_APPS_CRANE_PATH"]) != "":
                COMMAND_CRANE = [CONFIG["LOCAL_APPS_CRANE_PATH"]]


# Scan Images Manifest Digest and Compare Source with Destination
def scan_images_manifest_digest(images):
    # Create Dataframe and add all Images to it
    df_images = pd.DataFrame.from_records(images)

    # Display Images that have been Registered
    # Debug
    if CONFIG["DEBUG_LEVEL"] > 3:
        display(df_images)

    # Define Manifest Digest Hashes
    comparison = []
    comparisonTemplate = dict(ShortArtifactReference="",
                              Status="",
                              Source="",
                              SourceHash="",
                              Destination="",
                              DestinationHash=""
                              )

    # Iterate Over All Images
    for index, row in df_images.iterrows():
        # Debug
        # print(row['Registry'], row['Namespace'])

        # Fully Qualified Artifact Reference
        sourcefullyqualifiedartifactreference = row["FullyQualifiedArtifactReference"]

        # Query the Source Repository
        command_source = COMMAND_REGCTL.copy()
        command_source.extend(["manifest", "head", sourcefullyqualifiedartifactreference])

        result_source = run(command_source,
                            stdout=PIPE,
                            stderr=PIPE,
                            universal_newlines=True,
                            text=True
                            )

        text_source = result_source.stdout.rsplit("\n")

        # Query the Destination Repository
        destinationfullyqualifiedartifactreference = CONFIG["DESTINATION_REGISTRY_HOSTNAME"] + "/" + sourcefullyqualifiedartifactreference
        command_destination = COMMAND_REGCTL.copy()
        command_destination.extend(["manifest", "head", destinationfullyqualifiedartifactreference])

        result_destination = run(command_destination,
                                 stdout=PIPE,
                                 stderr=PIPE,
                                 universal_newlines=True,
                                 text=True
                                 )

        text_destination = result_destination.stdout.rsplit("\n")

        # Current Comparison
        currentcomparison = comparisonTemplate.copy()
        currentcomparison["ShortArtifactReference"] = row["ShortArtifactReference"]
        currentcomparison["Source"] = sourcefullyqualifiedartifactreference
        currentcomparison["SourceHash"] = text_source[0]
        currentcomparison["Destination"] = destinationfullyqualifiedartifactreference
        currentcomparison["DestinationHash"] = text_destination[0]

        if (result_source.returncode == 0) and (result_destination.returncode == 0):
            if currentcomparison["SourceHash"] == currentcomparison["DestinationHash"]:
                currentcomparison["Status"] = "OK"
            else:
                currentcomparison["Status"] = "SYNC_NEEDED"
        else:
            if result_source.returncode == 0:
                currentcomparison["Status"] = "ERROR_RETRIEVING_MANIFEST_FROM_DESTINATION"
            else:
                if result_destination.returncode == 0:
                    currentcomparison["Status"] = "ERROR_RETRIEVING_MANIFEST_FROM_SOURCE"
                else:
                    currentcomparison["Status"] = "ERROR_RETRIEVING_MANIFEST_FROM_BOTH"

        # Debug current Comparison
        # print(currentcomparison)

        # Append to List
        comparison.append(currentcomparison)

    # Debug Comparison
    if CONFIG["DEBUG_LEVEL"] > 3:
        print(comparison)

    # Return Result
    return comparison


# Synchronize Images based on Manifest Digest Comparison
# This will synchronize ALL Architectures / Platforms
def sync_images_based_on_manifest_digest(df_comparison):
    # Iterate Over All Images
    for index, row in df_comparison.iterrows():
        if row["Status"] != "OK":
            # Echo
            print(f"[INFO] SYNC_NEEDED Perform Synchronization for Image {row['Source']}")

            # Perform Sync
            # In --scoped mode, only the base Destination Domain must be used !
            # This is equal to CONFIG["DESTINATION_REGISTRY_HOSTNAME"]
            command_sync = COMMAND_SKOPEO.copy()
            command_sync.extend(
                                 [
                                    "sync",
                                    "--scoped",
                                    "--src",
                                    "docker",
                                    "--dest",
                                    "docker",
                                    "--all",
                                    row["Source"],
                                    CONFIG["DESTINATION_REGISTRY_HOSTNAME"]
                                 ]
                                 )
            result_sync = run(command_sync,
                              stdout=PIPE,
                              stderr=PIPE,
                              universal_newlines=True,
                              text=True
                              )

            if result_sync.returncode != 0:
                # text_sync = result_sync.stderr.rsplit("\n")
                print(f"[ERROR] {result_sync.stderr}")
            else:
                # Do nothing
                pass

                # text_sync = result_sync.stdout.rsplit("\n")
                # Debug
                # print(text_sync)


# Main Method
if __name__ == "__main__":
    # Debug
    # print(os.environ.get("PATH"))
    # for name, value in os.environ.items():
    #    print("{0}: {1}".format(name, value))

    # Load .env Environment Parameters
    # CONFIG = dotenv_values(".env")

    # Configure APP PATHs
    configure_app()

    # Setup External APPs Commands
    setup_external_apps_commands()

    # Set Pandas DataFrame Display Properties
    pd.options.display.max_columns = 99999
    pd.options.display.max_rows = 99999
    pd.options.display.width = 4000

    # Read All Configuration
    images = read_images_config_all()

    # Scan Configuration Files
    manifest_digest_comparison = scan_images_manifest_digest(images)

    # Convert to Pandas DataFrame
    df_manifest_digest_comparison = pd.DataFrame.from_records(manifest_digest_comparison)

    # Print Comparison
    # Debug
    # display(df_manifest_digest_comparison)

    # Synchronize Images based on Manifest Digest Comparison
    sync_images_based_on_manifest_digest(df_manifest_digest_comparison)

    # Notes
    # Get Manifest Digest (same for all Architectures / Platforms)
    # regctl manifest head docker.MYDOMAIN.TLD/docker.io/library/nginx:latest
    #
    # Get All Information about a particular Image
    # regctl manifest get docker.MYDOMAIN.TLD/docker.io/library/nginx:latest
    #
    # Get Digest for an Image of a particular Architecture / Platform
    # regctl image digest --platform linux/arm64 docker.MYDOMAIN.TLD/docker.io/library/nginx:latest
    # regctl manifest digest --platform linux/arm64 docker.MYDOMAIN.TLD/docker.io/library/nginx:latest
    #
    # List all Tags for a given Image
    # regctl tag ls docker.MYDOMAIN.TLD/docker.io/library/nginx

    # Legacy
    # dxf = DXF(CONFIG['DOCKERHUB_REGISTRY_HOSTNAME'] , '', auth)
    # digest = dxf.head_manifest_and_response('library/nginx:latest')
    # print(digest)

    # digest = dxf.get_digest(alias = 'nginx:latest' , platform = 'linux/amd64')
    # print(digest)
