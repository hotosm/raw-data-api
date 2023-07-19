variable "project_name" {
  type    = string
  default = "raw-data"
}

variable "azure_subscription_id" {
  type    = string
  default = ""
}

variable "azure_client_id" {
  type    = string
  default = ""
}

variable "azure_client_secret" {
  type    = string
  default = ""
}

variable "azure_tenant_id" {
  type    = string
  default = ""
}

variable "arm_location" {
  type    = string
  default = "West Europe"

}

variable "deployment_environment" {
  type    = string
  default = "production"
}

variable "admin_usernames" {
  type = map(any)
  default = {
    backend  = "hotsysadmin"
    database = "hotdba"
  }
}
variable "disk_size" {
  type = map(number)
  default = {
    backend_os = 32
  }
}

variable "server_skus" {
  type = map(any)
  default = {
    database    = "GP_Standard_D2ds_v4"
    backend_old = "Standard_D2ls_v5"
    backend     = "Standard_E4as_v5"
  }
}

variable "ssh_public_key" {
  type        = string
  default     = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDDqvEc1ESPkG7z2lBX2xYg1fsjXq+JNlcFJdEYtP2SKaVg8Vt0q4/oPBZSHN4p74oHZLEAF//2uFFbqADSvZYRtXIAdp78KvKGXo0Gkqd1pyf0ZPk4kEsfQfxcGeNYmT2T5I1ciYEdpbNgMv9C+WMdXZg0qZhOrgoAeJ6cudsBMtrJu3TTf6At3VELWqB0wL8fMHAfhDxy2+nojitp2OC20y9vAzwg8Uwpv+hVtjf19pijWT5i3gZspNYh+QxsZm+iPzhsD0E40Yi5UH/sqHmulbRYdlbemybeV4XoPEzcZ9UZHTQNXE3yvM592k7AxKHKdhr0y8qL+YzuO3Q0OCmxLtK9iQSchtBvnjhWqQQFfQoVxe+W/Yz0woKzy6+tixZOaTuTio2c23SQrAozTCIEpUkmDpv38FJXDAPl0Emsd5cUWyI2kcyq642B2jKZaKIZgJ0DBlbo7n1TIFYoBRYSa+wDQJ6VkMhNWVOhOBZ6ugu2wOFUe9BU2Q8Fd68hCSc="
  description = "Content of SSH Key public component"
}

variable "azuread_admin_group_object_id" {
  type    = string
  default = ""
}

variable "newrelic_license_key" {
  type    = string
  default = ""
}

variable "container_images" {
  description = "Remote container image URI to pull from"
  type        = map(string)

  default = {
    api    = "quay.io/hotosm/raw-data-api:latest"
    worker = "quay.io/hotosm/raw-data-api:latest"
  }
}

variable "container_envvar" {
  description = "Environment Variables to pass to the container"
  type        = map(string)

  default = {}
}

variable "container_sensitive_envvar" {
  description = "Environment Variables to pass to the container"
  type        = map(string)

  default = {}
}

