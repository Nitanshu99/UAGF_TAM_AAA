# OpenBao server configuration for the production overlay
# (docker-compose.prod.yml mounts this at /openbao/config/config.hcl).
#
# The local profile runs `server -dev`: in-memory storage, auto-unsealed, a
# fixed root token. None of that is acceptable once real Stage C credentials
# exist. This config gives the vault durable file storage on a named volume;
# the operator still has to run `bao operator init` once and unseal after
# every restart (or wire an auto-unseal seal stanza) — see infra/runbook.md.

# The openbao/openbao:2.0.0 image ships without the web UI ("OpenBao UI is
# not available in this binary"); the HTTP API and `bao` CLI are the interface.
ui = false
disable_mlock = false

storage "file" {
  path = "/openbao/data"
}

# Plaintext on the compose network only: no host port is published in the
# production overlay and TLS terminates at the reverse proxy in front of the
# stack (ARCHITECTURE §14.8). Put certificates here and set tls_disable = 0
# if the vault is ever reachable from outside that network.
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 1
}

api_addr = "http://openbao:8200"
