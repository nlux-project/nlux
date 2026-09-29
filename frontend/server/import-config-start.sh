#!/bin/sh
set -e
if [ ! -f ../../frontend/config.json ]; then
  echo "Using default config"
else
  cp ../../frontend/config.json .
fi
yarn install
yarn build
