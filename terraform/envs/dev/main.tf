# ── Mini Prism — Dev Environment (Free Tier) ──────────────────────────────────
# Run from this directory:
#   terraform init -backend-config="bucket=<your-s3-bucket>"
#   terraform plan -var="db_password=<password>" -var="ssh_public_key=$(cat ~/.ssh/id_rsa.pub)"
#   terraform apply -var="db_password=<password>" -var="ssh_public_key=$(cat ~/.ssh/id_rsa.pub)"
#
# Free-tier costs: $0/month (within 12-month free tier limits)
#   - EC2 t2.micro:   750 hrs/month free
#   - RDS db.t2.micro: 750 hrs/month free
#   - No NAT gateways (disabled)

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # bucket passed at init time: terraform init -backend-config="bucket=<name>"
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
  create_nat_gateway = false
  tags               = {}
}

# ── EC2 (replaces EKS — free tier eligible) ───────────────────────────────────

module "ec2" {
  source           = "../../modules/ec2"
  name             = local.name
  vpc_id           = module.vpc.vpc_id
  public_subnet_id = module.vpc.public_subnet_ids[0]
  public_key       = var.ssh_public_key
  instance_type    = "t3.micro"
  tags             = {}
}

# ── RDS ───────────────────────────────────────────────────────────────────────

module "rds" {
  source                = "../../modules/rds"
  identifier            = "${local.name}-db"
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  app_security_group_id = module.ec2.security_group_id
  db_password           = var.db_password
  db_username           = "prism"

  instance_class      = "db.t3.micro"
  allocated_storage   = 20
  multi_az            = false
  deletion_protection = false
  tags                = {}
}

# ── Outputs ───────────────────────────────────────────────────────────────────

output "ec2_public_ip"  { value = module.ec2.public_ip }
output "ec2_public_dns" { value = module.ec2.public_dns }
output "rds_endpoint"   { value = module.rds.endpoint }
output "ecr_registry"   { value = module.ec2.ecr_registry }
output "ecr_urls"       { value = module.ec2.ecr_urls }
output "app_url"        { value = "http://${module.ec2.public_ip}" }
