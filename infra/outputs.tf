output "raw-data-backend-public-IP" {
  value       = azurerm_public_ip.raw-data-backend.ip_address
  description = "Public SSH-able IP address for the raw-data backend VM"
}

output "raw-data-db-endpoint" {
  value       = azurerm_postgresql_flexible_server.raw-data.fqdn
  description = "FQDN to connect to raw-data API PostgreSQL DB"
}

output "default_backend_ssh_string" {
  description = "SSH string to use to connect to the backend VM"
  value = join(
    "",
    [
      "ssh ",
      lookup(var.admin_usernames, "backend"),
      "@",
      azurerm_public_ip.raw-data-backend.ip_address
    ]
  )
}