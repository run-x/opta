resource "aws_apigatewayv2_api" "api" {
  count         = var.expose_via_domain ? 1 : 0
  name          = "opta-${var.module_name}-${random_string.lambda.result}"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_route" "route" {
  count     = var.expose_via_domain ? 1 : 0
  api_id    = aws_apigatewayv2_api.api[0].id
  route_key = "ANY /"

  target = "integrations/${aws_apigatewayv2_integration.lambda_integration[0].id}"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  count                  = var.expose_via_domain ? 1 : 0
  api_id                 = aws_apigatewayv2_api.api[0].id
  integration_type       = "AWS_PROXY"
  payload_format_version = "2.0"
  connection_type        = "INTERNET"
  description            = "Lambda integration"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.lambda.invoke_arn
}

resource "aws_apigatewayv2_deployment" "deployment" {
  count       = var.expose_via_domain ? 1 : 0
  api_id      = aws_apigatewayv2_api.api[0].id
  description = "Lambda deployment"

  triggers = {
    redeployment = sha1("opta-v1")
  }

  lifecycle {
    create_before_destroy = true
  }
  depends_on = [aws_apigatewayv2_route.route[0]]
}


resource "aws_apigatewayv2_stage" "stage" {
  count         = var.expose_via_domain ? 1 : 0
  api_id        = aws_apigatewayv2_api.api[0].id
  deployment_id = aws_apigatewayv2_deployment.deployment[0].id
  name          = "$default"
}

# Permission
resource "aws_lambda_permission" "apigw" {
  count         = var.expose_via_domain ? 1 : 0
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda.arn
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.api[0].execution_arn}/*/*"
}
