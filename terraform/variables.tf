variable "lambda_role_name" {
  description = "Name of the IAM role to create for Lambda"
  type        = string
  default     = "connect-lambda-exec-role"
}

variable "lexbot_role_name" {
  description = "Name of the IAM role to create for Lex Bot"
  type        = string
  default     = "LexExecutionRole"
}

variable "include_lex_policy" {
  description = "Whether to attach AmazonLexFullAccess policy"
  type        = bool
  default     = true
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "create_lambda_role" {
  type    = bool
  default = true
}
