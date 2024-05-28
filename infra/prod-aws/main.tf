resource "aws_cloudwatch_log_group" "main" {
  name              = "raw-data-services"
  retention_in_days = 7
}

module "vpc" {
  source = "git::https://gitlab.com/eternaltyro/terraform-aws-vpc.git"

  project_meta = var.project_meta

  deployment_environment = var.deployment_environment
  default_tags           = var.default_tags
}

module "db" {
  source = "git::https://gitlab.com/eternaltyro/terraform-aws-rds.git"

  project_meta = var.project_meta
  org_meta     = var.org_meta

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  deployment_environment = var.deployment_environment
  deletion_protection    = false
  default_tags           = var.default_tags

  database = {
    name            = "rawdata"
    admin_user      = "datadba"
    password_length = 48
    engine_version  = 15
    port            = 5432
  }

  backup = {
    retention_days            = 7
    skip_final_snapshot       = true
    final_snapshot_identifier = "final"
  }
}

resource "aws_ecs_cluster" "main" {
  name = lookup(var.project_meta, "name")

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = merge(
    {
      Name = lookup(var.project_meta, "name")
    },
    var.default_tags,
    {
      environment = var.deployment_environment
    }
  )
}

locals {
  redis_connection_string = join("", [
    "redis://",
    aws_elasticache_cluster.main.cache_nodes[0].address,
    ":",
    aws_elasticache_cluster.main.cache_nodes[0].port,
    "/0"
  ])

  container_secrets = merge(var.container_secrets, { REMOTE_DB = var.remote_db_arn })

  container_envvars = merge(
    var.container_envvars,
    {
      CELERY_BROKER_URL        = local.redis_connection_string
      CELERY_RESULT_BACKEND    = local.redis_connection_string
      RATE_LIMITER_STORAGE_URI = local.redis_connection_string
      BUCKET_NAME              = var.bucket_name
    }
  )
}

module "alb" {
  source = "git::https://gitlab.com/eternaltyro/terraform-aws-alb.git"

  vpc_id              = module.vpc.vpc_id
  app_port            = 8000
  acm_tls_cert_domain = "*.${var.DNS_domain}"
  health_check_path   = "/docs"
  alb_subnets         = module.vpc.public_subnets
  alb_name            = "raw-data-services-staging"
  target_group_name   = "raw-data-api-staging"
}

module "alb-flower" {
  source = "git::https://gitlab.com/eternaltyro/terraform-aws-alb.git"

  vpc_id              = module.vpc.vpc_id
  app_port            = 5555
  acm_tls_cert_domain = "*.${var.DNS_domain}"
  health_check_path   = "/healthcheck"
  alb_subnets         = module.vpc.public_subnets
  alb_name            = "raw-data-flower-staging"
  target_group_name   = "raw-data-flower-staging"
}

module "ecs-api" {
  source = "git::https://gitlab.com/eternaltyro/terraform-aws-ecs.git"

  service_name = "api"
  aws_vpc_id   = module.vpc.vpc_id

  scaling_target_values = {
    container_min_count = 1
    container_max_count = 1
  }

  ecs_cluster_name = aws_ecs_cluster.main.name
  ecs_cluster_arn  = aws_ecs_cluster.main.arn

  load_balancer_settings = {
    enabled                 = true
    target_group_arn        = module.alb.target_group_arn
    target_group_arn_suffix = module.alb.target_group_arn_suffix
    arn_suffix              = module.alb.load_balancer_arn_suffix
    scaling_request_count   = 1000
  }
  task_role_arn = var.task_role_arn

  service_security_groups = [
    module.alb.load_balancer_app_security_group,
    module.db.database_security_group_id,
    aws_security_group.redis.id
  ]

  container_secrets = merge(local.container_secrets,
    {
      SENTRY_DSN     = var.sentry_dsn
      APP_SECRET_KEY = var.app_secret_key
    }
  )
  container_envvars = merge(local.container_envvars,
    {
      ALLOW_BIND_ZIP_FILTER = "True"
    }
  )

  service_subnets = module.vpc.private_subnets

  container_capacity = {
    cpu       = 1024
    memory_mb = 2048
  }

  container_settings = {
    app_port         = 8000
    cpu_architecture = "X86_64"
    image_url        = "ghcr.io/hotosm/raw-data-api"
    image_tag        = lookup(var.project_meta, "version")
    service_name     = "raw-data-api"
  }

  log_configuration = {
    logdriver = "awslogs"
    options = {
      awslogs-group         = aws_cloudwatch_log_group.main.name
      awslogs-region        = var.aws_region
      awslogs-stream-prefix = "api"
    }
  }

  default_tags = merge(var.default_tags, {environment = var.deployment_environment})
  efs_settings = var.efs_settings
}

