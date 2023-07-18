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

output "redis-connection-string-default" {
  sensitive = true

  description = "Default secure connection string for Redis"
  value = join("",
    [
      "rediss://:",
      azurerm_redis_cache.raw-data-queue.primary_access_key,
      "@",
      azurerm_redis_cache.raw-data-queue.hostname,
      ":",
      azurerm_redis_cache.raw-data-queue.ssl_port,
      "/0?ssl_cert_reqs=required"
    ]
  )
}

output "raw-data-redis-endpoint" {
  description = "Redis cache service endpoint"
  value = join(
    ":",
    [
      azurerm_redis_cache.raw-data-queue.hostname,
      azurerm_redis_cache.raw-data-queue.ssl_port
    ]
  )
}

output "container-subnet-id" {
  description = "Subnet ID for the container subnet"
  value       = azurerm_subnet.raw-data-containers.id
}
