---
title: "aws-vpn"
linkTitle: "aws-vpn"
date: 2022-04-28
draft: false
weight: 1
description: Creates an AWS VPN endpoint for folks to access their private Opta network
---

This module sets up an [AWS Client VPN Endpoint](https://aws.amazon.com/vpn/client-vpn/) for you. For those new to
this service, AWS Client VPN is AWS' implementation of a VPN which natively integrates to their networking solutions.
It follows the OpenVPN specification and can readily be connected to with the [OpenVPN Client](https://openvpn.net/vpn-client/)
(which we recommend).

As with other VPN solutions, this one is used to gain secure access to a private network, in this case the private VPC
subnets Opta provisioned for your environment. This means that when connected you should have the network access needed
to locally connect to your databases, caches, pretty much all resources in your private network that are accepting 
traffic.

## Adding VPN to your Environment
For most cases, it's actually just adding a single line for the VPN module like so:
```yaml
name: testing-vpn
org_name: runx
providers:
  aws:
    region: us-east-1
    account_id: XXXXXXXXXX
modules:
  - type: base
  - type: aws-vpn
  - type: k8s-cluster
  - type: k8s-base
```
For upcoming work, it's best to place it just after the base module instead of at the end.
Run `opta apply` and you should be good to go!

## Setting Up the Client
AWS VPN uses the OpenVPN client and the ovpn file format to set up the configuration for the connection profile. Opta
makes a default profile for you and stores it in an SSM parameter which you can fetch it from (refer to the 
`ovpn_profile_parameter_arn` output). Simply fetch the value from this parameter, write it into a .ovpn file locally
and tell your OpenVPN client to import a new profile from said file.

Our VPN uses mTLS to handle the network encryption and validation of both the server and each client connecting to it.
Opta creates a brand new Certificate Authority to provision the certs for both the servers and clients. As in larger
companies it's an important security consideration to revoke VPN access on a per-person use case, it's highly 
recommended to generate a new client key/cert for each user. This can be done in the following steps (steps 2-5
will be repeated for each new user):

1. Download the certificate and key of the CA created for your VPN. Again, we store them as SSM parameters whose 
   arns are the outputs `vpn_ca_cert_parameter_arn` and `vpn_ca_key_parameter_arn`. Name them `rootCA.crt` and
   `rootCA.key`.
2. Generate a new RSA key for your new client certificate like so `openssl genrsa -out "USER_NAME.tld.key" 2048`
3. Generate the certificate signing request like so `openssl req -new -key USER_NAME.tld.key -out USER_NAME.tld.csr`
4. Create the new certificate like so `openssl x509 -req -in USER_NAME.tld.csr -CA rootCA.crt -CAkey rootCA.key -CAcreateserial -out USER_NAME.tld.crt -days 180 -sha256`
5. Done! Your new client certificate+key are stored in the files `USER_NAME.tld.key` and `USER_NAME.tld.crt` 

To get the new OVPN profile, simply download the default one stored in SSM (`ovpn_profile_parameter_arn`) and
replace the contents of
```
<cert>
DEFAULT_CERT_HERE
</cert>
```

and 
```
<key>
DEFAULT_KEY_HERE
</key>
```
with the new key and cert just created. Create a new OpenVPN profile from it and you're done!

## Extra Info
* You will actually get logs of the VPN activity sent to AWS Cloudwatch under a log group made just for the VPN logs
  ("opta-ENV_NAME-vpn-RANDOM_STRING").
* You can monitor current connections from thr AWS console by going to the VPN endpoint resource.

## Caveats
* Note that the default client certificate and the one displayed above is set to expire after 2 years. This short
  lifetime is intentional due to the security risk of having a VPN profile be valid for too long.
* You will need to use certificate revocation lists to revoke individual certificates.