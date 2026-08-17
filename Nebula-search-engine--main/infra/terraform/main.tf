terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC
resource "aws_vpc" "nebula" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "nebula-vpc"
    Environment = var.environment
  }
}

# Internet Gateway
resource "aws_internet_gateway" "nebula" {
  vpc_id = aws_vpc.nebula.id

  tags = {
    Name = "nebula-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = 2

  vpc_id                  = aws_vpc.nebula.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "nebula-public-subnet-${count.index + 1}"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count = 2

  vpc_id            = aws_vpc.nebula.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "nebula-private-subnet-${count.index + 1}"
  }
}

# NAT Gateway
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "nebula-nat-eip"
  }
}

resource "aws_nat_gateway" "nebula" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "nebula-nat-gw"
  }

  depends_on = [aws_internet_gateway.nebula]
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.nebula.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.nebula.id
  }

  tags = {
    Name = "nebula-public-rt"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.nebula.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nebula.id
  }

  tags = {
    Name = "nebula-private-rt"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public" {
  count = 2

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = 2

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# Security Groups
resource "aws_security_group" "alb" {
  name        = "nebula-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.nebula.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "nebula-alb-sg"
  }
}

resource "aws_security_group" "backend" {
  name        = "nebula-backend-sg"
  description = "Security group for backend services"
  vpc_id      = aws_vpc.nebula.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.rds.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "nebula-backend-sg"
  }
}

resource "aws_security_group" "rds" {
  name        = "nebula-rds-sg"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.nebula.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.backend.id]
  }

  tags = {
    Name = "nebula-rds-sg"
  }
}

# RDS PostgreSQL
resource "aws_db_subnet_group" "nebula" {
  name       = "nebula-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "nebula-db-subnet-group"
  }
}

resource "aws_db_instance" "nebula" {
  identifier             = "nebula-postgres"
  engine                 = "postgres"
  engine_version         = "16.1"
  instance_class         = "db.t3.micro"
  allocated_storage      = 20
  storage_type           = "gp3"
  db_subnet_group_name   = aws_db_subnet_group.nebula.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  db_name  = "nebula"
  username = var.db_username
  password = var.db_password

  backup_retention_period = 7
  skip_final_snapshot     = false
  final_snapshot_identifier = "nebula-final-snapshot"

  tags = {
    Name = "nebula-postgres"
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "nebula" {
  name       = "nebula-cache-subnet"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_elasticache_replication_group" "nebula" {
  replication_group_id         = "nebula-redis"
  description                  = "Redis cluster for Nebula"
  engine                       = "redis"
  engine_version               = "7.1"
  node_type                    = "cache.t3.micro"
  number_cache_clusters        = 2
  subnet_group_name            = aws_elasticache_subnet_group.nebula.name
  security_group_ids           = [aws_security_group.backend.id]
  automatic_failover_enabled   = true
  multi_az_enabled             = true

  tags = {
    Name = "nebula-redis"
  }
}

# S3 Buckets
resource "aws_s3_bucket" "uploads" {
  bucket = "nebula-uploads-${var.environment}"

  tags = {
    Name        = "nebula-uploads"
    Environment = var.environment
  }
}

resource "aws_s3_bucket" "exports" {
  bucket = "nebula-exports-${var.environment}"

  tags = {
    Name        = "nebula-exports"
    Environment = var.environment
  }
}

# CloudFront CDN
resource "aws_cloudfront_distribution" "nebula" {
  origin {
    domain_name = aws_lb.nebula.dns_name
    origin_id   = "nebula-backend"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2", "TLSv1.3"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "POST", "PUT", "DELETE", "PATCH"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "nebula-backend"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      headers      = ["*"]

      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "nebula-cdn"
  }
}

# WAF Web ACL
resource "aws_wafv2_web_acl" "nebula" {
  name  = "nebula-waf"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  rule {
    name     = "RateLimitRule"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimitRule"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 2

    action {
      block {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "AWSManagedRulesCommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "nebula-waf"
    sampled_requests_enabled   = true
  }
}

# Application Load Balancer
resource "aws_lb" "nebula" {
  name               = "nebula-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = true

  tags = {
    Name = "nebula-alb"
  }
}

resource "aws_lb_target_group" "nebula" {
  name     = "nebula-backend-tg"
  port     = 8000
  protocol = "HTTP"
  vpc_id   = aws_vpc.nebula.id

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 30
    interval            = 60
    path                = "/health/ready"
    matcher             = "200"
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.nebula.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.ssl_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.nebula.arn
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "nebula" {
  name = "nebula-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "nebula" {
  family                   = "nebula-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/nebula-backend:latest"
      essential = true

      portMappings = [
        {
          containerPort = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "DATABASE_URL"
          value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.nebula.endpoint}/nebula"
        },
        {
          name  = "REDIS_URL"
          value = "redis://${aws_elasticache_replication_group.nebula.primary_endpoint_address}:6379/0"
        },
        {
          name  = "APP_ENV"
          value = "production"
        }
      ]

      secrets = [
        {
          name      = "JWT_SECRET"
          valueFrom = aws_ssm_parameter.jwt_secret.arn
        },
        {
          name      = "ENCRYPTION_KEY"
          valueFrom = aws_ssm_parameter.encryption_key.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/nebula"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "backend"
        }
      }
    }
  ])
}

# ECS Service
resource "aws_ecs_service" "nebula" {
  name            = "nebula-backend"
  cluster         = aws_ecs_cluster.nebula.id
  task_definition = aws_ecs_task_definition.nebula.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.backend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.nebula.arn
    container_name   = "backend"
    container_port   = 8000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }
}

# IAM Roles
resource "aws_iam_role" "ecs_execution" {
  name = "nebula-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role" "ecs_task" {
  name = "nebula-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# SSM Parameters for secrets
resource "aws_ssm_parameter" "jwt_secret" {
  name  = "/nebula/jwt_secret"
  type  = "SecureString"
  value = var.jwt_secret
}

resource "aws_ssm_parameter" "encryption_key" {
  name  = "/nebula/encryption_key"
  type  = "SecureString"
  value = var.encryption_key
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}