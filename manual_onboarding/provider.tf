# Define the version of terraform itself and the aws plugin version.
terraform {
  required_providers {
    aws = {
      source  = "registry.terraform.io/hashicorp/aws"
      version = "~> 5.41.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2.1"
    }
  }
  required_version = ">= 1.2.0"
}

# Define the region in which to create your resources.
provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Project = "AWS Manual Onboarding Production Scale Solution"
      IaC     = "Terraform"
    }
  }
}
