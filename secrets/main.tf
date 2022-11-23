# This file creates secrets in the AWS Secret Manager
# Note that this does not contain any actual secret values
# make sure to not commit any secret values to git!
# you could put them in secrets.tfvars which is in .gitignore


resource "aws_secretsmanager_secret" "application_secrets" {
  count = length(var.application-secrets)
  name  = "${var.name}-application-secrets-${element(keys(var.application-secrets), count.index)}"
}

resource "aws_secretsmanager_secret_version" "application_secrets_values" {
  count         = length(var.application-secrets)
  secret_id     = element(aws_secretsmanager_secret.application_secrets.*.id, count.index)
  secret_string = element(values(var.application-secrets), count.index)
}

locals {
  count   = length(var.application-secrets)
  secrets = var.application-secrets

  secretMap = [for index, item in aws_secretsmanager_secret_version.application_secrets_values : {
    name      = keys(var.application-secrets)[index]
    valueFrom = item.arn
    }
  ]
}

output "secrets_map" {
  description = "Secrets map structure"
  value       = local.secretMap
}
