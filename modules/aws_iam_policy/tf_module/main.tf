resource "random_string" "policy_suffix" {
  length  = 4
  special = false
  upper   = false
}

resource "aws_iam_policy" "policy" {
  name   = "${var.env_name}-${var.layer_name}-${var.module_name}"
  policy = file(var.file)
  tags = {
    "opta-created" : true
  }
}