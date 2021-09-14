#!/usr/bin/env bash
reg_name='opta-local-registry'
reg_port='5000'
# create a cluster with the local registry and nginx externalPorts enabled in containerd
cat <<EOF | ~/.opta/local/kind create cluster --name opta-local-cluster --wait 5m --kubeconfig ~/.opta/local/kubeconfig --config=-
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

# connect the registry to the cluster network
# (the network may already be connected)
docker network connect "kind" "${reg_name}" || true

# To enable ingress
# kubectl  --kubeconfig /home/sachin/.opta/kind/config apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
