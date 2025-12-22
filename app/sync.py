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
from subprocess import PIPE, run, CompletedProcess

# Time Module
# import time

# Datetime Module
from datetime import datetime

# JSON Module
import json

# Useful Material
# https://about.gitlab.com/blog/2020/11/18/docker-hub-rate-limit-monitoring/
# https://gitlab.com/gitlab-da/unmaintained/check-docker-hub-limit/-/blob/main/check_docker_hub_limit.py?ref_type=heads

# Lock File
LOCK_FILE = "/var/run/sync-registries.lock"

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

               # SYNC INTERVAL
               "SYNC_INTERVAL",
]


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


class ConfigurationManager:
    # Class Constructor
    def __init__(self,
                 environment_file: str | None = None
                 ) -> None:

        # Initialize Variable
        self.CONFIG = dict()

        # Load Environment File
        if environment_file is not None and os.path.exists(environment_file):
            # Load .env Environment File if available
            self.CONFIG.update(dotenv_values(".env"))

        # Environment Variables Override .env File
        # This is made so that compose.yml File can override .env File which is also used for local Development
        for keyname in CONFIG_KEYS:
            self.env_override_config(keyname)

    # Get Configuration Keys
    def keys(self) -> list[str]:
        return self.CONFIG.keys()

    # Get Configuration Value
    def get(self,
            key: str,
            default_value: Any | None = None
            ) -> Any:

        return self.CONFIG.get(key, default_value)

    # Override Configuration
    def env_override_config(self,
                            key: str
                            ):

        # Check if Environment Variable is set
        if os.environ.get(key) is not None:
            # If Environment Variable is set, store its value in CONFIG overriding any possible previous Value
            self.set_if_not_set(key=key,
                                default_value=os.environ.get(key)
                                )

    # Set Variable if not Set
    def set_if_not_set(self,
                       key: str,
                       default_value: Any | None,
                       type_instance: type[str | int | float] = None
                       ) -> None:

        if default_value is not None:
            # Extract Type Information from Argment
            type_instance = type(default_value)

        # Debug
        # print(f"Convert Configuration Key {key} to Instance Type {type_instance}")

        # Debug
        # print(f"Current Configuration Value set to {self.CONFIG.get(key)}")

        # Set Variable if not Set
        if key not in self.CONFIG and default_value is not None:
            # Set Default Value, ensuring that it is of the correct Type
            self.CONFIG[key] = type_instance(default_value)
        else:
            if self.CONFIG[key] is not None:
                # Make sure that the current Configuration is of the correct Type
                self.CONFIG[key] = type_instance(self.CONFIG[key])

        # Debug
        # print(f"New Configuration for Key {key} with Value {self.CONFIG[key]} of type {type(CONFIG[key])}")


