#!/usr/bin/env bash
reg_name='opta-local-registry'
reg_port='5000'
set -o errexit
echo "Installing kind"
mkdir -p ~/.opta/local
curl -Lo ~/.opta/local/kind https://kind.sigs.k8s.io/dl/v0.11.1/kind-linux-amd64
chmod +x ~/.opta/local/kind
# create registry container unless it already exists
reg_name='opta-local-registry'
reg_port='5000'
docker top "${reg_name}" 2>/dev/null  || docker run -d --restart=always -p "127.0.0.1:${reg_port}:5000" --name "${reg_name}"  registry:2
