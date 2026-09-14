# AAA — Production Topology stub (§14.8)
#
# Hetzner-Cloud reference module. Two AZ-equivalents (locations) hosting the
# same containers defined in docker-compose.prod.yml. Provider-agnostic enough
# that swapping to Scaleway only requires changing the `provider` block.
#
# Usage:
#   tofu -chdir=infra/tofu init
#   tofu -chdir=infra/tofu workspace select staging   # or `prod`
#   tofu -chdir=infra/tofu apply
#
# This stub provisions only the network + compute primitives; secrets are
# handed off to OpenBao at first boot via cloud-init (not included here).

terraform {
  required_version = ">= 1.6"
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.45"
    }
  }
  backend "s3" {
    # State storage — fill in via environment variables or a backend.tfvars
    # See https://opentofu.org/docs/language/settings/backends/s3/
    bucket = "aaa-tofu-state"
    key    = "infra/state.tfstate"
    region = "eu-central-1"
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

# ─── Network ────────────────────────────────────────────────────────────────
resource "hcloud_network" "aaa" {
  name     = "aaa-${var.environment}"
  ip_range = "10.0.0.0/16"
}

resource "hcloud_network_subnet" "primary" {
  network_id   = hcloud_network.aaa.id
  type         = "cloud"
  network_zone = "eu-central"
  ip_range     = "10.0.1.0/24"
}

resource "hcloud_network_subnet" "secondary" {
  network_id   = hcloud_network.aaa.id
  type         = "cloud"
  network_zone = "eu-central"
  ip_range     = "10.0.2.0/24"
}

# ─── Compute (single docker-compose host per AZ for staging) ────────────────
resource "hcloud_server" "app" {
  count       = var.environment == "prod" ? 2 : 1
  name        = "aaa-app-${var.environment}-${count.index}"
  image       = "ubuntu-24.04"
  server_type = var.server_type
  location    = element(["nbg1", "fsn1"], count.index)
  ssh_keys    = var.ssh_key_ids

  network {
    network_id = hcloud_network.aaa.id
  }

  user_data = templatefile("${path.module}/cloud-init.yaml", {
    environment = var.environment
  })

  labels = {
    environment = var.environment
    role        = "aaa-app"
  }
}

# ─── Object storage (off-site backup target for restic) ─────────────────────
# Hetzner does not offer S3 directly — backups should go to Scaleway / Backblaze.
# This is a placeholder that the runbook explains how to wire up.

# ─── Outputs ────────────────────────────────────────────────────────────────
output "app_ipv4" {
  description = "Public IPv4 of each AAA application server."
  value       = [for s in hcloud_server.app : s.ipv4_address]
}

output "network_id" {
  description = "Hetzner network ID for the AAA VPC."
  value       = hcloud_network.aaa.id
}
