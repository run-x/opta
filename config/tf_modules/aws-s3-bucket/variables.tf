variable "bucket_name" {
  type = string
}

variable "block_public" {
  type = bool
  default = true
}

variable "bucket_policy" {
  type = map(any)
  default = null
}

