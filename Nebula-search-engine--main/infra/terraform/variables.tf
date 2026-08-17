variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev/staging/prod)"
  type        = string
  default     = "prod"
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "nebula_admin"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT signing secret"
  type        = string
  sensitive   = true
}

variable "encryption_key" {
  description = "Data encryption key"
  type        = string
  sensitive   = true
}

variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate for CloudFront/ALB"
  type        = string
}

variable "domain_name" {
  description = "Primary domain name"
  type        = string
  default     = "nebula-search.example.com"
}