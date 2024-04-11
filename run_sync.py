#!/usr/bin/env python3

# Import Libraries
import yaml
from yaml.loader import SafeLoader

# Useful Material
# https://about.gitlab.com/blog/2020/11/18/docker-hub-rate-limit-monitoring/
# https://gitlab.com/gitlab-da/unmaintained/check-docker-hub-limit/-/blob/main/check_docker_hub_limit.py?ref_type=heads

def read_head():
   

def read_config():
   # Declare List
   images = []

   with open('sync.yml', 'r') as f:
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
   images = read_config()
   print(images)
