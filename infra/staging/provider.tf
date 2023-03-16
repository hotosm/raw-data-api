terraform {
  required_version = ">= 1.4.0"

  backend "remote" {
    organization = "hotosm"

    workspaces {
      name = "raw-data-staging"
    }
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.46.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "=3.4.3"
    }

    tfe = {
      source  = "hashicorp/tfe"
      version = "~> 0.42.0"
    }

  }
}

provider "azurerm" {
  subscription_id = var.azure_subscription_id
  client_id       = var.azure_client_id
  client_secret   = var.azure_client_secret
  tenant_id       = var.azure_tenant_id

  features {}
}

provider "random" {

}
