output "load_balancer_raw_ip" {
  value = var.nginx_enabled ? google_compute_global_address.load_balancer[0].address : ""
}