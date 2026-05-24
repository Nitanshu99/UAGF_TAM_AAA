# AAA — Tofu module input variables (§14.8)

variable "hcloud_token" {
  description = "Hetzner Cloud API token. Provide via TF_VAR_hcloud_token, never commit."
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Deployment environment. One of: staging, prod."
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["staging", "prod"], var.environment)
    error_message = "environment must be staging or prod."
  }
}

variable "server_type" {
  description = "Hetzner server type (cx32 = 4 vCPU / 8 GB for staging; cpx41 for prod)."
  type        = string
  default     = "cx32"
}

variable "ssh_key_ids" {
  description = "List of Hetzner SSH key IDs allowed to log in as root."
  type        = list(string)
  default     = []
}
