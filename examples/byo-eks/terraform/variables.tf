
variable "cluster_name" {
  type        = string
  description = "EKS cluster name - where to deploy this stack"
}

variable "oidc_provider_url" {
  description = "To allow using IAM roles for service accounts, see [documentation](https://docs.aws.amazon.com/eks/latest/userguide/enable-iam-roles-for-service-accounts.html)"
  type        = string
}

variable "kubeconfig" {
  description = "kubeconfig file path, to use another authentication, edit the helm provider configuration"
  type        = string
  default     = "~/.kube/config"
}

variable "nginx_chart_version" {
  description = "ingress-nginx version, see [releases](https://github.com/kubernetes/ingress-nginx/releases)"
  type        = string
  default     = "4.0.19"
}

variable "nginx_config" {
  description = "Additional configuration for ingress-nginx. [Available options](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/configmap/#configuration-options)"
  type        = map(string)
  default     = {}
}

variable "nginx_high_availability" {
  description = "Install ingress-nginx controller in high availability (HA) mode: enable auto-scaling and set minimum replicas to 3"
  type        = bool
  default     = false
}

variable "nginx_extra_pod_annotations" {
  description = "Extra podAnnotations for nginx chart values"
  type        = map(string)
  default     = {}
}

variable "nginx_extra_service_annotations" {
  description = "Extra service.annotations for nginx chart values"
  type        = map(string)
  default     = {}
}

variable "load_balancer_cert_arn" {
  description = "specifies the ARN of one or more certificates managed by the AWS Certificate Manager. If you don't set a certificate, TLS termination will be done in the nginx-controller"
  type        = string
  default     = ""
}
