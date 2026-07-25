variable "aws_region" {
  description = "AWS region for AuraCommerce infrastructure"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "development"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
  default     = "postgres"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "ecommerce"
}

variable "eks_cluster_version" {
  description = "EKS Kubernetes version"
  type        = string
  default     = "1.29"
}

variable "lambda_s3_bucket" {
  description = "S3 bucket for Lambda deployment package"
  type        = string
  default     = "aura-commerce-lambda-artifacts"
}
