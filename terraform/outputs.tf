output "email_lambda_role_arn" {
  value = aws_iam_role.email_lambda_role[0].arn
}

output "lambda_exec_role" {
  value = aws_iam_role.lambda_exec_role[0].arn
}
