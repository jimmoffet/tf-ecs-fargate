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
  # backend "s3" {
  #   bucket  = "terraform-backend-store"
  #   encrypt = true
  #   key     = "terraform.tfstate"
  #   region  = "us-west-2"
  #   # dynamodb_table = "terraform-state-lock-dynamo" - uncomment this line once the terraform-state-lock-dynamo has been terraformed
  # }
}

# resource "aws_dynamodb_table" "dynamodb-terraform-state-lock" {
#   name           = "terraform-state-lock-dynamo"
#   hash_key       = "LockID"
#   read_capacity  = 20
#   write_capacity = 20
#   attribute {
#     name = "LockID"
#     type = "S"
#   }
#   tags = {
#     Name = "DynamoDB Terraform State Lock Table"
#   }
# }

data "aws_availability_zones" "available" {
}

module "vpc" {
  source = "./vpc"
  name   = var.name
  cidr   = var.cidr
  # private_subnets = var.private_subnets
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

# module "alb" {
#   source              = "./alb"
#   name                = var.name
#   vpc_id              = module.vpc.id
#   subnets             = module.vpc.public_subnets
#   environment         = var.environment
#   alb_security_groups = [module.security_groups.alb]
#   alb_tls_cert_arn    = var.tsl_certificate_arn
#   health_check_path   = var.health_check_path
# }

module "ecr" {
  source      = "./ecr"
  name        = var.name
  environment = var.environment
}


module "secrets" {
  source              = "./secrets"
  name                = var.name
  environment         = var.environment
  application-secrets = var.application-secrets
}

module "my-container-image" {
  source      = "github.com/mathspace/terraform-aws-ecr-docker-image?ref=v4.0"
  image_name  = "my-container-image"
  source_path = "ecs/src"
}

module "ecs" {
  source      = "./ecs"
  name        = var.name
  environment = var.environment
  region      = var.aws-region
  # subnets     = module.vpc.private_subnets
  subnets = module.vpc.public_subnets
  # aws_alb_target_group_arn      = module.alb.aws_alb_target_group_arn
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
    value = "DEBUG" },
    { name = "PORT",
    value = var.container_port },
    { name = "WHISPER_INCOMING_AUDIO_BUCKET",
    value = var.whisper_incoming_audio_bucket },
    { name = "WHISPER_OUTGOING_TEXT_BUCKET",
    value = var.whisper_outgoing_text_bucket },
    { name = "ENV_NAME",
    value = var.environment },
    { name = "AWS_ACCESS_KEY_ID",
    value = var.s3-only-aws-access-key },
    { name = "AWS_SECRET_ACCESS_KEY",
    value = var.s3-only-aws-secret-key },
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

output "my_container_image" {
  description = "The ID and ARN of the load balancer we created."
  value       = "${module.my-container-image.repository_url}:${module.my-container-image.tag}"
}

