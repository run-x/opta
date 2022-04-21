resource "aws_sqs_queue" "terraform_queue" {
  name                        = var.fifo ? "${var.env_name}-${var.layer_name}-${var.module_name}.fifo" : "${var.env_name}-${var.layer_name}-${var.module_name}"
  kms_master_key_id           = aws_kms_key.key.id
  fifo_queue                  = var.fifo
  content_based_deduplication = var.content_based_deduplication
  delay_seconds               = var.delay_seconds
  message_retention_seconds   = var.message_retention_seconds
  receive_wait_time_seconds   = var.receive_wait_time_seconds

  tags = {
    Environment = "production"
  }
}

## SQS Queue policy
resource "aws_sqs_queue_policy" "default" {

  policy    = data.aws_iam_policy_document.sqs_queue_policy.json
  queue_url = aws_sqs_queue.terraform_queue.id
}

data "aws_iam_policy_document" "sqs_queue_policy" {
  policy_id = "__default_policy_ID"

  statement {
    actions = [
      # Accept the risk
      #tfsec:ignore:aws-sqs-no-wildcards-in-policy-documents
      "SQS:*"
    ]

    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    resources = [
      aws_sqs_queue.terraform_queue.arn,
    ]

    sid = "__default_statement_ID"
  }

  statement {
    # Accept the risk
    #tfsec:ignore:aws-sqs-no-wildcards-in-policy-documents
    actions = [
      "SQS:*"
    ]
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }

    resources = [
      aws_sqs_queue.terraform_queue.arn,
    ]

    sid = "sns_access"
  }

  statement {
    # Accept the risk
    #tfsec:ignore:aws-sqs-no-wildcards-in-policy-documents
    actions = [
      "SQS:*"
    ]
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }

    resources = [
      aws_sqs_queue.terraform_queue.arn,
    ]

    sid = "events_access"
  }
}