variable "aws_region" {
  description = "AWS region for the isolated owner-beta environment."
  type        = string
  default     = "us-west-2"
}

variable "google_client_id" {
  description = "Optional Google OAuth client ID; configure together with google_client_secret_arn."
  type        = string
  default     = ""
}

variable "google_client_secret_arn" {
  description = "Existing Google OAuth plaintext secret ARN, not its value. Use the default Secrets Manager KMS key."
  type        = string
  default     = ""

  validation {
    condition     = var.google_client_secret_arn == "" || can(regex("^arn:aws:secretsmanager:us-west-2:[0-9]{12}:secret:", var.google_client_secret_arn))
    error_message = "Use an existing Secrets Manager secret ARN in us-west-2."
  }
}

variable "project_name" {
  description = "Short, globally unique prefix for owner-beta resources."
  type        = string
  default     = "casework-owner-beta-uat"
}

variable "vpc_cidr" {
  description = "Dedicated UAT VPC CIDR."
  type        = string
  default     = "10.74.0.0/16"
}

variable "budget_limit_usd" {
  description = "Account-wide monthly AWS cost alert threshold. Alerts do not cap usage."
  type        = number
  default     = 100

  validation {
    condition     = var.budget_limit_usd > 0
    error_message = "The monthly budget alert must be greater than zero."
  }
}

variable "budget_notification_email" {
  description = "Verified operator address that receives account-wide budget alerts."
  type        = string

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.budget_notification_email))
    error_message = "Provide a valid budget notification email address."
  }
}

variable "db_instance_class" {
  description = "Single-AZ PostgreSQL class for low-volume synthetic UAT."
  type        = string
  default     = "db.t4g.micro"
}

variable "fargate_cpu" {
  description = "CPU units for the combined API and worker task."
  type        = number
  default     = 1024
}

variable "fargate_memory" {
  description = "MiB for the combined API and worker task."
  type        = number
  default     = 3072
}
