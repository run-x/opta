resource "aws_s3_bucket_object" "user_files" {
  for_each     = local.files_to_upload
  bucket       = aws_s3_bucket.bucket.id
  key          = each.key
  source       = "${var.files}/${each.key}"
  content_type = lookup(local.mime_types, try(regex("\\.[^.]+$", each.key), ""), "binary/octet-stream")
  source_hash  = filemd5("${var.files}/${each.key}")
}