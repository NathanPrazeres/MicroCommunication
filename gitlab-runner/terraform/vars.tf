# Blank var for use by terraform.tfvars
variable "token_secret" {
}
# Blank var for use by terraform.tfvars
variable "token_id" {
}

variable "template_name" {
  type        = string
  description = "OS template to be used when creating LXC"
  default     = "debian-12-standard_12.7-1_amd64.tar.zst"
}