module "ecs-worker-daemon" {
  source = "git::https://gitlab.com/eternaltyro/terraform-aws-ecs.git"

  service_name  = "worker-daemon"
  task_role_arn = var.task_role_arn

  aws_vpc_id = module.vpc.vpc_id
  scaling_target_values = {
    container_min_count = 2
    container_max_count = 4
  }
  scale_by_cpu = {
    enabled = true
    cpu_pct = 50
  }
  scale_by_memory = {
    enabled    = true
    memory_pct = 50
  }
  ecs_cluster_name = aws_ecs_cluster.main.name
  ecs_cluster_arn  = aws_ecs_cluster.main.arn

  service_security_groups = [
    module.db.database_security_group_id,
    aws_security_group.redis.id
  ]

  container_commands = [
    "celery",
    "--app", "API.api_worker",
    "worker",
    "--loglevel=DEBUG",
    "--queues=raw_daemon",
    "--concurrency", "1",
    "-n", "ondemand_daemon-%h"
  ]
  container_secrets = local.container_secrets
  container_envvars = merge(local.container_envvars,
    {
      ALLOW_BIND_ZIP_FILTER = "True"
    }
  )

  service_subnets = module.vpc.private_subnets

  container_ephemeral_storage = 100
  container_capacity = {
    cpu       = 2048
    memory_mb = 16384
  }

  container_settings = {
    app_port         = 8000
    cpu_architecture = "X86_64"
    image_url        = "ghcr.io/hotosm/raw-data-api"
    image_tag        = lookup(var.project_meta, "version")
    service_name     = "raw-data-worker-daemon"
  }

  log_configuration = {
    logdriver = "awslogs"
    options = {
      awslogs-group         = aws_cloudwatch_log_group.main.name
      awslogs-region        = var.aws_region
      awslogs-stream-prefix = "worker-daemon"
    }
  }

  default_tags = merge(var.default_tags, {environment = var.deployment_environment})
  efs_settings = var.efs_settings
}

module "ecs-worker-ondemand" {
  source = "git::https://gitlab.com/eternaltyro/terraform-aws-ecs.git"

  service_name  = "worker-ondemand"
  task_role_arn = var.task_role_arn

  aws_vpc_id = module.vpc.vpc_id
  // TBD: SCALE BY QUEUE - EVENT DRIVEN SCALING
  scaling_target_values = {
    container_min_count = 1
    container_max_count = 2
  }

  ecs_cluster_name = aws_ecs_cluster.main.name
  ecs_cluster_arn  = aws_ecs_cluster.main.arn

  service_security_groups = [
    module.db.database_security_group_id,
    aws_security_group.redis.id
  ]

  container_commands = [
    "celery",
    "--app", "API.api_worker",
    "worker",
    "--loglevel=DEBUG",
    "--queues=raw_ondemand",
    "--concurrency", "1",
    "-n", "ondemand_worker-%h"
  ]
  container_secrets = local.container_secrets
  container_envvars = merge(local.container_envvars, { MAX_WORKERS = "2" })

  service_subnets = module.vpc.private_subnets

  container_ephemeral_storage = 150
  container_capacity = {
    cpu       = 4096
    memory_mb = 24576
  }

  container_settings = {
    app_port         = 8000
    cpu_architecture = "X86_64"
    image_url        = "ghcr.io/hotosm/raw-data-api"
    image_tag        = lookup(var.project_meta, "version")
    service_name     = "raw-data-worker-ondemand"
  }

  log_configuration = {
    logdriver = "awslogs"
    options = {
      awslogs-group         = aws_cloudwatch_log_group.main.name
      awslogs-region        = var.aws_region
      awslogs-stream-prefix = "worker-ondemand"
    }
  }

  default_tags = merge(var.default_tags, {environment = var.deployment_environment})
  efs_settings = var.efs_settings
}

module "ecs-flower" {
  source = "git::https://gitlab.com/eternaltyro/terraform-aws-ecs.git"

  service_name = "worker-monitoring"
  load_balancer_settings = {
    enabled                 = true
    target_group_arn        = module.alb-flower.target_group_arn
    target_group_arn_suffix = module.alb-flower.target_group_arn_suffix
    arn_suffix              = module.alb-flower.load_balancer_arn_suffix
    scaling_request_count   = 100
  }

  aws_vpc_id = module.vpc.vpc_id
  scaling_target_values = {
    container_min_count = 1
    container_max_count = 1
  }
  ecs_cluster_name = aws_ecs_cluster.main.name
  ecs_cluster_arn  = aws_ecs_cluster.main.arn

  service_security_groups = [
    module.alb-flower.load_balancer_app_security_group,
    aws_security_group.redis.id
  ]

  container_commands = [
    "celery",
    "flower"
  ]

  container_secrets = {
    DUMMY = var.dummy_arn
  }

