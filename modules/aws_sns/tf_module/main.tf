resource "aws_sns_topic" "topic" {
  name_prefix                 = "${var.env_name}-${var.layer_name}-${var.module_name}"
  kms_master_key_id           = aws_kms_key.key.id
  fifo_topic                  = var.fifo
  content_based_deduplication = var.content_based_deduplication
  delivery_policy             = <<EOF
{
  "http": {
    "defaultHealthyRetryPolicy": {
      "minDelayTarget": 20,
      "maxDelayTarget": 20,
      "numRetries": 3,
      "numMaxDelayRetries": 0,
      "numNoDelayRetries": 0,
      "numMinDelayRetries": 0,
      "backoffFunction": "linear"
    },
    "disableSubscriptionOverrides": false,
    "defaultThrottlePolicy": {
      "maxReceivesPerSecond": 1
    }
  }
}
EOF
  lifecycle {
    ignore_changes = [name, name_prefix]
  }
}

## SNS topic policy
resource "aws_sns_topic_policy" "default" {
  arn = aws_sns_topic.topic.arn

  policy = data.aws_iam_policy_document.sns_topic_policy.json
}

data "aws_iam_policy_document" "sns_topic_policy" {
  policy_id = "__default_policy_ID"

  statement {
    actions = [
      "SNS:Subscribe",
      "SNS:SetTopicAttributes",
      "SNS:RemovePermission",
      "SNS:Receive",
      "SNS:Publish",
      "SNS:ListSubscriptionsByTopic",
      "SNS:GetTopicAttributes",
      "SNS:DeleteTopic",
      "SNS:AddPermission",
    ]

    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    resources = [
      aws_sns_topic.topic.arn,
    ]

    sid = "__default_statement_ID"
  }
}

## SQS Subscriptions
resource "aws_sns_topic_subscription" "user_updates_sqs_target" {
  count     = length(var.sqs_subscribers)
  topic_arn = aws_sns_topic.topic.arn
  protocol  = "sqs"
  endpoint  = var.sqs_subscribers[count.index]
}