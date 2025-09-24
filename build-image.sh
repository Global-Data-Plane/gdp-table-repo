#!/bin/bash

# Fail on first error
set -e

# CONFIGURABLE VARIABLES — edit as needed
IMAGE_NAME="rickmcgeer/gdp-sidecar"
# IMAGE_TAG="latest"

# Optionally use a timestamped tag for CI/CD
IMAGE_TAG="$(date +%Y%m%d-%H%M%S)"

echo "=== Building Docker image: $IMAGE_NAME:$IMAGE_TAG ==="
docker build -t $IMAGE_NAME:$IMAGE_TAG .

echo "=== Pushing Docker image: $IMAGE_NAME:$IMAGE_TAG ==="
docker push $IMAGE_NAME:$IMAGE_TAG

echo "=== Done! Image pushed: $IMAGE_NAME:$IMAGE_TAG ==="
