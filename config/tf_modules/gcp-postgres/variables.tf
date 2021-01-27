variable "name" {
  description = "Name of the db instance and primary db"
  type = string
}

variable "tier" {
  description = "DB tier/size"
  type = string
}

variable "gcp-network" {
  description = "Network where the db should be created"
  type = string
}
