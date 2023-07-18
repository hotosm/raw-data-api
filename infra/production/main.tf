data "tfe_ip_ranges" "addresses" {}

data "azurerm_client_config" "current" {}

locals {
  required_tags = {
    deployment_environment    = var.deployment_environment
    infrastructure_management = "terraform"
    project                   = var.project_name
  }

  conditional_tags = {
    _monitor_cloudwatch     = "Yes"
    _monitor_newrelic_infra = "Yes"
    _monitor_apm            = "No"
    _monitor_sentry         = "No"
    _patch_management       = "No"
  }
}

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
  #ts:skip=accurics.azure.NS.272 [TODO] Explore what resource lock is and if it's appropriate here
  name     = join("-", [var.project_name, random_string.raw_data.id])
  location = var.arm_location
}

resource "azurerm_storage_account" "raw-data" {
  name                     = "hotosmrawdata"
  resource_group_name      = azurerm_resource_group.raw-data.name
  location                 = azurerm_resource_group.raw-data.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = local.required_tags
}

resource "azurerm_virtual_network" "raw-data" {
  name                = join("-", [var.project_name, var.deployment_environment])
  resource_group_name = azurerm_resource_group.raw-data.name
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.raw-data.location

  tags = local.required_tags
}

resource "azurerm_subnet" "raw-data" {
  #ts:skip=accurics.azure.NS.161 [TODO] Give the VNet subnet a network security group
  name                 = join("-", [var.project_name, var.deployment_environment])
  resource_group_name  = azurerm_resource_group.raw-data.name
  virtual_network_name = azurerm_virtual_network.raw-data.name
  address_prefixes     = [cidrsubnet(azurerm_virtual_network.raw-data.address_space[0], 8, 0)]

  service_endpoints = ["Microsoft.KeyVault"]
}

resource "azurerm_subnet" "raw-data-containers" {
  #ts:skip=accurics.azure.NS.161 [TODO] Give the VNet subnet a network security group
  name                 = join("-", [var.project_name, "containers", var.deployment_environment])
  resource_group_name  = azurerm_resource_group.raw-data.name
  virtual_network_name = azurerm_virtual_network.raw-data.name
  address_prefixes     = [cidrsubnet(azurerm_virtual_network.raw-data.address_space[0], 5, 1)]

  delegation {
    name = "containers"

    service_delegation {
      name = "Microsoft.ContainerInstance/containerGroups"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action"
      ]
    }
  }

  service_endpoints = [
    "Microsoft.ContainerRegistry",
    "Microsoft.KeyVault"
  ]
}

resource "azurerm_subnet" "raw-data-db" {
  #ts:skip=accurics.azure.NS.161 [TODO] Give the VNet subnet a network security group
  name                 = join("-", [var.project_name, "database", var.deployment_environment])
  resource_group_name  = azurerm_resource_group.raw-data.name
  virtual_network_name = azurerm_virtual_network.raw-data.name
  address_prefixes     = [cidrsubnet(azurerm_virtual_network.raw-data.address_space[0], 8, 1)]

  delegation {
    name = "postgres"

    service_delegation {
      name = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = [
        "Microsoft.Network/virtualNetworks/subnets/join/action"
      ]
    }
  }

  service_endpoints = [
    "Microsoft.KeyVault",
    "Microsoft.Storage"
  ]
}

resource "azurerm_key_vault" "raw-data" {
  #checkov:skip=CKV_AZURE_110:[BACKLOG] Purge protection not enabled while developing
  #checkov:skip=CKV_AZURE_42:[BACKLOG] Key Vault is not set to be recoverable while developing
  #ts:skip=accurics.azure.EKM.20 [TODO] How much does enabling logging cost?

  // [WARNING] Name has a length constraint: 8-24 characters
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
    bypass         = "AzureServices"
    default_action = "Allow" // "Deny" will cut-off Terraform workers IP
    ip_rules       = data.tfe_ip_ranges.addresses.api
    virtual_network_subnet_ids = [
      azurerm_subnet.raw-data.id,
      azurerm_subnet.raw-data-db.id
    ]
  }

  // [WARNING] Setting this to false will make Terraform unable to access Key Vault
  //       ... because it would cut off **ALL** public access
  public_network_access_enabled = true

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Set",
      "Get",
      "List",
      "Delete",
      "Purge"
    ]

  }

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = var.azuread_admin_group_object_id

    key_permissions = [
      "List",
      "Get",
      "Delete",
      "Purge",
      "Rotate"
    ]

    secret_permissions = [
      "Set",
      "Get",
      "List",
      "Delete",
      "Purge"
    ]

    storage_permissions = [
      "Get",
      "Set",
      "List",
      "Purge",
      "Update"
    ]
  }

  // [ACHTUNG | DANGER] DO NOT ENABLE PURGE PROTECTION!!
  purge_protection_enabled   = false
  soft_delete_retention_days = 7

  tags = local.required_tags
}

resource "azurerm_key_vault_secret" "raw-data-db" {
  #checkov:skip=CKV_AZURE_41:[BACKLOG] Expiration date for secrets can't be set until there's a policy for rotation
  name = join("-", [
    var.project_name,
    "database",
    var.deployment_environment
  ])
  value        = random_string.raw_data_db_password.result
  content_type = "text/plain"

  key_vault_id = azurerm_key_vault.raw-data.id

  tags = local.required_tags
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

  tags = local.required_tags
}

