variable "node-pool-name" {
  type = string
  default = "default"
}
variable "machine-type" {
  type = string
  default = "e2-standard-4"
}
variable "max-node-count" {
  type = number
  default = 3
}
variable "min-node-count" {
  type = number
  default = 3
}
variable "k8s-cluster-name" {
  type = string
}