variable "lambda_role_name" {
  description = "Name of the IAM role to create for Lambda"
  type        = string
  default     = "connect-lambda-exec-role"
}

variable "lexbot_role_name" {
  description = "Name of the IAM role to create for Lex Bot"
  type        = string
  default     = "lex-exec-role"
}

variable "include_lex_policy" {
  description = "Whether to attach AmazonLexFullAccess policy"
  type        = bool
  default     = true
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default = "us-east-1"
}

variable "create_role" {
  type    = bool
  default = false
}

variable "environment" {
  description = "The deployment environment(e.g., dev, uat, prod)"
  type        = string
}

variable "aws_account_id" {
  type = string
}

variable "bucket_name" {
  type = string
}

variable "lambda_name" {
  type = string
}

variable "ses_from" {
  type = string
}

variable "ses_to" {
    type = string
}
