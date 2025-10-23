resource "google_compute_address" "lb_ip" {
  name         = "k8s-lb-ip"
  region       = var.GCP_REGION
  address_type = "EXTERNAL"

  labels = {
    managed_by = "terraform"
    component  = "traefik"
  }
}