  container_envvars = {
    FLOWER_PERSISTENT          = "True"
    FLOWER_STATE_SAVE_INTERVAL = "10000"
    FLOWER_DB                  = "flower_db"
    FLOWER_BASIC_AUTH          = var.flower_creds
    CELERY_BROKER_URL          = local.redis_connection_string
  }

  service_subnets = module.vpc.private_subnets

  container_settings = {
    app_port         = 5555
    cpu_architecture = "X86_64"
    image_url        = "ghcr.io/hotosm/raw-data-api"
    image_tag        = lookup(var.project_meta, "version")
    service_name     = "raw-data-monitoring"
  }

  log_configuration = {
    logdriver = "awslogs"
    options = {
      awslogs-group         = aws_cloudwatch_log_group.main.name
      awslogs-region        = var.aws_region
      awslogs-stream-prefix = "flower"
    }
  }

  default_tags = merge(var.default_tags, {environment = var.deployment_environment})
  efs_settings = var.efs_settings
}

resource "aws_security_group" "redis" {
  name        = "redis_private_access"
  description = "Attach this to give access to Raw Data redis"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "Allow connections from self"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    self        = true
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = merge(
  {
    Name = "Access to elasticache Redis"
  },
  var.default_tags,
  {
    environment = var.deployment_environment
  })
}

resource "aws_elasticache_subnet_group" "private" {
  name       = lookup(var.project_meta, "short_name")
  subnet_ids = module.vpc.private_subnets
}

resource "aws_elasticache_cluster" "main" {
  cluster_id           = lookup(var.project_meta, "short_name")
  engine               = "redis"
  node_type            = "cache.m7g.large" // TODO: PARAMETERIZE
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7" // TODO: PARAMETERIZE
  subnet_group_name    = aws_elasticache_subnet_group.private.name
  security_group_ids   = [aws_security_group.redis.id]
  network_type         = "dual_stack"
}

resource "aws_instance" "jump" {
  # EC2 machine for backend - Storage 100G for stage; 500G for prod
  ami                         = data.aws_ami.debian_bookworm_x86.id
  associate_public_ip_address = true
  instance_type               = "t3.small"
  key_name                    = var.SSH_key_name
  vpc_security_group_ids = [
    module.vpc.default_security_group_id,
    module.db.database_security_group_id,
    aws_security_group.redis.id
  ]
  subnet_id = element(module.vpc.public_subnets, 1)

  root_block_device {
    volume_type = "gp3"
    volume_size = 50
  }

  tags = merge({
    Name = "raw-data-jump"
  },
  var.default_tags,
  {
    environment = var.deployment_environment
  })

  lifecycle {
    ignore_changes = [
      ami,
    ]
  }
}

resource "aws_instance" "backend" {
  # EC2 machine for backend - Storage 100G for stage; 500G for prod
  ami                         = data.aws_ami.debian_bookworm_x86.id
  associate_public_ip_address = false
  instance_type               = "t3.large"
  key_name                    = var.SSH_key_name
  vpc_security_group_ids = [
    module.vpc.default_security_group_id,
    module.db.database_security_group_id,
    aws_security_group.redis.id
  ]
  subnet_id = element(module.vpc.private_subnets, 1)

  root_block_device {
    volume_type = "gp3"
    volume_size = 80
  }

  ebs_block_device {
    device_name = "/dev/sdf"
    volume_type = "gp3"
    volume_size = 500
  }

  metadata_options {
    http_tokens = "required"
  }

  tags = merge({
    Name = "raw-data-backend"
  },
  var.default_tags,
  {
    environment = var.deployment_environment
  })

  lifecycle {
    ignore_changes = [
      ami,
    ]
  }
}

resource "aws_route53_record" "stage-v4" {
  zone_id = var.DNS_zone
  name    = "api-prod.${var.DNS_domain}"
  type    = "A"

  alias {
    name                   = module.alb.load_balancer_dns
    zone_id                = module.alb.load_balancer_dns_zone
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "stage-v6" {
  zone_id = var.DNS_zone
  name    = "api-prod.${var.DNS_domain}"
  type    = "AAAA"

  alias {
    name                   = module.alb.load_balancer_dns
    zone_id                = module.alb.load_balancer_dns_zone
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "stage-flower-v4" {
  zone_id = var.DNS_zone
  name    = "flower-prod.${var.DNS_domain}"
  type    = "A"

  alias {
    name                   = module.alb-flower.load_balancer_dns
    zone_id                = module.alb-flower.load_balancer_dns_zone
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "stage-flower-v6" {
  zone_id = var.DNS_zone
  name    = "flower-prod.${var.DNS_domain}"
  type    = "AAAA"

  alias {
    name                   = module.alb-flower.load_balancer_dns
    zone_id                = module.alb-flower.load_balancer_dns_zone
    evaluate_target_health = true
  }
}
