output "ssh_private_key" {
  value     = tls_private_key.ssh_key.private_key_openssh
  sensitive = true
}

output "master_static_ip" {
  value = google_compute_address.master_ip.address
}
