FROM node:22.21.0-bookworm-slim

RUN mkdir /src
ADD . /src

# procps contains "free" command
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates wget unzip jq procps && \
    cd /src/client/ && \
    npm ci --legacy-peer-deps && \
    cp index.html.template index.html && \
    npm run typescript && \
    npx vite build && \
    cd /src/server/ && \
    yarn install && \
    yarn build && \
    cp package.json build/ && \
    mv /src/server/build /app && \
    rm -rf /src && \
    cd /app && \
    yarn install --production && \
    yarn cache clean && \
    apt-get remove -y curl wget unzip yarn && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

ADD docker/import-config-start.sh /app/

WORKDIR /app

CMD ["./import-config-start.sh"]
