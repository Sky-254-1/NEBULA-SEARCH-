output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.nebula.id
}

output "alb_dns" {
  description = "Application Load Balancer DNS name"
  value       = aws_lb.nebula.dns_name
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain"
  value       = aws_cloudfront_distribution.nebula.domain_name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.nebula.endpoint
}

output "redis_endpoint" {
  description = "Redis cluster endpoint"
  value       = aws_elasticache_replication_group.nebula.primary_endpoint_address
}

output "ecs_cluster" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.nebula.name
}

output "ecs_service" {
  description = "ECS service name"
  value       = aws_ecs_service.nebula.name
}

output "s3_uploads_bucket" {
  description = "S3 bucket for uploads"
  value       = aws_s3_bucket.uploads.id
}

output "s3_exports_bucket" {
  description = "S3 bucket for exports"
  value       = aws_s3_bucket.exports.id
}

output "waf_acl_id" {
  description = "WAF Web ACL ID"
  value       = aws_wafv2_web_acl.nebula.id
}