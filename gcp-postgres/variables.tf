variable "name" {
  description = "Name of the db instance and primary db"
  type = string
}

variable "gcp_project" {
  description = "GCP project where the db should be created"
  type = string
}

variable "tier" {
  description = "DB tier/size"
  type = string
}

variable "gcp_network" {
  description = "Network where the db should be created"
  type = string
}

variable "db_password" {
  description = "Password for the primary db"
  type = string
  sensitive = true
}
