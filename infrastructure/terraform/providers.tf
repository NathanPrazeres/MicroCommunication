terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.2.0"
    }
  }
}

provider "google" {
  credentials = file("agisit-2425-website-XXXXXXX.json")
  project     = var.GCP_PROJECT_ID
  zone        = var.GCP_ZONE

  # optional
  add_terraform_attribution_label               = true
  terraform_attribution_label_addition_strategy = "PROACTIVE"
}
