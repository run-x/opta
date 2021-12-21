output "db_user" {
  value = aws_db_instance.mysql.username
}

output "db_password" {
  value     = aws_db_instance.mysql.password
  sensitive = true
}

output "db_host" {
  value = aws_db_instance.mysql.endpoint
}

output "db_name" {
  value = aws_db_instance.mysql.name
}