resource "google_compute_address" "lb_ip" {
  name         = "k8s-lb-ip"
  region       = var.GCP_REGION
  address_type = "EXTERNAL"

  labels = {
    managed_by = "terraform"
    component  = "traefik"
  }
}

resource "null_resource" "inject_traefik_ip" {
  triggers = {
    ip = google_compute_address.lb_ip.address
  }

  provisioner "local-exec" {
    command = <<EOT
      sed -i "s|loadBalancerIP:.*|loadBalancerIP: ${google_compute_address.lb_ip.address}|" ../k8s-manifests/infrastructure/traefik/values.yml
    EOT
  }
}

# data "template_file" "traefik_values" {
#   template = file("${path.module}/traefik-values.tpl.yaml")
#   vars = {
#     static_ip = google_compute_address.traefik_ip.address
#   }
# }

# resource "local_file" "traefik_values" {
#   content  = data.template_file.traefik_values.rendered
#   filename = "${path.module}/k8s-manifests/infrastructure/traefik/values.yaml"
# }
