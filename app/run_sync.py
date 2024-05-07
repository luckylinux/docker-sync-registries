#!/usr/bin/env python3

# Python Modules to interact with YAML Files
import yaml
from yaml.loader import SafeLoader

# Python Module to Load .env Files and set Environment Parameters
from dotenv import dotenv_values

# Python Module to interact with Docker Registry
#from dxf import DXF

# Pandas
import pandas as pd

# OS Library
import os

# Glob Library
import glob

# Import IPython to Display
from IPython.display import display

# Subprocess Python Module
from subprocess import Popen, PIPE, run

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

def read_config_single(filepath = 'sync.d/main.yml'):
   # Declare List
   images = []

   with open(filepath, 'r') as f:
   #    data = yaml.safe_load(f)
   #     data = list(yaml.load_all(f, Loader=SafeLoader))
      data = list(yaml.load_all(f, Loader=SafeLoader))

      # Print the values as a dictionary
      #print(data)

      # Length of list
      length = len(data)

      # Declare Dictionary for each Image as a Template
      #imageTemplate = dict(Repository = "" , Reference = "" , Name = "" , Tag = "" , Custom  = {'Value' : "" , 'Percent_Of_Rated' : ""})
      imageTemplate = dict(Registry = "" , Namespace = ""  , Repository = "" , ImageName = "" , Tag = "" , ShortArtifactReference = "" , FullyQualifiedArtifactReference = "")

      # Iterate over list
      for l in range(length):
         # Get Data of the current Iteration
         currentdata = data[l]

         # Number of elements in currentdata
         #lcurrentdata = len(currentdata)
         #print(currentdata)

         # List registries
         #registries = currentdata.items()

         #print(type(currentdata))

         #registries = currentdata["0"]

         # Iterate over currentdata
         for registry in currentdata:
            #print(registry)
            currentimages = currentdata[registry]["images"]
            #print(currentdata[registry])
            #print(currentimages)
            #print(registries)
            for im in currentimages:
               #print(im)
               tags = currentimages[im]

               for tag in tags:
                  # Start with the Template Dictionary
                  # Must use .copy() otherwise all images will point to the LAST image that has been processed !
                  image = imageTemplate.copy()

                  #print(tag)

                  # Try to exact namespace from registry
                  contents = registry.split("/")
                  if len(contents) > 1:
                     # Registry was actually in the form example.com/namespace
                     # Separate these two
                     registry = contents[0]
                     namespace = contents[1]
                     imname = im
                  else:
                     # Registry was specified on its own
                     # Try to determine namespace and image name alternatively
                     contents = im.split("/")
                     if len(contents) > 1:
                        namespace = contents[0]
                        imname = contents[1]
                     else:
                        # Couldn't find Namespace
                        # Assume it was "library" (as in Docker Hub)
                        namespace = "library"
                        imname = im

                  # Affect Properties
                  image["Registry"] =  registry
                  #image["Reference"] = registry
                  image["Namespace"] = namespace
                  image["Repository"] = "/".join([namespace , imname])
                  image["ImageName"] = imname
                  image["Tag"] = tag
                  image["ShortArtifactReference"] = im + ":" + tag
                  image["FullyQualifiedArtifactReference"] = registry + "/" + namespace + "/" + imname + ":" + tag

                  #print(image) # Works correctly

                  # Append to the list
                  images.append(image)

   # Return Result
   return images

# Read all Configuration Files
def read_config_all():
   # Initialize Images as a List
   images = []

   # Images Config Folder
   imagesconfigdir = os.path.abspath("sync.d")

   # Load Synchronization Configuration
   for filepath in glob.glob(f"{imagesconfigdir}/**/*.yml", recursive=True):
      # Build File Path from File Name
      #filepath = os.path.join(imagesconfigdir , filename)

      # Get File Name from File Path
      filename = os.path.basename(filepath)

      #print(filename)
      #print(filepath)

      # Get Images defined in the Current File
      current_images = read_config(filepath)

      # Read File
      images.extend(current_images)
      #print(current_images)
      #print(images)

   # Return Result
   return images

