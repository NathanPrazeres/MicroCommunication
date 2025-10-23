output "ssh_private_key" {
  value     = tls_private_key.ssh_key.private_key_openssh
  sensitive = true
}

output "traefik_external_ip" {
  description = "Static external IP for Traefik LoadBalancer"
  value       = google_compute_address.lb_ip.address
}
