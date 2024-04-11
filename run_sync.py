#!/usr/bin/env python3

# Python Modules to interact with YAML Files
import yaml
from yaml.loader import SafeLoader

# Python Module to Load .env Files and set Environment Parameters
from dotenv import dotenv_values

# Python Module to interact with Docker Registry
from dxf import DXF



# Useful Material
# https://about.gitlab.com/blog/2020/11/18/docker-hub-rate-limit-monitoring/
# https://gitlab.com/gitlab-da/unmaintained/check-docker-hub-limit/-/blob/main/check_docker_hub_limit.py?ref_type=heads


def read_config(filename = 'sync.d/main.yml'):
   # Declare List
   images = []

   with open(filename, 'r') as f:
   #    data = yaml.safe_load(f)
   #     data = list(yaml.load_all(f, Loader=SafeLoader))
      data = list(yaml.load_all(f, Loader=SafeLoader))

      # Print the values as a dictionary
      #print(data)

      # Length of list
      length = len(data)

      # Declare Dictionary for each Image as a Template
      #imageTemplate = dict(Repository = "" , Reference = "" , Name = "" , Tag = "" , Custom  = {'Value' : "" , 'Percent_Of_Rated' : ""})
      imageTemplate = dict(Repository = "" , Reference = "" , Name = "" , Tag = "" , Short = "")

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

                  # Affect Properties
                  image["Repository"] =  registry
                  image["Reference"] = registry
                  image["Name"] = im
                  image["Tag"] = tag
                  image["Short"] = im + ":" + tag
                  image["FullyQualifiedReference"] = registry + "/" + im + ":" + tag

                  #print(image) # Works correctly

                  # Append to the list
                  images.append(image)

   # Return Result
   return images


# Main Method
if __name__ == "__main__":
   # Load .env Environment Parameters
   config = dotenv_values(".env")

   # Load Synchronization Configuration
   images = read_config('sync.d/sync.yml')
   print(images)

   #def auth(dxf, response):
   #   dxf.authenticate(config['DOCKERHUB_REGISTRY_USERNAME'], config['DOCKERHUB_REGISTRY_PASSWORD'], response=response)
   #
   #
   #dxf = DXF(config['DOCKERHUB_REGISTRY_HOSTNAME'] , '', auth)
   #digest = dxf.head_manifest_and_response('library/nginx:latest')
   #print(digest)

   #digest = dxf.get_digest(alias = 'nginx:latest' , platform = 'linux/amd64')
   #print(digest)
   