class SyncRegistries:
    # Class Constructor
    def __init__(self) -> None:
        # Initialize Variables
        self.config = ConfigurationManager()

        # CONFIG_PATH containing the PATH to the Registries & Images Definition
        self.CONFIG_PATH = None

        # DATABASE_PATH containing the PATH to the Database of previous Runs
        self.DATABASE_PATH = None

        # Initialize Images as a List
        self.images = []

        # Initialize Database as a List
        self.database = []

        # Initialize Current as a List (previously manifest_digest List)
        self.current = []

        # Initialize Images fast Index as Dict
        self.images_by_source_reference = dict()
        self.images_by_destination_reference = dict()

        # Initialize Database fast Index as Dict
        self.database_by_source_reference = dict()
        # self.database_by_destination_reference = dict()

        # Set Default Configuration
        self.set_default_config()

        # Set Application Configuration
        self.configure()

        # Setup External Application Commands if required
        self.setup_external_apps_commands()

    # Set Default Configuration
    def set_default_config(self):
        # Set Default DEBUG_LEVEL
        self.config.set_if_not_set(key="DEBUG_LEVEL", default_value=1)

        # Set Default SYNC_INTERVAL
        self.config.set_if_not_set(key="SYNC_INTERVAL", default_value=1800)

        # Set Pandas DataFrame Display Properties
        pd.options.display.max_columns = 99999
        pd.options.display.max_rows = 99999
        pd.options.display.width = 4000

    # Configure App
    def configure(self):
        # Images Config Folder
        if (os.environ.get("CONFIG_BASE_PATH") is None) and ("CONFIG_BASE_PATH" not in self.config.keys()):
            # Default to build absolute Path based on Relative Path
            self.CONFIG_PATH = os.path.abspath("sync.d")
        else:
            if os.environ.get("CONFIG_BASE_PATH") is not None:
                # Prefer Environment Variable
                self.CONFIG_PATH = os.environ.get("CONFIG_BASE_PATH")
            else:
                if "CONFIG_BASE_PATH" in self.config.keys():
                    # Use Setting from .env File
                    self.CONFIG_PATH = self.config.get("CONFIG_BASE_PATH")

        if (os.environ.get("DATABASE_BASE_PATH") is None) and ("DATABASE_BASE_PATH" not in self.config.keys()):
            # Default to build absolute Path based on Relative Path
            self.DATABASE_PATH = "/var/lib/sync-registries"
        else:
            if os.environ.get("DATABASE_BASE_PATH") is not None:
                self.DATABASE_PATH = os.environ.get("DATABASE_BASE_PATH")
            else:
                if "DATABASE_BASE_PATH" in self.config.keys():
                    # Use Setting from .env File
                    self.DATABASE_PATH = self.config.get("DATABASE_BASE_PATH")

        # Set Default Configuration
        self.set_default_config()

        # Debug
        # print("Final Application Configuration")
        # pprint.pprint(CONFIG)

    # Read Single Config File
    def read_images_config_single(self,
                                  filepath='sync.d/main.yml'
                                  ) -> list[dict[str, Any]]:

        # Declare List
        images = []

        if os.path.exists(filepath):
            with open(filepath, "r", encoding="UTF-8") as f:
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
                                     SourceShortArtifactReference="",
                                     SourceFullArtifactReference="",
                                     LastCheck=0,
                                     LastUpdate=0
                                     )

                # Iterate over list
                for list_index in range(length):
                    # Get Data of the current Iteration
                    currentdata = data[list_index]

                    # Iterate over currentdata
                    for registry in currentdata:
                        currentimages = currentdata[registry]["images"]

                        # If there are any Images defined
                        if currentimages is not None:
                            for index, im in enumerate(currentimages):
                                # Debug
                                if self.config.get("DEBUG_LEVEL") > 3:
                                    print(f"[DEBUG] [{index+1} / {len(currentimages)}] Processing Image {im} under Registry {registry}")

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

                                    # Get Full Qualified Artifact Reference
                                    fullArtifactReference = registry + "/" + namespace + "/" + imname + ":" + tag

                                    # Debug
                                    if self.config.get("DEBUG_LEVEL") > 3:
                                        print(f"[DEBUG] Processing Image {fullArtifactReference}: Image {imname} with Tag {tag} from Registry {registry} with Namespace {namespace}")

                                    if fullArtifactReference not in self.images_by_source_reference.keys():
                                        # Affect Properties
                                        image["Registry"] = registry
                                        image["Namespace"] = namespace
                                        image["Repository"] = "/".join([namespace, imname])
                                        image["ImageName"] = imname
                                        image["Tag"] = tag
                                        image["SourceShortArtifactReference"] = im + ":" + tag
                                        image["SourceFullArtifactReference"] = fullArtifactReference

                                        # Append to the list
                                        images.append(image)

                                        # Store in Source Dictionary
                                        self.images_by_source_reference[fullArtifactReference] = image
                                        self.images_by_source_reference[fullArtifactReference]["Index"] = len(images) - 1

                                        # Store in Destination Dictionary
                                        destinationFullArtifactReference = self.config.get("DESTINATION_REGISTRY_HOSTNAME") + "/" + fullArtifactReference
                                        self.images_by_destination_reference[destinationFullArtifactReference] = image
                                        self.images_by_destination_reference[destinationFullArtifactReference]["Index"] = len(images) - 1

                                        # Also store in the Object
                                        self.images.append(image)
                                    else:
                                        # Display Warning
                                        print(f"[WARNING] Image {fullArtifactReference} has already been processed. Ignoring duplicated Entry.")
        else:
            print(f"ERROR: File {filepath} does NOT exist !")

        # Return Result
        return images

    # Check Lock File
    def is_lock_set(self) -> bool:
        if os.path.exists(LOCK_FILE):
            # Display Warning
            print(f"WARNING: LOCK File {LOCK_FILE} is set. Is another instance running ? Did the previous Run fail in a non-graceful Way ?")

            # Return Value
            return True
        else:
            # Return
            return False

    # Set Lock File
    def set_lock(self) -> None:
        with open(LOCK_FILE, "w") as lock_handle:
            # Generate Current Timestamp
            timestamp = str(int(datetime.now().timestamp()))
            lock_handle.write(timestamp)

    # Clear Lock File
    def clear_lock(self) -> None:
        if os.path.exists(LOCK_FILE):
            os.unlink(LOCK_FILE)

    # Read all Configuration Files
    def read_images_config_all(self) -> list[dict[str, Any]]:
        # Initialize Images as List
        images = []

        # Debug
        if self.config.get("DEBUG_LEVEL") > 3:
            print(f"[DEBUG] Load Configuration Files from {self.CONFIG_PATH}")

        # Load Synchronization Configuration
        for filepath in glob.glob(f"{self.CONFIG_PATH}/**/*.yml", recursive=True):
            # Debug
            if self.config.get("DEBUG_LEVEL") > 3:
                print(f"[DEBUG] Read Configuration File {filepath}")

            # Get File Name from File Path
            # filename = os.path.basename(filepath)

            # Get Images defined in the Current File
            current_images = self.read_images_config_single(filepath)

            # Read File
            images.extend(current_images)

        # Return Result
        return images

    # Get Database Filepath
    def get_database_filepath(self) -> str:
        # Build Database Filepath
        database_filepath = os.path.join(self.DATABASE_PATH, "db.json")

        # Return Value
        return database_filepath

    # Load Database of Previous Runs
    def load_database(self) -> list[dict[str, Any]]:
        # Get Database Filepath
        database_filepath = self.get_database_filepath()

        # Define Fallback Values (empty List & String)
        data = []
        database_file_contents = "[]"

        # Read Database File if it exists
        if os.path.exists(database_filepath):
            with open(database_filepath, "r", encoding="UTF-8") as database_file_handle:
                database_file_contents = database_file_handle.read()

        try:
            # Evaluate JSON
            data = json.loads(database_file_contents)
        except Exception as e:
            # Display Warning & Error Message
            print(f"WARNING Loading Database File {database_filepath} failed")
            print(e)

        # Save Database into Object
        self.database = data

        # Initialize Fully Qualified References Dictionary
        database_fullartifactreferences = dict()

        # Build a faster way to find Items in Database
        for index, item in enumerate(self.database):
            # Debug
            print(f"[{index+1} / {len(self.database)}] Processing Database Item {item['SourceFullArtifactReference']}")

            # Get Fully Qualified Artifact Reference
            fullArtifactReference = item.get("SourceFullArtifactReference")

            # Store in Dictionary
            database_fullartifactreferences[fullArtifactReference] = item
            database_fullartifactreferences[fullArtifactReference]["Index"] = index

        # Save Database Index in Object
        self.database_by_source_reference = database_fullartifactreferences

        # Debug
        if self.config.get("DEBUG_LEVEL") > 3:
            print("Set Database by Source Reference")
            print(json.dumps(self.database_by_source_reference,
                             sort_keys=False,
                             indent=4
                             )
                  )

        # Return Database
        return data

    # Update Images Information
    def update_images_info(self) -> None:
        # Debug
        # if self.config.get("DEBUG_LEVEL") > 3:
        #     print(f"Database by Source Reference")
        #     print(json.dumps(self.database_by_source_reference,
        #                      sort_keys=False,
        #                      indent=4
        #                      )
        #           )
           
        # Process all Images
        for index, item in enumerate(self.images):
            # Debug
            print(f"[{index+1} / {len(self.images)}] Processing Image Item {item['SourceFullArtifactReference']}")

            # Get FullArtifactReference
            fullArtifactReference = item.get("SourceFullArtifactReference")

            # Store in Dictionary
            # images_fullartifactreferences[fullArtifactReference] = item

            # Get Data from Database
            database_values = self.database_by_source_reference.get(fullArtifactReference)

            # Debug
            if self.config.get("DEBUG_LEVEL") > 5:
                print(f"Database Values for {fullArtifactReference}:")
                print(database_values)

            if database_values is not None:
                database_values_to_use = database_values.copy()

                # Update Images Information
                self.images[index]["Status"] = database_values_to_use.get("Status")
                self.images[index]["LastCheck"] = database_values_to_use.get("LastCheck")
                self.images[index]["LastUpdate"] = database_values_to_use.get("LastUpdate")
                self.images[index]["SourceHash"] = database_values_to_use.get("SourceHash")
                self.images[index]["DestinationHash"] = database_values_to_use.get("DestinationHash")
                self.images[index]["DestinationFullArtifactReference"] = database_values_to_use.get("DestinationFullArtifactReference")

    # Save Database
    def save_database(self) -> None:
        # Get Database Filepath
        database_filepath = self.get_database_filepath()

        # Get Data as String
        database_file_contents = json.dumps(self.current)

        # Save to File
        with open(database_filepath, "w", encoding="UTF-8") as database_file_handle:
            database_file_handle.write(database_file_contents)

    # Run Synchronization
    def run(self) -> None:
        # Check Lock File
        # Only allow run if there is no Lock File set !
        if self.is_lock_set() is False:
            # Set Lock
            self.set_lock()

            # Read All Configuration
            self.read_images_config_all()

            # Load Database Status
            self.load_database()

            # Update Images based on Database Information
            self.update_images_info()

            # Scan Configuration Files
            self.current = self.scan_images_manifest_digest(self.images)

            # Debug
            # if self.config.get("DEBUG_LEVEL") > 3:
            #/home/podman/containers/config/docker-sync-registries/application/sync-registries.d/main.yml     # Convert to Pandas DataFrame (only used for display Purposes)
            #     df_manifest_digest_comparison = pd.DataFrame.from_records(self.current)
            #
            #     # Print Dataframe
            #     display(df_manifest_digest_comparison)

            # Synchronize Images based on Manifest Digest Comparison
            self.sync_images_based_on_manifest_digest()

            # Save Database Status
            self.save_database()

            # Find Old Images
            self.find_old_images()

            # Clear Lock
            self.clear_lock()

            # Notes
            # List all Repositories
            # regctl repo ls docker.MYDOMAIN.TLD --limit 1000 --format='{{json .}}' --verbosity error
            #
            # # List all Tags for a given Repository
            # regctl tag ls docker.MYDOMAIN.TLD/docker.io/library/nginx
            #
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
            # Delete Image (requires REGISTRY_STORAGE_DELETE_ENABLED=true)
            # regctl image delete --referrers docker.MYDOMAIN.TLD/docker.io/library/python@sha256:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

            # Legacy
            # dxf = DXF(CONFIG['DOCKERHUB_REGISTRY_HOSTNAME'] , '', auth)
            # digest = dxf.head_manifest_and_response('library/nginx:latest')
            # print(digest)

            # digest = dxf.get_digest(alias = 'nginx:latest' , platform = 'linux/amd64')
            # print(digest)

    # Setup External APPs Commands
    def setup_external_apps_commands(self):
        # Need to be able to modify global COMMAND_XXX Variables
        global COMMAND_PODMAN, COMMAND_SKOPEO, COMMAND_REGCTL, COMMAND_REGSYNC, COMMAND_REGBOT, COMMAND_CRANE

        # Define Command for each APP
        if self.config.get("LOCAL_APPS_RUN_INSIDE_CONTAINER") == "true":
            # Define Container Name in case of running APPs within a Container
            containerName = self.config.get("LOCAL_APPS_CONTAINER_NAME")

            # Get Container Engine in case of running APPs within a Container
            containerEngine = self.config.get("LOCAL_APPS_CONTAINER_ENGINE")

            # Run APPs from inside container
            COMMAND_PODMAN = [containerEngine, "exec", containerName, "podman"]
            COMMAND_SKOPEO = [containerEngine, "exec", containerName, "skopeo"]
            COMMAND_REGCTL = [containerEngine, "exec", containerName, "regctl"]
            COMMAND_REGSYNC = [containerEngine, "exec", containerName, "regsync"]
            COMMAND_REGBOT = [containerEngine, "exec", containerName, "regbot"]
            COMMAND_CRANE = [containerEngine, "exec", containerName, "crane"]
        else:
            # Override default PATHs if Custom ENV has been set and Variable is not empty
            if "LOCAL_APPS_PODMAN_PATH" in self.config.keys():
                if strip_quotes(self.config.get("LOCAL_APPS_PODMAN_PATH")) != "":
                    COMMAND_PODMAN = [self.config.get("LOCAL_APPS_PODMAN_PATH")]

            if "LOCAL_APPS_SKOPEO_PATH" in self.config.keys():
                if strip_quotes(self.config.get("LOCAL_APPS_SKOPEO_PATH")) != "":
                    COMMAND_SKOPEO = [self.config.get("LOCAL_APPS_SKOPEO_PATH")]

            if "LOCAL_APPS_REGCTL_PATH" in self.config.keys():
                if strip_quotes(self.config.get("LOCAL_APPS_REGCTL_PATH")) != "":
                    COMMAND_REGCTL = [self.config.get("LOCAL_APPS_REGCTL_PATH")]

            if "LOCAL_APPS_REGSYNC_PATH" in self.config.keys():
                if strip_quotes(self.config.get("LOCAL_APPS_REGSYNC_PATH")) != "":
                    COMMAND_REGSYNC = [self.config.get("LOCAL_APPS_REGSYNC_PATH")]

            if "LOCAL_APPS_REGBOT_PATH" in self.config.keys():
                if strip_quotes(self.config.get("LOCAL_APPS_REGBOT_PATH")) != "":
                    COMMAND_REGBOT = [self.config.get("LOCAL_APPS_REGBOT_PATH")]

            if "LOCAL_APPS_CRANE_PATH" in self.config.keys():
                if strip_quotes(self.config.get("LOCAL_APPS_CRANE_PATH")) != "":
                    COMMAND_CRANE = [self.config.get("LOCAL_APPS_CRANE_PATH")]

    # Get Manifest Hash
    def get_manifest_hash(self,
                          full_artifact_reference: str
                          ) -> (str, CompletedProcess, int):

        command = COMMAND_REGCTL.copy()
        command.extend(["manifest", "head", full_artifact_reference])

        result = run(command,
                     stdout=PIPE,
                     stderr=PIPE,
                     universal_newlines=True,
                     text=True
                     )

        # Get Command Output
        text = result.stdout.rsplit("\n")

        # Get Manifest Hash (first Line)
        hash_value = text[0]

        # Return Result
        return (hash_value, result, result.returncode)

    # Scan Images Manifest Digest and Compare Source with Destination
    def scan_images_manifest_digest(self,
                                    images: list[dict[str, Any]]
                                    ) -> list[dict[str, Any]]:

        # Display Images that have been Registered
        # Debug
        if self.config.get("DEBUG_LEVEL") > 3:
            print("Requested Images to be synchronized")

            # Create Dataframe and add all Images to it
            df_images = pd.DataFrame.from_records(images)

            # Diplay Dataframe
            display(df_images)

        # Define Manifest Digest Hashes
        comparison = []
        comparisonTemplate = dict(SourceShortArtifactReference="",
                                  Status="",
                                  SourceFullArtifactReference="",
                                  SourceHash="",
                                  DestinationFullArtifactReference="",
                                  DestinationHash="",
                                  LastCheck=0,
                                  LastUpdate=0
                                  )

        # Iterate Over All Images
        # for index, row in df_images.iterrows():
        for index, row in enumerate(images):
            # Debug
            # print(row['Registry'], row['Namespace'])

            # Fully Qualified Artifact References
            sourcefullartifactreference = row["SourceFullArtifactReference"]
            destinationfullartifactreference = self.config.get("DESTINATION_REGISTRY_HOSTNAME") + "/" + sourcefullartifactreference

            # Get Time since last Check
            lastCheckTimestamp = row["LastCheck"]

            # Compute delta Time since last Check
            deltaTimeLastCheck = int(datetime.now().timestamp()) - lastCheckTimestamp

            # Get Data from Database
            database_index = self.get_database_index(source_fully_qualified_artifact_reference=sourcefullartifactreference)

            if database_index is not None:
                # Get Database Item
                database_item = self.database[database_index]
            else:
                # Default to empty Dictionary
                database_item = dict()

            # Get Last Update Timestamp
            lastUpdateTimestamp = database_item.get("LastUpdate")

            if deltaTimeLastCheck > self.config.get("SYNC_INTERVAL"):
                # Debug
                if self.config.get("DEBUG_LEVEL") > 3:
                    print(f"[{index+1} / {len(images)}] Check if Image {sourcefullartifactreference} has an updated Image available")

                # Query the Source Repository
                source_hash, source_result, source_retcode = self.get_manifest_hash(full_artifact_reference=sourcefullartifactreference)

                # Query the Destination Repository
                destination_hash, destination_result, destination_retcode = self.get_manifest_hash(full_artifact_reference=destinationfullartifactreference)

                # Set Time for LastCheck
                lastCheckTimestamp = int(datetime.now().timestamp())

                if (source_retcode == 0) and (destination_retcode == 0):
                    if source_hash == destination_hash:
                        syncStatus = "OK"
                    else:
                        syncStatus = "SYNC_NEEDED"
                else:
                    if source_retcode == 0:
                        syncStatus = "ERROR_RETRIEVING_MANIFEST_FROM_DESTINATION"
                    else:
                        if destination_retcode == 0:
                            syncStatus = "ERROR_RETRIEVING_MANIFEST_FROM_SOURCE"
                        else:
                            syncStatus = "ERROR_RETRIEVING_MANIFEST_FROM_BOTH"
            else:
                # Debug
                if self.config.get("DEBUG_LEVEL") > 3:
                    print(f"[{index+1} / {len(images)}] Recent Check was only {deltaTimeLastCheck} Seconds (< {self.config.get('SYNC_INTERVAL')} Seconds) ago: use Database Values for {sourcefullartifactreference}")

                # Get Source Hash
                source_hash = database_item.get("SourceHash")

                # Get Destination Hash
                destination_hash = database_item.get("DestinationHash")

                # Get Last Check Timestamp
                lastCheckTimestamp = database_item.get("LastCheck")

                # Copy Status from previous Run
                syncStatus = database_item.get("Status")

            # Current Comparison
            currentcomparison = comparisonTemplate.copy()
            currentcomparison["SourceShortArtifactReference"] = row["SourceShortArtifactReference"]
            currentcomparison["SourceFullArtifactReference"] = sourcefullartifactreference
            currentcomparison["SourceHash"] = source_hash
            currentcomparison["DestinationFullArtifactReference"] = destinationfullartifactreference
            currentcomparison["DestinationHash"] = destination_hash
            currentcomparison["LastCheck"] = lastCheckTimestamp
            currentcomparison["LastUpdate"] = lastUpdateTimestamp
            currentcomparison["Status"] = syncStatus

            # Debug current Comparison
            if self.config.get("DEBUG_LEVEL") > 5:
                print(f"Debug Comparison for Item {sourcefullartifactreference}")
                print(currentcomparison)

            # Append to List
            comparison.append(currentcomparison)

        # Debug Comparison
        if self.config.get("DEBUG_LEVEL") > 3:
            # Create Dataframe and add all Images to it
            df_comparison = pd.DataFrame.from_records(comparison)

            # Display Comparison
            print("Overall Comparison:")
            print(df_comparison)

        # Return Result
        return comparison

    # Get Database Index
    def get_database_index(self,
                           source_fully_qualified_artifact_reference: str | None = None,
                           destination_fully_qualified_artifact_reference: str | None = None,
                           ) -> int:

        # Get Dict Item by Key
        item = self.database_by_source_reference.get(source_fully_qualified_artifact_reference)

        if item is not None:
            # Return Index
            return item["Index"]
        else:
            # Return None
            return None

    # Synchronize Images based on Manifest Digest Comparison
    # This will synchronize ALL Architectures / Platforms
    def sync_images_based_on_manifest_digest(self):

        # Debug
        if self.config.get("DEBUG_LEVEL") > 3:
            # Create Dataframe from current Data
            df_debug = pd.DataFrame.from_records(self.current)

            # Filter Dataframe            
            df_filtered = df_debug[df_debug["Status"] != "OK"]

            # Display List of Images to be synchronized
            display(df_filtered)

        # Iterate Over All Images
        # Move away from Dataframe df_comparison.iterrows():
        for index, row in enumerate(self.current):
            if row["Status"] != "OK":
                # Echo
                print(f"[INFO] SYNC_NEEDED Perform Synchronization for Image {row['SourceFullArtifactReference']}")

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
                                        row["SourceFullArtifactReference"],
                                        self.config.get("DESTINATION_REGISTRY_HOSTNAME")
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
                    # Set the LastUpdate Field to the current Timestamp
                    # df_comparison.loc[index, 'LastUpdate'] = int(datetime.now().timestamp())

                    # Set the Status to OK
                    self.current[index]["Status"] = "OK"

                    # Set the LastUpdate Field to the current Timestamp
                    self.current[index]["LastUpdate"] = int(datetime.now().timestamp())

                    # text_sync = result_sync.stdout.rsplit("\n")
                    # Debug
                    # print(text_sync)

    # Format Command
    def format_command(self,
                       *args
                       ) -> list[str]:

        # Initialize String
        command = []

        # Iterate over Arguments
        for arg in args:
            # print(f"Processing Argument: {arg}")
            if isinstance(arg, list):
                # print(f"A List: {arg}")
                command.extend([str(subarg) for subarg in arg])
                # for subarg in arg:
                #     print(f"Processing Sub-Argument {subarg}")
                #     print(f"Current Command: {command}")
                #
                #     if isinstance(subarg, list):
                #         command.extend(str(self.format_command(subarg)))
                #     else:
                #         command.extend(str(self.format_command(subarg)))
            else:
                # print(f"Not a List: {arg}")
                # print(f"Current Command: {command}")
                command.append(str(arg))

        # Debug
        # print("Overall Command")
        # pprint.pprint(command)
        # print(f"Type: {type(command)}")
        # print(f"Type[0]: {type(command[0])}")

        # Return Value
        return command

    # Regctl Command
    def regctl(self,
               *args
               ) -> CompletedProcess:

        # Define Command
        command = self.format_command(COMMAND_REGCTL.copy(), *args)

        # Debug
        # print(f"Command: {command}")

        result = run(command,
                     stdout=PIPE,
                     stderr=PIPE,
                     universal_newlines=True,
                     text=True
                     )

        output = result.stdout

        # Return
        return result

    # Get Repositories from a Registry
    def get_repositories(self,
                         registry: str,
                         limit: int = 1000
                         ) -> CompletedProcess:

        # Perform Command
        result = self.regctl("repo",
                             "ls",
                             registry,
                             "--limit",
                             limit,
                             # Make sure **NOT** to add Quotes around the Format Parameter
                             # Do **NOT** use "--format='{{json .}}'" as this will add a Literal single Quote at the Beginning and End of the Output !
                             "--format={{json .}}"
                             )

        # Return Result
        return result

    # Get Tags from a given Repository
    def get_tags(self,
                 registry: str,
                 repository: str,
                 limit: int = 1000
                 ) -> CompletedProcess:

        # Perform Command
        result = self.regctl("tag",
                             "ls",
                             f"{registry}/{repository}",
                             "--limit",
                             limit,
                             # Make sure **NOT** to add Quotes around the Format Parameter
                             # Do **NOT** use "--format='{{json .}}'" as this will add a Literal single Quote at the Beginning and End of the Output !
                             "--format={{json .}}"
                             )

        # Return Result
        return result

    # Pretty JSON Print
    def json_print(self,
                   data: dict
                   ) -> None:

        print(json.dumps(data,
                         sort_keys=False,
                         indent=4
                         )
              )

    # Find Old Images
    def find_old_images(self) -> None:
        # Print Currently selected Artifacts
        print("Currently selected Artifacts")
        selected_artifacts = self.images_by_destination_reference.keys()
        for selected_artifact in selected_artifacts:
            print(f"\t- {selected_artifact}")
            
        # Initialize Artifact Dict
        destination_artifacts = dict()

        # Get Destination Registry
        destination_registry = self.config.get("DESTINATION_REGISTRY_HOSTNAME")

        # Get all Repositories on the Destination Server
        destination_repositories_result = self.get_repositories(registry=destination_registry)

        # Get data from json
        destination_repositories = json.loads(destination_repositories_result.stdout)["repositories"]

        # Print Images
        # self.json_print(destination_repositories)

        # Loop over Repositories
        for repo in destination_repositories:
            # Get all Tags
            repo_tags_result = self.get_tags(registry=destination_registry,
                                             repository=repo
                                             )

            repo_tags = json.loads(repo_tags_result.stdout)["tags"]

            # Print Tags
            # self.json_print(repo_tags)

            for repo_tag in repo_tags:
                # Build Fully Qualified Artifact Name
                fully_qualified = f"{destination_registry}/{repo}:{repo_tag}"

                # Print
                # print(fully_qualified)

                # Add to Dictionary
                destination_artifacts[fully_qualified] = dict()

        

        # Check which Artifact is NOT in the currently selected List
        print("These Images seem to be old and not desired anymore")
        
        for destination_artifact in destination_artifacts:
            if destination_artifact not in selected_artifacts:
                print(f"\t- {destination_artifact}")


# Main Method (execution as a Script)
if __name__ == "__main__":
    # Initialize Object
    app = SyncRegistries()

    # Run Synchronization
    app.run()
