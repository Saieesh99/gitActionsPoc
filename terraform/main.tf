provider "aws" {
  region  = var.aws_region
}

module "s3_bucket" {
  source = "./modules/s3"  # Optional: or define inline
  bucket_name = var.bucket_name
}

resource "aws_lambda_function" "email_lambda" {
  function_name = var.lambda_name
  role          = aws_iam_role.lambda_email_role.arn
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  filename      = "lambda_email.zip"

  environment {
    variables = {
      SES_FROM = var.ses_from
      SES_TO   = var.ses_to
    }
  }

  depends_on = [aws_iam_role_policy_attachment.email_lambda_policy_attach]
}

resource "aws_lambda_permission" "allow_s3_trigger" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.email_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = module.s3_bucket.bucket_arn
}

resource "aws_s3_bucket_notification" "s3_event" {
  bucket = module.s3_bucket.bucket_id

  lambda_function {
    lambda_function_arn = aws_lambda_function.email_lambda.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "voicemails/"
    filter_suffix       = ".wav"
  }

  depends_on = [aws_lambda_permission.allow_s3_trigger]
}
