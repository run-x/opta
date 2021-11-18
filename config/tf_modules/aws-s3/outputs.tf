output "bucket_id" {
  value = aws_s3_bucket.bucket.id
}

output "bucket_arn" {
  value = aws_s3_bucket.bucket.arn
}

output "cloudfront_read_path" {
  value = aws_cloudfront_origin_access_identity.read.cloudfront_access_identity_path
}

output "cloudfront_read_write_path" {
  value = aws_cloudfront_origin_access_identity.read_write.cloudfront_access_identity_path
}

output "cloudfront_read_write_delete_path" {
  value = aws_cloudfront_origin_access_identity.read_write_delete.cloudfront_access_identity_path
}

