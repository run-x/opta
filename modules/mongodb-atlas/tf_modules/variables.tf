variable "mongodb_atlas_project_id" {
  type        = string
  description = "The MongoDB Atlas Project Name"
}
variable "layer_name" {
  description = "Layer name"
  type        = string
}

variable "module_name" {
  description = "Module name"
  type        = string
}

variable "cloud_provider" {
  type        = string
  description = "The cloud provider to use, must be AWS, GCP or AZURE"
  validation {
    condition     = contains(["AWS", "GCP", "AZURE"], var.cloud_provider)
    error_message = "Allowed values for input_parameter are \"AWS\", \"GCP\", or \"AZURE\"."
  }
}
variable "region" {
  type        = string
  description = "MongoDB Atlas Cluster Region, must be a region for the provider given"
}
variable "mongodbversion" {
  type        = string
  description = "The Major MongoDB Version"
  default     = "4.4"
}

variable "database_name" {
  type        = string
  description = "The database in the cluster to limit the database user to, the database does not have to exist yet"
  default     = "app"
}

variable "public_nat_ips" {
  type        = list(string)
  description = "The IP address(es) from where clients can connect"
}

variable "mongodb_instance_size" {
  type        = string
  description = "MongoDB Atlas Cluster size, see this: https://docs.atlas.mongodb.com/cluster-tier/"
  default     = "M0"

}


