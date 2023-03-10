data "tfe_ip_ranges" "addresses" {}

data "azurerm_client_config" "current" {}

resource "random_string" "raw_data_db_password" {
  length           = 20
  override_special = "*()-_=+[]{}<>"
}

resource "random_string" "raw_data" {
  length  = 3
  special = false
  upper   = false
}

resource "azurerm_resource_group" "raw-data" {
  name     = join("-", [var.project_name, random_string.raw_data.id])
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

  service_endpoints = ["Microsoft.KeyVault"]
}

/** Key Vault stores database password
 ** Key Vault name has a length constraint 8-24 chars
 **/
resource "azurerm_key_vault" "raw-data" {
  name = join("-", [
    var.project_name,
    var.deployment_environment,
    random_string.raw_data.id
  ])
  location            = azurerm_resource_group.raw-data.location
  resource_group_name = azurerm_resource_group.raw-data.name
  sku_name            = "standard"
  tenant_id           = data.azurerm_client_config.current.tenant_id

  network_acls {
    bypass                     = "AzureServices"
    default_action             = "Allow" // Todo: Deny
    ip_rules                   = data.tfe_ip_ranges.addresses.api
    virtual_network_subnet_ids = [azurerm_subnet.raw-data.id]
  }

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "List",
      "Get",
    ]

    secret_permissions = [
      "Set",
      "Get",
      "List",
    ]

    storage_permissions = [
    ]
  }

  purge_protection_enabled   = false
  soft_delete_retention_days = 7

  tags = {
  }

}

resource "azurerm_key_vault_secret" "raw-data-db" {
  name = join("-", [
    var.project_name,
    "database",
    var.deployment_environment
  ])
  value        = random_string.raw_data_db_password.result
  key_vault_id = azurerm_key_vault.raw-data.id
}

resource "azurerm_public_ip" "raw-data-backend" {
  name = join("-", [
    var.project_name,
    "backend",
    var.deployment_environment
  ])
  resource_group_name = azurerm_resource_group.raw-data.name
  location            = azurerm_resource_group.raw-data.location
  allocation_method   = "Static" // or "Dynamic"
}

resource "azurerm_network_interface" "raw-data-backend" {
  name                = join("-", [var.project_name, var.deployment_environment])
  location            = azurerm_resource_group.raw-data.location
  resource_group_name = azurerm_resource_group.raw-data.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.raw-data.id
    private_ip_address_allocation = "Dynamic"
    primary                       = true
    public_ip_address_id          = azurerm_public_ip.raw-data-backend.id
  }
}

resource "azurerm_linux_virtual_machine" "raw-data-backend" {
  admin_username        = lookup(var.admin_usernames, "backend")
  location              = var.arm_location
  name                  = join("-", [var.project_name, "backend", var.deployment_environment])
  network_interface_ids = [azurerm_network_interface.raw-data-backend.id]
  resource_group_name   = azurerm_resource_group.raw-data.name
  size                  = lookup(var.server_skus, "backend")

  custom_data = base64encode(
    file(
      "bootstrap_backend.sh"
    )
  )

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

  tags = {
    deployment_environment    = var.deployment_environment
    infrastructure_management = "terraform"
    role                      = "backend"
    project                   = var.project_name
    _monitor_cloudwatch       = "Yes"
    _monitor_newrelic_infra   = "Yes"
    _monitor_apm              = "No"
    _monitor_sentry           = "No"
    _patch_management         = "No"
  }
}

resource "azurerm_postgresql_flexible_server" "raw-data" {
  name = join("-", [
    var.project_name,
    var.deployment_environment,
    random_string.raw_data.id
  ])
  resource_group_name = azurerm_resource_group.raw-data.name
  location            = azurerm_resource_group.raw-data.location
  sku_name            = lookup(var.server_skus, "database")

  administrator_login    = lookup(var.admin_usernames, "database")
  administrator_password = azurerm_key_vault_secret.raw-data-db.value

  backup_retention_days        = 7
  geo_redundant_backup_enabled = false
  storage_mb                   = 2097152

  tags = {
    deployment_environment    = var.deployment_environment
    infrastructure_management = "terraform"
    role                      = "database"
    project                   = var.project_name
    _monitor_cloudwatch       = "Yes"
    _monitor_newrelic_infra   = "Yes"
    _monitor_apm              = "No"
    _monitor_sentry           = "No"
    _patch_management         = "No"
  }

  version = 14
  zone    = "1"
}

resource "azurerm_postgresql_flexible_server_configuration" "raw-data-postgis" {
  name      = "azure.extensions"
  server_id = azurerm_postgresql_flexible_server.raw-data.id
  value     = "BTREE_GIST,INTARRAY,POSTGIS"
}

resource "azurerm_redis_cache" "raw-data-queue" {
  name = join("-", [
    var.project_name,
    var.deployment_environment,
    random_string.raw_data.id
  ])
  resource_group_name = azurerm_resource_group.raw-data.name
  location            = azurerm_resource_group.raw-data.location
  capacity            = 0
  family              = "C"
  sku_name            = "Basic"

  minimum_tls_version = "1.2"
  redis_version       = 6
}
