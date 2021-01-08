data "google_project" "caller" {}

variable "name" {
  description = "Name of the environment"
  type = string
}