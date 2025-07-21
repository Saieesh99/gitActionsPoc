output "email_lambda_role_arn" {
  value = length(aws_iam_role.email_lambda_role) > 0 ? aws_iam_role.email_lambda_role[0].arn : null
}

output "lambda_exec_role" {
  value = length(aws_iam_role.lambda_exec_role) > 0 ? aws_iam_role.lambda_exec_role[0].arn : null
}
