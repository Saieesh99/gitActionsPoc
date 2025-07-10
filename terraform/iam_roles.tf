resource "aws_iam_role" "lambda_email_role" {
  name = "${var.lambda_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "lambda.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_policy" "lambda_email_policy" {
  name = "${var.lambda_name}-policy"

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
  role       = aws_iam_role.lambda_email_role.name
  policy_arn = aws_iam_policy.lambda_email_policy.arn
}
