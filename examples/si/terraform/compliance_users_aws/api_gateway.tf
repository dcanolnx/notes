resource "aws_api_gateway_rest_api" "compliance_api" {
  name        = "ComplianceAPI"
  description = "API for compliance data collection"
}

resource "aws_api_gateway_resource" "compliance_resource" {
  rest_api_id = aws_api_gateway_rest_api.compliance_api.id
  parent_id   = aws_api_gateway_rest_api.compliance_api.root_resource_id
  path_part   = "compliance"
}

resource "aws_api_gateway_method" "compliance_post_method" {
  rest_api_id   = aws_api_gateway_rest_api.compliance_api.id
  resource_id   = aws_api_gateway_resource.compliance_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id = aws_api_gateway_rest_api.compliance_api.id
  resource_id = aws_api_gateway_resource.compliance_resource.id
  http_method = aws_api_gateway_method.compliance_post_method.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.compliance_lambda.invoke_arn
}

resource "aws_api_gateway_deployment" "compliance_deployment" {
  depends_on = [
    aws_api_gateway_integration.lambda_integration
  ]

  rest_api_id = aws_api_gateway_rest_api.compliance_api.id
  stage_name  = "prod"
}
