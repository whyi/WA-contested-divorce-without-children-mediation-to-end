output "aws_account_id" {
  description = "AWS account used by this Terraform configuration."
  value       = data.aws_caller_identity.current.account_id
}

output "aws_region" {
  value = var.aws_region
}

output "uat_url" {
  description = "AWS-managed HTTPS URL. The ECS service starts at desired count zero."
  value       = aws_apigatewayv2_api.uat.api_endpoint
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.uat.name
}

output "ecs_service_name" {
  value = aws_ecs_service.app.name
}

output "app_task_definition_arn" {
  value = aws_ecs_task_definition.app.arn
}

output "bootstrap_task_definition_arn" {
  value = aws_ecs_task_definition.bootstrap.arn
}

output "private_subnet_ids" {
  value = join(",", aws_subnet.private[*].id)
}

output "public_subnet_ids" {
  value = join(",", aws_subnet.public[*].id)
}

output "app_security_group_id" {
  value = aws_security_group.app.id
}

output "rds_master_secret_arn" {
  description = "AWS-managed RDS master secret; its value is not stored in Terraform state."
  value       = aws_db_instance.uat.master_user_secret[0].secret_arn
}

output "application_secret_names" {
  description = "Secret Manager names to populate with deploy/aws/owner-beta/bootstrap-secrets.sh."
  value       = local.secret_names
}

output "monthly_budget_alert_usd" {
  value = var.budget_limit_usd
}
