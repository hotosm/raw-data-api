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
    backend_os = 30
  }
}

variable "server_skus" {
  type = map(any)
  default = {
    database = "Standard_D2ds_v4"
    backend  = "Standard_F2"
  }
}
