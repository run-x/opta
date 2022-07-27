# Overview

This page describes how to run a [Minecraft](https://www.minecraft.net/en-us) server in AWS (on Kubernetes).

> We'll be using Opta to handle provisioning and deployment. Opta is an Infrastrucutre-as-code framework that packages
all the best practices and provides you a robust cloud setup - without being an Infrastructure expert.


**Make sure** to set the `OPS` env var to you minecraft user name. This is the field which
controls who is an admin, so it is very important for this to be set correctly.

# How it works
All the magic happens in the [minecraft-aws.yaml](./minecraft-aws.yaml) file - Opta reads this file and configures your cloud account.

We are deploying a single container version of Minecraft on EKS in AWS. It uses EBS volumes that persist between different
restorations of the container to preserve the state of the world it is hosting. It also sets up various other resources 
like VPCs, subnets, load balancers etc.


# Steps to deploy
* Fill in the required variables in the config file
* Set the `OPS` env var field to your minecraft username.
* Run `opta apply -c minecraft-aws.yaml`
* You will be prompted to approve changes a couple of times as opta will go through various stages. This is expected, just keep approving.

That's it. Minecraft is deployed on your cloud account! You can find the AWS load balancer URL to access the deployment by running `opta output`,

To start playing on this server: Start the minecraft client on your computer and on the multiplayer window, click to add a new server 
and fill in the load balancer domain as the address (do not include the "https://" prefix). Complete this client config, and jump in!

# Further Configuration
This example is using the [docker-minecraft-server](https://github.com/itzg/docker-minecraft-server) to
function. This project is well documented and has a vibrant online community that will be happy to answer 
minecraft-specific questions. Most of the configuration is determined by environment variables and you can update
this by modifying the `env_vars` field of the k8s-service module of the deployment.

# Multiple Minecraft Servers
If you wish to host multiple minecraft servers/worlds in the same environment, do the following steps:

* Create a new [Opta Service](https://docs.opta.dev/getting-started/aws/#service-creation) yaml manifest holding a new
  k8s-service module instance under the modules list (**WARNING**: this is needed because Opta currently only allows
  one k8s service per yaml manifest).
* In your new service manifest, update the `service_port` field set to 25565 to a new value (typically just increment
  by 1 in each new service yaml). Also update the original minecraft-aws.yaml and append the new port to the
  `nginx_extra_tcp_ports` list
* `opta apply` both minecraft-aws.yaml and your new yaml file.
* Your new minecraft server should be ready in the same domain which you've used in your first server, but under your
new port. This means that in the client when you  wish to connect to this server, you should set the address to
"DOMAIN_BEING_USED:NEW_PORT"
* Complete the new world config form like before an jump in!

# Cost/Management Effectiveness
Due to Opta's ~$100 overhead, this solution is initially not cost-effective in comparison to some minecraft server 
hosting sites, but it can quickly become so after several Minecraft worlds are deployed on the same environment.
As Opta creates environments in your own cloud accounts, you also retain absolute power over your resources,
capable of provisioning larger or smaller servers as you wish, and updating any configuration.

Thus, this self-cloud solution is not recommended for beginners, but rather for professional server managers/modders.

# Minecraft Server CPU and Memory concerns
Unlike common http services, Minecraft worlds were not built to be distributed and are stateful. The current set up
does not support multiple containers/servers per world, which is why the `min_containers` and `max_containers` are set
to 1. Any scaling will be done by increasing/decreasing the underlying ec2 machine and the resource requests our server
will ask of it (you can have multiple minecraft server per ec2, but we're doing a 1-1 mapping to keep the resource
request setup simple).

The ec2 machine deployed in this setup to hold your world is beefy as is (see c5.xlarge 
[here](https://aws.amazon.com/ec2/instance-types/)), but if you wish for larger instances, simply update the
`node_instance_type: "c5.xlarge"` field in the yaml to the new instance type wish you wish, and update the `cpu` and
`memory` fields under `resource_request` in the k8s-service block to just under half the cpu/memory of your new instance
(a good rule of thumb is double the current value for each C5 tier that you increase).

# Minecraft Modding
The Opta minecraft server deployed here does support minecraft modding from the Forge modes, but you will need to start 
with a new server with the `TYPE` env var set from `VANILLA` to `FORGE`. Once that has been opta-applied go inside the
server by executing:
```
opta configure-kubectl --config minecraft-aws.yaml
opta shell -c minecraft-aws.yaml
```

You should now be in a bash shell on your container. Go ahead and download your mod and place it under the typical path
in the `/data` directory. Exit out and in minecraft-aws.yaml, add a new envar `CF_SERVER_MOD: "YOUR_MODS_ZIP_FILE_NAME"`.
Opta apply once more, and your mod should now be loaded!

# Getting DNS to work
Minecraft handles its own communication encryptions so there really is no need for additional DNS
setup (e.g. TLS and using your own domain) except for cosmetics (i.e. you want to give your server a nice domain
to be connected as). If you are ready for this step, then go ahead and:

* Uncomment out the dns module block in minecraft-aws.yaml. Fill the `domain` with the domain which you own and want to use.
* Run `opta apply -c minecraft-aws.yaml`
* Run `opta output -c minecraft-aws.yaml` to get the nameservers. You will see a section like this:
```yaml
name_servers = tolist([
  “ns-1384.awsdns-45.org”,
  “ns-2001.awsdns-58.co.uk”,
  “ns-579.awsdns-08.net”,
  “ns-83.awsdns-10.com”,
])
```
* Go to your domain registrar (link namecheap, godaddy, etc.) to point the domain to these nameservers.
* Update `delegated` field to `true` in the `minecraft-aws.yaml` file.
* Run `opta apply -c minecraft-aws.yaml` again to generate the TLS certificate
* Your minecraft server should now be accessible under your domain-- go ahead and update your minecraft client config
  to point to this new domain instead of the load balancer directly.

For more information, checkout this [this tutorial](https://docs.opta.dev/tutorials/ingress/) and follow the dns
delegation steps.

# [FAQ](../FAQ.md)

For more guidance, please reach out to us in our [slack channel](https://slack.opta.dev).
