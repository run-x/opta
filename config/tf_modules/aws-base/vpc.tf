resource "aws_vpc" "vpc" {
  cidr_block           = var.total_ipv4_cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name      = "opta-${var.layer_name}"
    terraform = "true"
  }
}

resource "aws_default_security_group" "default" {
  vpc_id = aws_vpc.vpc.id
}

resource "aws_flow_log" "vpc" {
  iam_role_arn    = aws_iam_role.vpc_flow_log.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_log.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.vpc.id
}

resource "aws_cloudwatch_log_group" "vpc_flow_log" {
  name              = "opta-${var.env_name}-vpc-flow"
  kms_key_id        = aws_kms_key.key.arn
  retention_in_days = 90
}

resource "aws_iam_role" "vpc_flow_log" {
  name = "opta-${var.env_name}-vpc-flow"

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
  name = "opta-${var.env_name}-vpc-flow"
  role = aws_iam_role.vpc_flow_log.id

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
