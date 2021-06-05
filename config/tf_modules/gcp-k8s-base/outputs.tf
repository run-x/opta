output "load_balancer_raw_ip" {
  value = google_compute_global_address.load_balancer.address
}