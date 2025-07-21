variable "bucket_name" {
  type        = string
  description = "Name of the bucket"
}

variable "create_role" {
  type        = bool
  description = "Flag to conditionally create S3 bucket"
}