resource "azurerm_network_interface" "raw-data-backend" {
  name                          = join("-", [var.project_name, var.deployment_environment])
  location                      = azurerm_resource_group.raw-data.location
  resource_group_name           = azurerm_resource_group.raw-data.name
  enable_accelerated_networking = true

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.raw-data.id
    private_ip_address_allocation = "Dynamic"
    primary                       = true
    public_ip_address_id          = azurerm_public_ip.raw-data-backend.id
  }
}

resource "azurerm_managed_disk" "backend-data-volume" {
  #checkov:skip=CKV_AZURE_93:[WONT DO] Disk encryption unnecessary and benefits negligible
  name = join("-", [
    var.project_name,
    var.deployment_environment,
    "data-volume"
    ]
  )
  location             = azurerm_resource_group.raw-data.location
  resource_group_name  = azurerm_resource_group.raw-data.name
  storage_account_type = "StandardSSD_LRS"
  create_option        = "Empty"
  disk_size_gb         = "1000"

  tags = merge(local.required_tags, local.conditional_tags)
}

resource "azurerm_linux_virtual_machine" "raw-data-backend" {
  #checkov:skip=CKV_AZURE_179:[TODO] VM Agent installed by default.
  admin_username        = lookup(var.admin_usernames, "backend")
  location              = var.arm_location
  name                  = join("-", [var.project_name, "backend", var.deployment_environment])
  network_interface_ids = [azurerm_network_interface.raw-data-backend.id]
  resource_group_name   = azurerm_resource_group.raw-data.name
  size                  = lookup(var.server_skus, "backend")

  allow_extension_operations = false

  custom_data = base64encode(
    templatefile(
      "${path.module}/bootstrap_backend.sh.tftpl",
      {
        APP_ADMIN_USER = lookup(var.admin_usernames, "backend")
      }
    )
  )

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
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

  tags = merge(local.required_tags, local.conditional_tags)
}

resource "azurerm_virtual_machine_data_disk_attachment" "backend-volume" {
  virtual_machine_id = azurerm_linux_virtual_machine.raw-data-backend.id
  managed_disk_id    = azurerm_managed_disk.backend-data-volume.id
  lun                = "10"
  caching            = "None"
}

resource "azurerm_private_dns_zone" "raw-data-db" {
  name = join("", [
    var.project_name,
    random_string.raw_data.id,
    ".postgres.database.azure.com"
    ]
  )
  resource_group_name = azurerm_resource_group.raw-data.name

  tags = local.required_tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "dns-link" {
  name                = "priv-dns-vnet-link"
  resource_group_name = azurerm_resource_group.raw-data.name

  private_dns_zone_name = azurerm_private_dns_zone.raw-data-db.name
  virtual_network_id    = azurerm_virtual_network.raw-data.id

  tags = local.required_tags
}

resource "azurerm_postgresql_flexible_server" "raw-data" {
  #checkov:skip=CKV_AZURE_136:[WONT DO] Geo-redundant backups are expensive
  depends_on = [
    azurerm_private_dns_zone_virtual_network_link.dns-link
  ]

  name = join("-", [
    var.project_name,
    var.deployment_environment,
    random_string.raw_data.id
    ]
  )
  resource_group_name = azurerm_resource_group.raw-data.name
  location            = azurerm_resource_group.raw-data.location
  sku_name            = lookup(var.server_skus, "database")
  delegated_subnet_id = azurerm_subnet.raw-data-db.id
  private_dns_zone_id = azurerm_private_dns_zone.raw-data-db.id

  administrator_login    = lookup(var.admin_usernames, "database")
  administrator_password = azurerm_key_vault_secret.raw-data-db.value

  backup_retention_days        = 7
  geo_redundant_backup_enabled = false
  storage_mb                   = 2097152

  tags = merge(local.required_tags, local.conditional_tags)

  version = 14
  zone    = "1"

  lifecycle {
    ignore_changes = [
      storage_mb,
    ]
  }
}

resource "azurerm_postgresql_flexible_server_configuration" "raw-data-postgis" {
  name      = "azure.extensions"
  server_id = azurerm_postgresql_flexible_server.raw-data.id
  value     = "BTREE_GIST,INTARRAY,POSTGIS"
}

// Improve password hashing security for PostgreSQL users
resource "azurerm_postgresql_flexible_server_configuration" "raw-data-password-encryption" {
  server_id = azurerm_postgresql_flexible_server.raw-data.id
  name      = "password_encryption"
  value     = "scram-sha-256"
}

resource "azurerm_postgresql_flexible_server_configuration" "raw-data-azure-password-encryption" {
  server_id = azurerm_postgresql_flexible_server.raw-data.id
  name      = "azure.accepted_password_auth_method"
  value     = "md5,scram-sha-256"
}

resource "azurerm_postgresql_flexible_server_database" "default-db" {
  name      = "osm_raw_data"
  server_id = azurerm_postgresql_flexible_server.raw-data.id
}

resource "azurerm_redis_cache" "raw-data-queue" {
  #checkov:skip=CKV_AZURE_89:[TODO] Disable public network access for Redis Cache
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

  // public_network_access_enabled = false

  tags = local.required_tags
}
