data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name = lower(var.project_name)
  azs  = slice(data.aws_availability_zones.available.names, 0, 2)

  tags = {
    Application = "Casework"
    Environment = "owner-beta-uat"
    ManagedBy   = "Terraform"
    Project     = local.name
  }

  secret_names = {
    database_url    = "/${local.name}/database-url"
    auth_jwt        = "/${local.name}/auth-jwt-secret"
    auth_encryption = "/${local.name}/auth-encryption-key"
    owner_email     = "/${local.name}/owner-email"
    smtp_username   = "/${local.name}/smtp-username"
    smtp_password   = "/${local.name}/smtp-password"
  }

  task_environment = [
    { name = "AUTH_ENABLED", value = "true" },
    { name = "AUTH_ISSUER", value = aws_apigatewayv2_api.uat.api_endpoint },
    { name = "AUTH_PUBLIC_BASE_URL", value = aws_apigatewayv2_api.uat.api_endpoint },
    { name = "AUTH_COOKIE_SECURE", value = "true" },
    { name = "AUTH_COOKIE_SAMESITE", value = "lax" },
    { name = "CASE_DATA_ENABLED", value = "true" },
    { name = "CASE_MATERIALS_ENABLED", value = "true" },
    { name = "DEMO_MODE_ENABLED", value = "false" },
    { name = "MAX_PDF_PAGES", value = "200" },
    { name = "MAX_UPLOAD_BYTES", value = "2097152" },
    { name = "OWNER_BETA_ENABLED", value = "true" },
    { name = "OWNER_BETA_FIXTURE_RESET_ENABLED", value = "true" },
    { name = "OWNER_BETA_FIXTURE_DATABASE_HOST_PREFIX", value = local.name },
    { name = "OWNER_BETA_READINESS_REQUIRED", value = "true" },
    { name = "PRODUCTION_READINESS_REQUIRED", value = "false" },
    { name = "S3_BUCKET", value = aws_s3_bucket.documents.bucket },
    { name = "S3_KMS_KEY_ID", value = aws_kms_key.uat.arn },
    { name = "S3_REGION", value = var.aws_region },
    { name = "DELETION_LEDGER_BUCKET", value = aws_s3_bucket.deletion_ledger.bucket },
    { name = "SMTP_HOST", value = "email-smtp.${var.aws_region}.amazonaws.com" },
    { name = "SMTP_PORT", value = "587" },
    { name = "SMTP_STARTTLS", value = "true" },
    { name = "WEBAUTHN_ORIGIN", value = aws_apigatewayv2_api.uat.api_endpoint },
    { name = "WEBAUTHN_RP_ID", value = trimprefix(aws_apigatewayv2_api.uat.api_endpoint, "https://") },
    { name = "WEBAUTHN_RP_NAME", value = "Casework Owner UAT" },
  ]

  task_secrets = [
    { name = "AUTH_EMAIL_FROM", valueFrom = aws_secretsmanager_secret.owner_email.arn },
    { name = "AUTH_ENCRYPTION_KEY", valueFrom = aws_secretsmanager_secret.auth_encryption.arn },
    { name = "AUTH_JWT_SECRET", valueFrom = aws_secretsmanager_secret.auth_jwt.arn },
    { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn },
    { name = "OWNER_BETA_EMAIL", valueFrom = aws_secretsmanager_secret.owner_email.arn },
    { name = "SMTP_PASSWORD", valueFrom = aws_secretsmanager_secret.smtp_password.arn },
    { name = "SMTP_USERNAME", valueFrom = aws_secretsmanager_secret.smtp_username.arn },
  ]

  api_container = {
    name      = "api"
    image     = "${aws_ecr_repository.app.repository_url}:bootstrap"
    essential = true
    cpu       = 512
    memory    = 2048
    portMappings = [{
      containerPort = 8000
      hostPort      = 8000
      protocol      = "tcp"
    }]
    environment = local.task_environment
    secrets     = local.task_secrets
    healthCheck = {
      command     = ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).read()"]
      interval    = 15
      timeout     = 5
      retries     = 3
      startPeriod = 120
    }
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.app.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "api"
      }
    }
  }

  worker_containers = [
    {
      name        = "extraction-worker"
      image       = "${aws_ecr_repository.app.repository_url}:bootstrap"
      essential   = true
      cpu         = 256
      memory      = 512
      command     = ["python", "-m", "app.extraction_worker"]
      environment = local.task_environment
      secrets     = local.task_secrets
      dependsOn   = [{ containerName = "api", condition = "HEALTHY" }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "extraction"
        }
      }
    },
    {
      name        = "analysis-worker"
      image       = "${aws_ecr_repository.app.repository_url}:bootstrap"
      essential   = true
      cpu         = 256
      memory      = 512
      command     = ["python", "-m", "app.analysis_worker"]
      environment = local.task_environment
      secrets     = local.task_secrets
      dependsOn   = [{ containerName = "api", condition = "HEALTHY" }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "analysis"
        }
      }
    },
  ]

  task_container_definitions = concat([local.api_container], local.worker_containers)
}

