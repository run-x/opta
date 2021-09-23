#!/usr/bin/env bash

set -o errexit
echo "Installing kind"
mkdir -p $HOME/.opta/local

if [ "$(uname)" == "Darwin" ]; then
	echo "Detected Mac OS"
  curl -Lo $HOME/.opta/local/kind https://kind.sigs.k8s.io/dl/v0.11.1/kind-darwin-amd64
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
  echo "Detected LINUX"
  curl -Lo $HOME/.opta/local/kind https://kind.sigs.k8s.io/dl/v0.11.1/kind-linux-amd64
    


chmod +x $HOME/.opta/local/kind

# create registry container unless it already exists
reg_name='opta-local-registry'
reg_port='5000'
running="$(docker inspect -f '{{.State.Running}}' "${reg_name}" 2>/dev/null || true)"
if [ "${running}" != 'true' ]; then
  docker run \
    -d --restart=always -p "127.0.0.1:${reg_port}:5000" --name "${reg_name}" \
    registry:2
fi