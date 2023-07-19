locals {
  redis_connection_endpoint = join("", [
    "rediss://",
    ":",
    azurerm_redis_cache.raw-data-queue.primary_access_key,
    "@",
    azurerm_redis_cache.raw-data-queue.hostname,
    ":",
    azurerm_redis_cache.raw-data-queue.ssl_port,
    "/0?ssl_cert_reqs=required"
    ]
  )
}

resource "azurerm_container_group" "app" {
  name                = join("-", [var.project_name, var.deployment_environment])
  resource_group_name = azurerm_resource_group.raw-data.name
  location            = azurerm_resource_group.raw-data.location

  ip_address_type = "Private"
  subnet_ids      = [azurerm_subnet.raw-data-containers.id]
  os_type         = "Linux"

  container {
    name   = "api"
    image  = lookup(var.container_images, "api")
    cpu    = "0.5"
    memory = "1.5"

    ports {
      port     = 8000
      protocol = "TCP"
    }

    environment_variables = merge(
      var.container_envvar,
      {
        PGHOST     = azurerm_postgresql_flexible_server.raw-data.fqdn
        PGPORT     = "5432"
        PGUSER     = lookup(var.admin_usernames, "database")
        PGDATABASE = azurerm_postgresql_flexible_server_database.default-db.name
      }
    )

    secure_environment_variables = merge(
      var.container_sensitive_envvar,
      {
        PGPASSWORD            = azurerm_key_vault_secret.raw-data-db.value
        CELERY_BROKER_URL     = local.redis_connection_endpoint
        CELERY_RESULT_BACKEND = local.redis_connection_endpoint
      }
    )
  }

  container {
    name   = "worker"
    image  = lookup(var.container_images, "worker")
    cpu    = "0.5"
    memory = "1.5"

    commands = ["celery", "--app", "API.api_worker", "worker", "--loglevel=INFO"]

    ports {
      port     = 8080
      protocol = "TCP"
    }

    environment_variables = merge(
      var.container_envvar,
      {
        PGHOST     = azurerm_postgresql_flexible_server.raw-data.fqdn
        PGPORT     = "5432"
        PGUSER     = lookup(var.admin_usernames, "database")
        PGDATABASE = azurerm_postgresql_flexible_server_database.default-db.name
      }
    )

    secure_environment_variables = merge(
      var.container_sensitive_envvar,
      {
        PGPASSWORD            = azurerm_key_vault_secret.raw-data-db.value
        CELERY_BROKER_URL     = local.redis_connection_endpoint
        CELERY_RESULT_BACKEND = local.redis_connection_endpoint
      }
    )
  }

  tags = {
  }
}
