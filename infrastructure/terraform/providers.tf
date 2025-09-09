terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "7.2.0"
    }
  }
}

provider "google" {
  project = "agisit25-g20"
  region  = "europe-southwest1"
  zone    = "europe-southwest1-a"

  add_terraform_attribution_label               = true
  terraform_attribution_label_addition_strategy = "PROACTIVE"
}
