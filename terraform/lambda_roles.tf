resource "aws_iam_role" "email_lambda_role" {
  count      = var.create_role ? 1 : 0
  name = "${var.email_lambda_role_name}-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement: [{
      Effect = "Allow",
      Principal: {
        Service: "lambda.amazonaws.com"
      },
      Action: "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "email_lambda_basic" {
  count      = var.create_role ? 1 : 0
  role       = aws_iam_role.email_lambda_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}


resource "aws_iam_policy" "email_lambda_policy" {
  count      = var.create_role ? 1 : 0
  name = "email-lambda-policy-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = ["s3:GetObject"],
        Resource = "arn:aws:s3:::${var.bucket_name}/*"
      },
      {
        Effect = "Allow",
        Action = ["ses:SendEmail", "ses:SendRawEmail"],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = ["logs:*"],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "email_lambda_policy_attach" {
  count      = var.create_role ? 1 : 0
  role       = aws_iam_role.email_lambda_role[0].name
  policy_arn = aws_iam_policy.email_lambda_policy[0].arn

  depends_on = [
    aws_iam_policy.email_lambda_policy,
    aws_iam_role.email_lambda_role
  ]
}



resource "aws_iam_role" "lambda_exec_role" {
  count      = var.create_role ? 1 : 0
  name = "${var.lambda_role_name}-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement: [{
      Effect = "Allow",
      Principal: {
        Service: "lambda.amazonaws.com"
      },
      Action: "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  count      = var.create_role ? 1 : 0
  role       = aws_iam_role.lambda_exec_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
