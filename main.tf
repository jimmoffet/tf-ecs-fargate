terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  access_key = var.local-tf-deployer-aws-access-key
  secret_key = var.local-tf-deployer-aws-secret-key
  region     = var.aws-region
}

terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}

data "aws_availability_zones" "available" {
}

module "vpc" {
  source             = "./vpc"
  name               = var.name
  cidr               = var.cidr
  public_subnets     = var.public_subnets
  availability_zones = data.aws_availability_zones.available.names[0]
  environment        = var.environment
}

module "security_groups" {
  source         = "./security-groups"
  name           = var.name
  vpc_id         = module.vpc.id
  environment    = var.environment
  container_port = var.container_port
}

module "ecr" {
  source      = "./ecr"
  name        = var.name
  environment = var.environment
}

module "my-container-image" {
  source      = "github.com/mathspace/terraform-aws-ecr-docker-image?ref=v4.0"
  image_name  = "my-container-image"
  source_path = "ecs/src"
}

module "secrets" {
  source              = "./secrets"
  name                = var.name
  environment         = var.environment
  application-secrets = var.application-secrets
}

# module "secrets" {
#   source = "exlabs/ecs-secrets-manager/aws"
#   # We recommend pinning every module to a specific version
#   # version     = "x.x.x"
#   name                    = "${var.name}-pipeline-secrets"
#   ecs_task_execution_role = "${var.name}-ecsTaskExecutionRole"

#   key_names = [
#     "my_secret_key",
#     "my_secret_key_1",
#     "my_secret_key_2"
#   ]
# }

module "ecs" {
  source                        = "./ecs"
  name                          = var.name
  environment                   = var.environment
  region                        = var.aws-region
  subnets                       = module.vpc.public_subnets
  ecs_service_security_groups   = [module.security_groups.ecs_tasks]
  my_container_image            = "${module.my-container-image.repository_url}:${module.my-container-image.tag}"
  container_port                = var.container_port
  container_cpu                 = var.container_cpu
  container_memory              = var.container_memory
  service_desired_count         = var.service_desired_count
  whisper_incoming_audio_bucket = var.whisper_incoming_audio_bucket
  whisper_outgoing_text_bucket  = var.whisper_outgoing_text_bucket
  container_environment = [
    { name = "LOG_LEVEL",
    value = "INFO" },
    { name = "PORT",
    value = var.container_port },
    { name = "WHISPER_INCOMING_AUDIO_BUCKET",
    value = var.whisper_incoming_audio_bucket },
    { name = "WHISPER_OUTGOING_TEXT_BUCKET",
    value = var.whisper_outgoing_text_bucket },
    { name = "ENV_NAME",
    value = var.environment },
    { name = "AWS_DEFAULT_REGION",
    value = var.aws-region }
  ]
  container_secrets = module.secrets.secrets_map
  # container_secrets_arns = module.secrets.application_secrets_arn
}

module "s3" {
  source                        = "./s3"
  whisper_incoming_audio_bucket = var.whisper_incoming_audio_bucket
  whisper_outgoing_text_bucket  = var.whisper_outgoing_text_bucket
  environment                   = var.environment
}

module "lambda" {
  source                        = "./lambda"
  name                          = var.name
  environment                   = var.environment
  region                        = var.aws-region
  whisper_incoming_audio_bucket = var.whisper_incoming_audio_bucket
  whisper_outgoing_text_bucket  = var.whisper_outgoing_text_bucket
  layer_environment = {
    SUBNET_1            = "${lookup(module.vpc.public_subnets[0], "id")}",
    SUBNET_2            = "${lookup(module.vpc.public_subnets[1], "id")}",
    COUNT               = 1,
    NAME                = var.name,
    CLUSTER_ARN         = "${module.ecs.cluster_arn}",
    TASK_DEFINITION_ARN = "${module.ecs.task_definition_arn}",
    S3_INCOMING_BUCKET  = var.whisper_incoming_audio_bucket,
    S3_OUTGOING_BUCKET  = var.whisper_outgoing_text_bucket,
  }
}

output "my_container_image" {
  description = "ECR repo and container image:tag"
  value       = "${module.my-container-image.repository_url}:${module.my-container-image.tag}"
}

output "empty_secrets" {
  description = "Test output empty secrets"
  value       = module.secrets.secrets_map
}