resource "aws_vpc" "uat" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true
}

resource "aws_internet_gateway" "uat" {
  vpc_id = aws_vpc.uat.id
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.uat.id
  availability_zone       = local.azs[count.index]
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  map_public_ip_on_launch = true
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.uat.id
  availability_zone = local.azs[count.index]
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 16)
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.uat.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.uat.id
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  count  = 2
  vpc_id = aws_vpc.uat.id
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_security_group" "vpc_link" {
  name_prefix = "${local.name}-vpc-link-"
  description = "API Gateway VPC Link for the owner-beta UAT API."
  vpc_id      = aws_vpc.uat.id
  egress      = []
}

resource "aws_security_group" "app" {
  name_prefix = "${local.name}-app-"
  description = "UAT tasks accept traffic only from the API Gateway VPC Link."
  vpc_id      = aws_vpc.uat.id
  egress      = []
}

resource "aws_security_group" "database" {
  name_prefix = "${local.name}-database-"
  description = "Private UAT PostgreSQL; only the application task can connect."
  vpc_id      = aws_vpc.uat.id
  egress      = []
}

resource "aws_vpc_security_group_egress_rule" "vpc_link_to_app" {
  security_group_id            = aws_security_group.vpc_link.id
  referenced_security_group_id = aws_security_group.app.id
  ip_protocol                  = "tcp"
  from_port                    = 8000
  to_port                      = 8000
}

resource "aws_vpc_security_group_ingress_rule" "app_from_vpc_link" {
  security_group_id            = aws_security_group.app.id
  referenced_security_group_id = aws_security_group.vpc_link.id
  ip_protocol                  = "tcp"
  from_port                    = 8000
  to_port                      = 8000
}

resource "aws_vpc_security_group_egress_rule" "app_https" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  description       = "HTTPS to AWS APIs and the SES SMTP TLS submission endpoint."
}

resource "aws_vpc_security_group_egress_rule" "app_smtp_submission" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 587
  to_port           = 587
  description       = "STARTTLS submission to the configured SES endpoint."
}

resource "aws_vpc_security_group_egress_rule" "app_to_database" {
  security_group_id            = aws_security_group.app.id
  referenced_security_group_id = aws_security_group.database.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_vpc_security_group_ingress_rule" "database_from_app" {
  security_group_id            = aws_security_group.database.id
  referenced_security_group_id = aws_security_group.app.id
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
}

resource "aws_kms_key" "uat" {
  description             = "Dedicated encryption key for ${local.name}."
  deletion_window_in_days = 7
  enable_key_rotation     = true
}

resource "aws_kms_alias" "uat" {
  name          = "alias/${local.name}"
  target_key_id = aws_kms_key.uat.key_id
}

resource "aws_s3_bucket" "documents" {
  bucket_prefix = "${local.name}-documents-"
  force_destroy = false
}

resource "aws_s3_bucket" "deletion_ledger" {
  bucket_prefix = "${local.name}-deletion-ledger-"
  force_destroy = false
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket                  = aws_s3_bucket.documents.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "deletion_ledger" {
  bucket                  = aws_s3_bucket.deletion_ledger.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "deletion_ledger" {
  bucket = aws_s3_bucket.deletion_ledger.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.uat.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "deletion_ledger" {
  bucket = aws_s3_bucket.deletion_ledger.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.uat.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_policy" "documents" {
  bucket = aws_s3_bucket.documents.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource = [
        aws_s3_bucket.documents.arn,
        "${aws_s3_bucket.documents.arn}/*",
      ]
      Condition = {
        Bool = { "aws:SecureTransport" = "false" }
      }
    }]
  })
}

resource "aws_s3_bucket_policy" "deletion_ledger" {
  bucket = aws_s3_bucket.deletion_ledger.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource = [
        aws_s3_bucket.deletion_ledger.arn,
        "${aws_s3_bucket.deletion_ledger.arn}/*",
      ]
      Condition = {
        Bool = { "aws:SecureTransport" = "false" }
      }
    }]
  })
}

