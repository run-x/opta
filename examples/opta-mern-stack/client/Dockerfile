FROM node:14
ENV JQ_VERSION=1.6

WORKDIR /app
COPY . .
RUN wget --no-check-certificate https://github.com/stedolan/jq/releases/download/jq-${JQ_VERSION}/jq-linux64 -O /tmp/jq-linux64
RUN cp /tmp/jq-linux64 /usr/bin/jq
RUN chmod +x /usr/bin/jq
RUN jq 'to_entries | map_values({ (.key) : ("$" + .key) }) | reduce .[] as $item ({}; . + $item)' ./src/config.json > ./src/config.tmp.json && mv ./src/config.tmp.json ./src/config.json
RUN npm install && npm run build

FROM nginx:1.17

ENV JSFOLDER=/usr/share/nginx/html/static/js/*.js
COPY ./start-nginx.sh /usr/bin/start-nginx.sh
RUN chmod +x /usr/bin/start-nginx.sh
WORKDIR /usr/share/nginx/html
COPY --from=0 /app/build .
ENTRYPOINT [ "start-nginx.sh" ]