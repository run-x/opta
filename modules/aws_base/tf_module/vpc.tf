resource "aws_vpc" "vpc" {
  count                = local.create_vpc ? 1 : 0
  cidr_block           = var.total_ipv4_cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name      = "opta-${var.layer_name}"
    terraform = "true"
  }
}

resource "aws_default_security_group" "default" {
  count  = local.create_vpc ? 1 : 0
  vpc_id = local.vpc_id
}

resource "aws_flow_log" "vpc" {
  count           = local.create_vpc ? 1 : 0
  iam_role_arn    = aws_iam_role.vpc_flow_log[0].arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_log[0].arn
  traffic_type    = "ALL"
  vpc_id          = local.vpc_id
}

resource "random_id" "vpc_flow_log_suffix" {
  count       = local.create_vpc ? 1 : 0
  byte_length = 8
}

resource "aws_cloudwatch_log_group" "vpc_flow_log" {
  count             = local.create_vpc ? 1 : 0
  name              = "opta-${var.env_name}-vpc-flow-${random_id.vpc_flow_log_suffix[0].hex}"
  kms_key_id        = aws_kms_key.key.arn
  retention_in_days = var.vpc_log_retention
  lifecycle { ignore_changes = [name] }
}

resource "aws_iam_role" "vpc_flow_log" {
  count = local.create_vpc ? 1 : 0
  name  = "opta-${var.env_name}-vpc-flow"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "vpc-flow-logs.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "vpc_flow_log" {
  count = local.create_vpc ? 1 : 0
  name  = "opta-${var.env_name}-vpc-flow"
  role  = aws_iam_role.vpc_flow_log[0].id
  #Ignore 
  #tfsec:ignore:aws-iam-no-policy-wildcards
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
EOF
}