resource "aws_db_subnet_group" "uat" {
  name       = "${local.name}-db"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_db_parameter_group" "uat" {
  name   = "${local.name}-postgres16"
  family = "postgres16"

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }
}

resource "aws_db_instance" "uat" {
  identifier                    = local.name
  engine                        = "postgres"
  engine_version                = "16"
  instance_class                = var.db_instance_class
  allocated_storage             = 20
  max_allocated_storage         = 50
  storage_type                  = "gp3"
  storage_encrypted             = true
  kms_key_id                    = aws_kms_key.uat.arn
  db_name                       = "owner_beta_uat"
  username                      = "casework"
  manage_master_user_password   = true
  master_user_secret_kms_key_id = aws_kms_key.uat.arn
  port                          = 5432
  db_subnet_group_name          = aws_db_subnet_group.uat.name
  vpc_security_group_ids        = [aws_security_group.database.id]
  parameter_group_name          = aws_db_parameter_group.uat.name
  publicly_accessible           = false
  multi_az                      = false
  backup_retention_period       = 7
  auto_minor_version_upgrade    = true
  apply_immediately             = true
  deletion_protection           = false
  skip_final_snapshot           = true
  copy_tags_to_snapshot         = true
}

resource "aws_ecr_repository" "app" {
  name                 = local.name
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the most recent ten UAT images."
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

resource "aws_secretsmanager_secret" "database_url" {
  name       = local.secret_names.database_url
  kms_key_id = aws_kms_key.uat.arn
}

resource "aws_secretsmanager_secret" "auth_jwt" {
  name       = local.secret_names.auth_jwt
  kms_key_id = aws_kms_key.uat.arn
}

resource "aws_secretsmanager_secret" "auth_encryption" {
  name       = local.secret_names.auth_encryption
  kms_key_id = aws_kms_key.uat.arn
}

resource "aws_secretsmanager_secret" "owner_email" {
  name       = local.secret_names.owner_email
  kms_key_id = aws_kms_key.uat.arn
}

resource "aws_secretsmanager_secret" "smtp_username" {
  name       = local.secret_names.smtp_username
  kms_key_id = aws_kms_key.uat.arn
}

resource "aws_secretsmanager_secret" "smtp_password" {
  name       = local.secret_names.smtp_password
  kms_key_id = aws_kms_key.uat.arn
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${local.name}"
  retention_in_days = 14
}

resource "aws_iam_role" "execution" {
  name = "${local.name}-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "execution_base" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execution_secrets" {
  name = "${local.name}-read-task-secrets"
  role = aws_iam_role.execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = [
          aws_secretsmanager_secret.database_url.arn,
          aws_secretsmanager_secret.auth_jwt.arn,
          aws_secretsmanager_secret.auth_encryption.arn,
          aws_secretsmanager_secret.owner_email.arn,
          aws_secretsmanager_secret.smtp_username.arn,
          aws_secretsmanager_secret.smtp_password.arn,
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt"]
        Resource = [aws_kms_key.uat.arn]
      },
    ]
  })
}

resource "aws_iam_role" "task" {
  name = "${local.name}-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "task_storage" {
  name = "${local.name}-case-storage"
  role = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "DocumentBucket"
        Effect   = "Allow"
        Action   = ["s3:ListBucket", "s3:ListBucketVersions"]
        Resource = [aws_s3_bucket.documents.arn]
      },
      {
        Sid    = "DocumentObjects"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:DeleteObjectVersion",
        ]
        Resource = ["${aws_s3_bucket.documents.arn}/*"]
      },
      {
        Sid      = "DeletionLedgerBucket"
        Effect   = "Allow"
        Action   = ["s3:ListBucket", "s3:ListBucketVersions"]
        Resource = [aws_s3_bucket.deletion_ledger.arn]
      },
      {
        Sid      = "DeletionLedgerObjects"
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = ["${aws_s3_bucket.deletion_ledger.arn}/*"]
      },
      {
        Sid    = "BucketEncryption"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey",
          "kms:DescribeKey",
        ]
        Resource = [aws_kms_key.uat.arn]
      },
    ]
  })
}

resource "aws_ecs_cluster" "uat" {
  name = local.name
}

resource "aws_ecs_task_definition" "app" {
  family                   = local.name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.fargate_cpu
  memory                   = var.fargate_memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn
  container_definitions    = jsonencode(local.task_container_definitions)
}

