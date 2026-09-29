FROM node:22.21.0-bookworm-slim

WORKDIR /app

# Copy all files
COPY import-config-start.sh /app/frontend/server/import-config-start.sh
COPY import-config-start.sh /app/frontend/client/import-config-start.sh
COPY server/package.json /app/server/package.json

COPY package.json /app/package.json
COPY config.json.template /app/config.json.template

# Install all dependencies and build
WORKDIR /app
RUN npm ci --legacy-peer-deps && \
    npm run typescript && \
    npx vite build

# Install server dependencies and build
WORKDIR /app/server
RUN yarn install && \
    yarn build && \
    cp package.json build/

# Combine client and server builds
WORKDIR /app
RUN mkdir -p /app/frontend/app && \
    cp -r client/build/* /app/frontend/app/ && \
    cp -r server/build/* /app/

# Install server production dependencies
WORKDIR /app
RUN yarn install --production && \
    yarn cache clean && \
    apt-get update && \
    apt-get install -y --no-install-recommends procps jq && \
    apt-get autoremove -y curl wget unzip yarn && \
    apt-get autoremove -y && \
    # Create default config.json if not present
    if [ ! -f config.json ]; then \
      cp config.json.template config.json; \
    fi

WORKDIR /app

# Copy the start script to root
COPY import-config-start.sh /app/

CMD ["./import-config-start.sh"]
