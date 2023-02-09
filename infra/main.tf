
data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "raw-data" {
  name     = var.project_name
  location = var.arm_location
}

resource "azurerm_virtual_network" "raw-data" {
  name                = join("-", [var.project_name, var.deployment_environment])
  resource_group_name = azurerm_resource_group.raw-data.name
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.raw-data.location
  tags = {
  }
}

resource "azurerm_subnet" "raw-data" {
  name                 = join("-", [var.project_name, var.deployment_environment])
  resource_group_name  = azurerm_resource_group.raw-data.name
  virtual_network_name = azurerm_virtual_network.raw-data.name
  address_prefixes     = [cidrsubnet(azurerm_virtual_network.raw-data.address_space[0], 8, 0)]
}

resource "random_string" "raw_data_db_password" {
  length           = 20
  override_special = "*()-_=+[]{}<>"
}

resource "azurerm_key_vault" "raw-data" {
  name                = join("-", [var.project_name, var.deployment_environment])
  location            = azurerm_resource_group.raw-data.location
  resource_group_name = azurerm_resource_group.raw-data.name
  sku_name            = "standard"
  tenant_id           = data.azurerm_client_config.current.tenant_id

  enabled_for_deployment          = false
  enabled_for_disk_encryption     = false
  enabled_for_template_deployment = true
  enable_rbac_authorization       = false

  network_acls {
    bypass                     = "AzureServices"
    default_action             = "Allow" // Todo: Deny
    ip_rules                   = []
    virtual_network_subnet_ids = [azurerm_subnet.raw-data.id]
  }

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    certificate_permissions = [
    ]

    key_permissions = [
    ]

    secret_permissions = [
      "Get",
      "List",
    ]

    storage_permissions = [
    ]
  }

  purge_protection_enabled      = false
  public_network_access_enabled = false
  soft_delete_retention_days    = 7
  contact {
    email = "yogesh.girikumar@hotosm.org"
    name  = "Yogesh Girikumar"
    phone = "+1 123 456 789"
  }

  tags = {
  }

}

resource "azurerm_network_interface" "raw-data-backend" {
  name                = join("-", [var.project_name, var.deployment_environment])
  location            = azurerm_resource_group.raw-data.location
  resource_group_name = azurerm_resource_group.raw-data.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.raw-data.id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_linux_virtual_machine" "raw-data-backend" {
  admin_username        = lookup(var.admin_usernames, "backend")
  location              = var.arm_location
  name                  = join("-", [var.project_name, "backend", var.deployment_environment])
  network_interface_ids = [azurerm_network_interface.raw-data-backend.id]
  resource_group_name   = azurerm_resource_group.raw-data.name
  size                  = lookup(var.server_skus, "backend")

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }

  /* Ref: https://wiki.debian.org/Cloud/MicrosoftAzure
  source_image_reference {
    publisher = "Debian"
    offer     = "debian-11"
    sku       = "11"
    version   = "latest"
  }
  */

  os_disk {
    caching              = "None"
    storage_account_type = "StandardSSD_LRS" // StandardSSD_ZRS
    disk_size_gb         = lookup(var.disk_size, "backend_os")
    name                 = join("-", [var.project_name, var.deployment_environment])

  }

  admin_ssh_key {
    public_key = var.ssh_public_key
    username   = lookup(var.admin_usernames, "backend")
  }
}

resource "azurerm_postgresql_flexible_server" "raw-data" {
  name                = join("-", [var.project_name, var.deployment_environment])
  resource_group_name = azurerm_resource_group.raw-data.name
  location            = azurerm_resource_group.raw-data.location
  sku_name            = lookup(var.server_skus, "database")

  administrator_login    = lookup(var.admin_usernames, "database")
  administrator_password = random_string.raw_data_db_password.result
  authentication {
  }
  backup_retention_days        = 7
  geo_redundant_backup_enabled = false
  storage_mb                   = 2097152
  tags = {
  }

  version = 14
  zone    = "1"
}
