resource "aws_s3_bucket" "voicemail_bucket" {
  bucket = "your-fixed-bucket-name"
}

resource "aws_iam_role" "lambda_email_role" {
  name = "lambda_email_role"

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
  name = "LambdaEmailPolicy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = ["s3:GetObject"],
        Resource = "${aws_s3_bucket.voicemail_bucket.arn}/*"
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

resource "aws_iam_role_policy_attachment" "email_lambda_attach" {
  role       = aws_iam_role.lambda_email_role.name
  policy_arn = aws_iam_policy.lambda_email_policy.arn
}

resource "aws_lambda_function" "email_lambda" {
  function_name = "voicemail_email_lambda"
  role          = aws_iam_role.lambda_email_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.12"
  filename      = "lambda_email.zip"  # You’ll generate this with the deploy script
  environment {
    variables = {
      SES_FROM = "from@example.com"
      SES_TO   = "to@example.com"
    }
  }
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.email_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.voicemail_bucket.arn
}

resource "aws_s3_bucket_notification" "s3_eventbridge_notification" {
  bucket = aws_s3_bucket.voicemail_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.email_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "voicemails/"
    filter_suffix       = ".wav"
  }

  depends_on = [aws_lambda_permission.allow_eventbridge]
}
