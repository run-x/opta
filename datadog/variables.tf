variable "name" {
  description = "Name of the datadog helm release"
  type = string
}

variable "api_key" {
  description = "Datadog API key"
  type = string
  default = null
}

variable "layer_name" {
  type = string
}
