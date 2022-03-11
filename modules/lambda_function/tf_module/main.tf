resource "random_string" "lambda" {
  length  = 4
  upper   = false
  special = false
}

data "aws_subnet_ids" "private_subnets" {
  count  = var.vpc_id == null ? 0 : 1
  vpc_id = var.vpc_id
  tags = {
    type = "private"
  }
}

resource "aws_security_group" "lambda" {
  count  = var.vpc_id == null ? 0 : 1
  name   = "opta-${var.module_name}-${random_string.lambda.result}"
  vpc_id = var.vpc_id
}

data "aws_kms_key" "main" {
  count  = var.vpc_id == null ? 0 : 1
  key_id = "alias/opta-${var.env_name}"
}

data "aws_iam_policy_document" "lambda_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      identifiers = ["lambda.amazonaws.com"]
      type        = "Service"
    }
  }
}

resource "aws_iam_role" "iam_for_lambda" {
  name = "opta-${var.module_name}-${random_string.lambda.result}"

  assume_role_policy = data.aws_iam_policy_document.lambda_trust.json
}

resource "aws_iam_role_policy_attachment" "AWSLambdaVPCAccessExecutionRole" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy_attachment" "extra_policies_attachment" {
  count      = length(var.extra_iam_policies)
  policy_arn = var.extra_iam_policies[count.index]
  role       = aws_iam_role.iam_for_lambda.name
}

data "aws_iam_policy_document" "lambda_cloudwatch" {
  statement {
    actions = ["logs:CreateLogGroup",
      "logs:CreateLogStream",
    "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.logs.arn}"]
  }
}

resource "aws_iam_policy" "lambda_logging" {
  name        = "opta-${var.module_name}-${random_string.lambda.result}-cloudwatch"
  description = "IAM policy for logging from a lambda"
  policy      = data.aws_iam_policy_document.lambda_cloudwatch.json
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda_logging.arn
}

resource "aws_cloudwatch_log_group" "logs" {
  name              = "/aws/lambda/opta-${var.module_name}-${random_string.lambda.result}"
  kms_key_id        = var.vpc_id == null ? "" : data.aws_kms_key.main[0].arn
  retention_in_days = 14
}

resource "aws_lambda_function" "lambda" {
  function_name    = "opta-${var.module_name}-${random_string.lambda.result}"
  role             = aws_iam_role.iam_for_lambda.arn
  runtime          = var.runtime
  filename         = var.filename
  source_code_hash = filebase64sha256(var.filename)
  handler          = var.handler

  dynamic "environment" {
    for_each = length(var.env_vars) == 0 ? [] : [1]
    content {
      variables = var.env_vars
    }
  }

  dynamic "vpc_config" {
    for_each = var.vpc_id == null ? [] : [1]
    content {
      subnet_ids         = data.aws_subnet_ids.private_subnets[0].ids
      security_group_ids = [aws_security_group.lambda[0].id]
    }
  }
  depends_on = [
    aws_iam_role_policy_attachment.lambda_logs,
    aws_cloudwatch_log_group.logs,
  ]
}