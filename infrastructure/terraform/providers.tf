terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.2.0"
    }
  }
}

provider "google" {
  credentials = file(var.CREDENTIALS_PATH)
  project     = var.GCP_PROJECT_ID
  zone        = var.GCP_ZONE
  region      = var.GCP_REGION

  # optional
  add_terraform_attribution_label               = true
  terraform_attribution_label_addition_strategy = "PROACTIVE"
}
