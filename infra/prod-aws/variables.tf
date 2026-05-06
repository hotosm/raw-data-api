variable "org_meta" {
  description = "Org info for secrets manager prefix"

  default = {
    name       = "hotosm.org"
    short_name = "hot"
    url        = "hotosm.org"
  }
}

variable "project_meta" {
  description = "Metadata relating to the project for which the VPC is being created"
  type        = map(string)

  default = {
    name       = "raw-data-services"
    short_name = "raw-data"
    version    = "1.1.2"
    url        = "https://raw-data.hotosm.org"
  }
}

variable "deployment_environment" {
  description = "Deployment flavour or variant identified by this name"
  type        = string

  default = "dev"
}

variable "default_tags" {
  description = "Default resource tags to apply to AWS resources"
  type        = map(string)

  default = {
    project        = "map-data-access"
    tool           = "raw-data-services"
    maintainer     = "kshitij.sharma@hotosm.org"
    documentation  = "https://docs.hotosm.org"
    cost_center    = "raw-data-services"
    IaC_Management = "Terraform"
  }
}

variable "aws_region" {
  description = "AWS region in which to launch the application"
  type        = string

  default = "us-east-1"
}

variable "container_envvars" {
  description = "Plain-text environment variables to pass to the container"
  default = {
    EXPORT_MAX_AREA_SQKM                = "80000"
    RATE_LIMIT_PER_MIN                  = "50"
    ENABLE_TILES                        = "true"
    ENABLE_POLYGON_STATISTICS_ENDPOINTS = "true"
    POLYGON_STATISTICS_API_URL          = "https://apps.kontur.io/insights-api/graphql"
    ENABLE_HDX_EXPORTS                  = "true"
    FILE_UPLOAD_METHOD                  = "s3"
    USE_DUCK_DB_FOR_CUSTOM_EXPORTS      = "True"
    ENABLE_CUSTOM_EXPORTS               = "True"
    POLYGON_STATISTICS_API_RATE_LIMIT   = "60"
    EXPORT_PATH                         = "/tmp/app-data"
  }
}

variable "task_role_arn" {
  type    = string
  default = "arn:aws:iam::670261699094:role/raw-data-testing"
}

# Null defaults

variable "efs_settings" {
  default = {
    file_system_id     = ""
    access_point_id    = ""
    root_directory     = "/"
    transit_encryption = "ENABLED"
    iam_authz          = "DISABLED"
  }
}

variable "alarm_settings" {
  default = {
    names    = []
    enable   = false
    rollback = false
  }
}

variable "sentry_dsn" {}
variable "remote_db_arn" {}
variable "app_secret_key" {}
variable "dummy_arn" {}
variable "flower_creds" {}
variable "DNS_zone" {}
variable "DNS_domain" {}
variable "SSH_key_name" {}
variable "bucket_name" {}
variable "container_secrets" {}

