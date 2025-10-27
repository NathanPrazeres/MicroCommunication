locals {
  depends_on = google_compute_instance.kubernetes_worker_node

  first_worker_ip = google_compute_instance.kubernetes_worker_node[0].network_interface[0].access_config[0].nat_ip

  traefik_nodeport = "30080"
}

resource "null_resource" "inject_configs" {
  triggers = {
    worker_ip = local.first_worker_ip
  }

  provisioner "local-exec" {
    command = <<EOT
      # Update Keycloak realm
      sed -i '' 's|http://[0-9.]*:[0-9]*|http://${local.first_worker_ip}:${local.traefik_nodeport}|g' \
        ../k8s-manifests/platform/keycloak/configmap.yml

      # Update UI ConfigMap
      sed -i '' 's|"VITE_AUTH_HOST": "[^"]*"|"VITE_AUTH_HOST": "${local.first_worker_ip}"|' \
        ../k8s-manifests/app/services/ui-service/configmap.yml
      sed -i '' 's|"VITE_AUTH_PORT": "[^"]*"|"VITE_AUTH_PORT": "${local.traefik_nodeport}"|' \
        ../k8s-manifests/app/services/ui-service/configmap.yml
    EOT
  }
}
