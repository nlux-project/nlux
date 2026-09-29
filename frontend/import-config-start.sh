#!/bin/sh
set -e
if [ ! -f config.json ]; then
  cp config.json.template config.json
fi
npm run build
