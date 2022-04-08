#!/usr/bin/env bash
set -o errexit
reg_name='opta-local-registry'
reg_port='5000'

stopped="$(docker inspect -f '{{.State.Status}}' "opta-local-cluster-control-plane" 2>/dev/null || true)"
if [ "${stopped}" == 'exited' ]; then
	echo "Found a stopped Opta local cluster docker container opta-local-cluster-control-plane, starting it again; manually clean it up if you want a new Opta Local environment."
	docker start "opta-local-cluster-control-plane"
	echo "Waiting 20s for restarted  docker container opta-local-cluster-control-plane to stabilize "
	sleep 20
	kubectl config use-context kind-opta-local-cluster
	exit 0
fi

running="$(docker inspect -f '{{.State.Status}}' "opta-local-cluster-control-plane" 2>/dev/null || true)"
if [ "${running}" == 'running' ]; then
	echo "Found a running Opta local cluster docker container opta-local-cluster-control-plane, manually clean it up if you want a new Opta Local environment."
	kubectl config use-context kind-opta-local-cluster
	exit 0
fi
# create a cluster with the local registry and nginx externalPorts enabled in containerd
cat <<EOF | $HOME/.opta/local/kind create cluster --name opta-local-cluster --kubeconfig $HOME/.kube/config --wait 5m --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
containerdConfigPatches:
- |-
  [plugins."io.containerd.grpc.v1.cri".registry.mirrors."localhost:${reg_port}"]
    endpoint = ["http://${reg_name}:${reg_port}"]
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 8080
    protocol: TCP
  - containerPort: 443
    hostPort: 6443
    protocol: TCP
EOF

kubectl config use-context kind-opta-local-cluster

# connect the registry to the cluster network
# (the network may already be connected)
docker network connect "kind" "${reg_name}" || true
