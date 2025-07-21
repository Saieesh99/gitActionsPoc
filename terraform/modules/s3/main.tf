resource "aws_s3_bucket" "this" {
  count  = var.create_role ? 1 : 0
  bucket = var.bucket_name
}
