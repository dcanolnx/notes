resource "aws_lambda_function" "compliance_lambda" {
  function_name    = "complianceFunction"
  filename         = "lambda.zip"
  source_code_hash = filebase64sha256("lambda.zip")
  handler          = "lambda_function.handler"  
  runtime          = "nodejs20.x"  
  role             = aws_iam_role.lambda_exec_role.arn
  vpc_config {
    subnet_ids         = [aws_subnet.my_subnet1.id, aws_subnet.my_subnet2.id]
    security_group_ids = [aws_security_group.my_sg.id]
  }
  environment {
    variables = {
      DB_HOST     = aws_db_instance.compliance_db.address,
      DB_NAME     = "compliance",
      DB_USER     = var.db_username,
      DB_PASSWORD = var.db_password,
      DB_PORT     = "3306"  
    }
  }
}

resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_exec_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com",
        },
      },
    ],
  })
}

resource "aws_iam_policy" "lambda_policy" {
  name   = "lambda_policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "rds-db:connect",
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ],
        Resource = "*"
      },
    ],
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.compliance_lambda.function_name
  principal     = "apigateway.amazonaws.com"

  # Construir el ARN de ejecución con el stage 'prod'
  source_arn = "${aws_api_gateway_rest_api.compliance_api.execution_arn}/prod/*/*"
}