# Setup APPs Commands
def setup_apps_commands(config):
   # Define Container Name in case of running APPs within a Container
   containerName = config["LOCAL_APPS_CONTAINER_NAME"]

   # Get Container Engine in case of running APPs within a Container
   containerEngine = config["LOCAL_APPS_CONTAINER_ENGINE"]

   # Define Command for each APP
   if config['LOCAL_APPS_RUN_INSIDE_CONTAINER'] == "true":
      # Run APPs from inside container
      COMMAND_PODMAN = [containerEngine , "exec" , containerName , "podman"]
      COMMAND_SKOPEO = [containerEngine , "exec" , containerName , "skopeo"]
      COMMAND_REGCTL = [containerEngine , "exec" , containerName , "regctl"]
      COMMAND_REGSYNC = [containerEngine , "exec" , containerName , "regsync"]
      COMMAND_REGBOT = [containerEngine , "exec" , containerName , "regbot"]
      COMMAND_CRANE = [containerEngine , "exec" , containerName , "crane"]
   else:
      # Run APPs locally on the HOST
      # Use default PATHs if Custom ENV Path has not been set
      if config["LOCAL_APPS_PODMAN_PATH"] != "":
         COMMAND_PODMAN = [config["LOCAL_APPS_PODMAN_PATH"]]
      if config["LOCAL_APPS_SKOPEO_PATH"] != "":
         COMMAND_SKOPEO = [config["LOCAL_APPS_SKOPEO_PATH"]]
      if config["LOCAL_APPS_REGCTL_PATH"] != "":
         COMMAND_REGCTL = [config["LOCAL_APPS_REGCTL_PATH"]] 
      if config["LOCAL_APPS_REGSYNC_PATH"] != "":
         COMMAND_REGSYNC = [config["LOCAL_APPS_REGSYNC_PATH"]] 
      if config["LOCAL_APPS_REGBOT_PATH"] != "":
         COMMAND_REGBOT = [config["LOCAL_APPS_REGBOT_PATH"]] 
      if config["LOCAL_APPS_CRANE_PATH"] != "":
         COMMAND_CRANE = [config["LOCAL_APPS_CRANE_PATH"]] 

# Scan Configuration Files
def scan_configuration(images):
   # Create Dataframe and add all Images to it
   df_images = pd.DataFrame.from_records(images)
   display(df_images)
   #display(df_images)
   #display(images)
   
   # Define Manifest Digest Hashes
   #manifestdigesthashsource = [""] * df_images.shape[0]
   #manifestdigesthashdestination = [""] * df_images.shape[0]
   #print(manifestdigesthashsource)
   comparison = []
   comparisonTemplate = dict(ShortArtifactReference = "" , Status = "" , Source = "" , SourceHash = "" , Destination = "" , DestinationHash = "")

   # Iterate Over All Images
   for index, row in df_images.iterrows():
      #print(row['Registry'], row['Namespace'])

      # Fully Qualified Artifact Reference
      sourcefullyqualifiedartifactreference = row["FullyQualifiedArtifactReference"]

      # Query the Source Repository
      command_source = COMMAND_REGCTL.copy()
      command_source.extend(["manifest" , "head" , sourcefullyqualifiedartifactreference])
      #result_source = run(command_source, stdout=PIPE, stderr=PIPE, universal_newlines=True)
      result_source = run(command_source, stdout=PIPE, stderr=PIPE, universal_newlines=True , text=True)
      #text_source = result_source.stdout.splitlines(0)
      text_source = result_source.stdout.rsplit("\n")
      #text_source = result_source.stdout

      # Query the Destination Repository
      destinationfullyqualifiedartifactreference = config["DESTINATION_REGISTRY_HOSTNAME"] + "/" + sourcefullyqualifiedartifactreference
      command_destination = COMMAND_REGCTL.copy()
      command_destination.extend(["manifest" , "head" , destinationfullyqualifiedartifactreference])
      #result_destination = run(command_destination, stdout=PIPE, stderr=PIPE, universal_newlines=True)
      result_destination = run(command_destination, stdout=PIPE, stderr=PIPE, universal_newlines=True , text=True)
      #text_destination = result_destination.stdout.splitlines(0)
      text_destination = result_destination.stdout.rsplit("\n")
      #text_destination = result_destination.stdout

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

      #print(currentcomparison)

      # Append to List
      comparison.append(currentcomparison)

# Main Method
if __name__ == "__main__":
   # Load .env Environment Parameters
   config = dotenv_values(".env")

   # Setup APPs Commands
   setup_apps_commands(config)
   
   # Set Pandas DataFrame Display Properties
   pd.options.display.max_columns = 99999
   pd.options.display.max_rows = 99999
   pd.options.display.width = 4000
   
   # Read All Configuration
   images = read_all_config()
   



   # Define Images Hashes
   

   # Scan Configuration Files
   scan_configuration(images)


   #print(comparison)

   # Convert to Pandas DataFrame
   df_comparison = pd.DataFrame.from_records(comparison)



   # Print DataFrame
   display(df_comparison)

      #print(command_source)
      #print(command_destination)

      # Echo
      #print(f"Image: {fullyqualifiedartifactreference}")
      #print(f"Source hash: {result_source.stdout}")
      #print(f"Destination has: {result_destination.stdout}")

      #print(result.returncode, result.stdout, result.stderr)
      #result = run(command, stdout=PIPE, stderr=PIPE, text=True)
      #result = run(command, stdout=PIPE, stderr=PIPE, capture_output=True)
      #def auth(dxf, response):
      #   dxf.authenticate(config['DOCKERHUB_REGISTRY_USERNAME'], config['DOCKERHUB_REGISTRY_PASSWORD'], response=response)
      #
      #
      #dxf = DXF(config['DOCKERHUB_REGISTRY_HOSTNAME'] , '', auth)
      #digest = dxf.head_manifest_and_response('library/nginx:latest')
      #print(digest)

      #digest = dxf.get_digest(alias = 'nginx:latest' , platform = 'linux/amd64')
      #print(digest)
   