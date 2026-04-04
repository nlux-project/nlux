#!/bin/bash

# Run from the root directory, e.g.
# $ ./docker/build-docker-image.sh

IMAGE_NAME=${IMAGE_NAME:-nlux-backend}

#docker build --platform=linux/amd64 -t $IMAGE_NAME -f docker/Dockerfile .
docker build -t $IMAGE_NAME -f docker/Dockerfile .
