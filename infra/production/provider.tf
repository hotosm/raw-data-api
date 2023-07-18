terraform {
  required_version = ">= 1.5.0"

  backend "remote" {
    organization = "hotosm"

    workspaces {
      name = "raw-data-production"
    }
  }

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.65.0"
    }

    random = {
      source  = "hashicorp/random"
      version = "=3.5.1"
    }

    tfe = {
      source  = "hashicorp/tfe"
      version = "~> 0.46.0"
    }

  }
}

provider "azurerm" {
  features {}

  subscription_id = var.azure_subscription_id
  client_id       = var.azure_client_id
  client_secret   = var.azure_client_secret
  tenant_id       = var.azure_tenant_id
}

provider "random" {

}
