#!/usr/bin/env sh
cp /usr/share/nginx/html/static/js/*.js /tmp

export EXISTING_VARS=$(printenv | awk -F= '{print $1}' | sed 's/^/\$/g' | paste -sd,)
for file in /tmp/*.js; do
	cat $file | envsubst $EXISTING_VARS | tee /usr/share/nginx/html/static/js/$(basename $file)
done
nginx -g 'daemon off;'
