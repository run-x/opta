
resource "mongodbatlas_project_ip_access_list" "ip1" {
  project_id = var.mongodb_atlas_project_id
  ip_address = each.value
  comment    = "IP Address for accessing the cluster"
  for_each   = toset(var.public_nat_ips)
}
