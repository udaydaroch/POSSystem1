# ── Mini Prism — Dev Environment ──────────────────────────────────────────────
# This is the root module that wires all sub-modules together.
# Run from this directory:
#   terraform init
#   terraform plan
#   terraform apply

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # bucket is passed at init time via -backend-config="bucket=<name>"
    key    = "mini-prism/dev/terraform.tfstate"
    region = "ap-southeast-2"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "mini-prism"
      Environment = "dev"
      ManagedBy   = "terraform"
    }
  }
}

locals {
  name   = "mini-prism-dev"
  region = var.aws_region
  azs    = ["${var.aws_region}a", "${var.aws_region}b"]
}

# ── VPC ───────────────────────────────────────────────────────────────────────

module "vpc" {
  source             = "../../modules/vpc"
  name               = local.name
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = local.azs
}

# ── EKS ───────────────────────────────────────────────────────────────────────

module "eks" {
  source             = "../../modules/eks"
  cluster_name       = local.name
  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids

  # t3.medium = 2 vCPU / 4 GB — good for running 3 Spring Boot services
  node_instance_types = ["t3.micro"]
  node_desired        = 1
  node_min            = 1
  node_max            = 1
}

# ── RDS ───────────────────────────────────────────────────────────────────────

module "rds" {
  source                = "../../modules/rds"
  identifier            = "${local.name}-db"
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  eks_security_group_id = module.eks.cluster_security_group_id
  db_password           = var.db_password

  instance_class      = "db.t3.micro"
  allocated_storage   = 20
  deletion_protection = false  # Set to true for production
}

# ── Outputs (needed by the CI/CD pipeline) ────────────────────────────────────

output "cluster_name"  { value = module.eks.cluster_name }
output "rds_endpoint"  { value = module.rds.endpoint }
output "ecr_registry"  { value = module.eks.ecr_registry }
output "ecr_urls"      { value = module.eks.ecr_urls }
