output "bucket_id" {
  value = aws_s3_bucket.bucket.id
}

output "bucket_arn" {
  value = aws_s3_bucket.bucket.arn
}

output "cloudfront_read_path" {
  value = aws_cloudfront_origin_access_identity.read.cloudfront_access_identity_path
}
