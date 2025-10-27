output "ssh_private_key" {
  value     = tls_private_key.ssh_key.private_key_openssh
  sensitive = true
}
