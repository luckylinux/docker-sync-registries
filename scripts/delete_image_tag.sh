#!/bin/bash

# Get Image Full Reference
image_reference="$1"

# Get Image Tag
image_tag="$2"

# Get Image Digest
image_digest=$(regctl image digest "${image_reference}:${image_tag}")

# Delete Image
regctl image delete --referrers "${image_reference}@${image_digest}"
