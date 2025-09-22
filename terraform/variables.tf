variable "GCP_PROJECT_ID" {
  type        = string
  description = "The project ID found in the GCP dashboard page under the project's name."
  default     = "agisit-g20"
}

variable "GCP_MACHINE_TYPE" {
  type        = string
  description = "The machine type used to run the Kubernetes Nodes. Defaults to a small 4GB RAM machine with a 1 core vCPU."
  default     = "e2-medium"
}

variable "GCP_REGION" {
  type        = string
  description = "Region where the GCP instances will be deployed."
  default     = "europe-southwest1"
}

variable "GCP_ZONE" {
  type        = string
  description = "Zone inside the region where the GCP instances will be deployed."
  default     = "europe-southwest1-a"
}

variable "LINUX_IMAGE" {
  type        = string
  description = "Linux image to be used in the GCP instances."
  default     = "debian-12-bookworm-v20250910"
}

variable "GCE_HOSTNAME" {
  type        = string
  description = "Hostname of the Google Cloud Engine instance that manages VMs"
  default     = "debian"
}

variable "CREDENTIALS_PATH" {
  type        = string
  description = "Path to the JSON file containing the credentials for the GCP account"
  default     = "~/service-account.json"
}

# Minimum required
# variable "DISK_SIZE" {
#   type    = string
#   default = "15"
# }
