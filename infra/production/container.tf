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

    environment_variables = var.container_envvar
  }

  container {
    name   = "worker"
    image  = lookup(var.container_images, "worker")
    cpu    = "0.5"
    memory = "1.5"

    ports {
      port     = 8080
      protocol = "TCP"
    }

    environment_variables = var.container_envvar
  }

  tags = {
  }
}
