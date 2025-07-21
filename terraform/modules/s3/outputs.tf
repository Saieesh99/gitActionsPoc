output "bucket_id" {
  value = aws_s3_bucket.this[0].id
}

output "bucket_arn" {
  value = aws_s3_bucket.this[0].arn
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.this[0].bucket
  description = "Name of the created S3 bucket"
}
