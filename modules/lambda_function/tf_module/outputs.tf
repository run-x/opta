output "function_name" {
  value = aws_lambda_function.lambda.function_name
}

output "function_arn" {
  value = aws_lambda_function.lambda.arn
}

output "cloudwatch_log_group_name" {
  value = aws_cloudwatch_log_group.logs.name
}

output "cloudwatch_log_group_url" {
  value = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#logsV2:log-groups/log-group/${urlencode(aws_cloudwatch_log_group.logs.name)}"
}

output "lambda_trigger_uri" {
  value = var.expose_via_domain ? aws_apigatewayv2_stage.stage[0].invoke_url : ""
}