resource "aws_ecs_task_definition" "bootstrap" {
  family                   = "${local.name}-bootstrap"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn
  container_definitions = jsonencode([{
    name        = "bootstrap"
    image       = "${aws_ecr_repository.app.repository_url}:bootstrap"
    essential   = true
    command     = ["true"]
    environment = local.task_environment
    secrets     = local.task_secrets
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.app.name
        awslogs-region        = var.aws_region
        awslogs-stream-prefix = "bootstrap"
      }
    }
  }])
}

resource "aws_service_discovery_private_dns_namespace" "uat" {
  name = "${local.name}.internal"
  vpc  = aws_vpc.uat.id
}

resource "aws_service_discovery_service" "api" {
  name = "api"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.uat.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

resource "aws_ecs_service" "app" {
  name                   = local.name
  cluster                = aws_ecs_cluster.uat.id
  task_definition        = aws_ecs_task_definition.app.arn
  desired_count          = 0
  launch_type            = "FARGATE"
  enable_execute_command = false

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.app.id]
    assign_public_ip = true
  }

  service_registries {
    registry_arn   = aws_service_discovery_service.api.arn
    container_name = "api"
    container_port = 8000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  lifecycle {
    ignore_changes = [desired_count, task_definition]
  }
}

resource "aws_apigatewayv2_vpc_link" "uat" {
  name               = "${local.name}-link"
  security_group_ids = [aws_security_group.vpc_link.id]
  subnet_ids         = aws_subnet.private[*].id
}

resource "aws_apigatewayv2_api" "uat" {
  name          = local.name
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "api" {
  api_id                 = aws_apigatewayv2_api.uat.id
  integration_type       = "HTTP_PROXY"
  integration_method     = "ANY"
  integration_uri        = aws_service_discovery_service.api.arn
  connection_type        = "VPC_LINK"
  connection_id          = aws_apigatewayv2_vpc_link.uat.id
  payload_format_version = "1.0"
  timeout_milliseconds   = 30000
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.uat.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.api.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.uat.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 20
    throttling_rate_limit  = 10
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId = "$context.requestId"
      routeKey  = "$context.routeKey"
      status    = "$context.status"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${local.name}"
  retention_in_days = 14
}

resource "aws_sns_topic" "operations" {
  name = "${local.name}-operations-alerts"
}

resource "aws_sns_topic_subscription" "operations_email" {
  topic_arn = aws_sns_topic.operations.arn
  protocol  = "email"
  endpoint  = var.budget_notification_email
}

resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  alarm_name          = "${local.name}-api-5xx"
  alarm_description   = "At least five API Gateway HTTP API 5xx responses in five minutes."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "5xx"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.operations.arn]

  dimensions = {
    ApiId = aws_apigatewayv2_api.uat.id
    Stage = aws_apigatewayv2_stage.default.name
  }
}

resource "aws_cloudwatch_metric_alarm" "ecs_task_shortfall" {
  alarm_name          = "${local.name}-ecs-task-shortfall"
  alarm_description   = "Desired ECS tasks have not remained healthy for the configured service."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  datapoints_to_alarm = 2
  threshold           = 0
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.operations.arn]

  metric_query {
    id          = "desired"
    return_data = false

    metric {
      metric_name = "DesiredTaskCount"
      namespace   = "AWS/ECS"
      period      = 60
      stat        = "Maximum"

      dimensions = {
        ClusterName = aws_ecs_cluster.uat.name
        ServiceName = aws_ecs_service.app.name
      }
    }
  }

  metric_query {
    id          = "running"
    return_data = false

    metric {
      metric_name = "RunningTaskCount"
      namespace   = "AWS/ECS"
      period      = 60
      stat        = "Minimum"

      dimensions = {
        ClusterName = aws_ecs_cluster.uat.name
        ServiceName = aws_ecs_service.app.name
      }
    }
  }

  metric_query {
    id          = "shortfall"
    expression  = "desired - running"
    label       = "Desired tasks not running"
    return_data = true
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${local.name}-rds-high-cpu"
  alarm_description   = "RDS CPU utilization exceeded 80 percent for at least 15 minutes."
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  datapoints_to_alarm = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.operations.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.uat.identifier
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_free_storage" {
  alarm_name          = "${local.name}-rds-low-storage"
  alarm_description   = "RDS free storage fell below 5 GiB."
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Minimum"
  threshold           = 5368709120
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.operations.arn]

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.uat.identifier
  }
}

resource "aws_budgets_budget" "monthly" {
  name         = "${local.name}-monthly-cost-alert"
  budget_type  = "COST"
  limit_amount = tostring(var.budget_limit_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_notification_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_notification_email]
  }
}
