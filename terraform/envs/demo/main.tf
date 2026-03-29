# ── Mini Prism — Demo Environment (EKS) ───────────────────────────────────────
# PostgreSQL runs inside the cluster — no external RDS needed.
# EKS nodes run in public subnets — no NAT gateway cost.
#
# Spin up:   trigger "Deploy Demo (EKS)" in GitHub Actions
# Tear down: trigger "Teardown Demo (EKS)" after the interview
#
# Estimated cost: ~$5/day (EKS control plane + 2x t3.medium nodes)

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    http = {
      source  = "hashicorp/http"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    key    = "mini-prism/demo/terraform.tfstate"
    region = "ap-southeast-2"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "mini-prism"
      Environment = "demo"
      ManagedBy   = "terraform"
    }
  }
}

locals {
  cluster_name = "mini-prism-demo"
  azs          = ["${var.aws_region}a", "${var.aws_region}b"]
}

# ── VPC ───────────────────────────────────────────────────────────────────────
# No NAT gateway — nodes go in public subnets so they can reach ECR directly.

module "vpc" {
  source             = "../../modules/vpc"
  name               = "mini-prism-demo"
  vpc_cidr           = "10.1.0.0/16"
  availability_zones = local.azs
  create_nat_gateway = false
  tags               = {}
}

# ── EKS ───────────────────────────────────────────────────────────────────────
# Nodes in public subnets (internet access without NAT gateway).
# ECR repos shared with dev — not recreated here.

module "eks" {
  source              = "../../modules/eks"
  cluster_name        = local.cluster_name
  vpc_id              = module.vpc.vpc_id
  public_subnet_ids   = module.vpc.public_subnet_ids
  private_subnet_ids  = module.vpc.private_subnet_ids
  node_subnet_ids     = module.vpc.public_subnet_ids
  node_instance_types = ["t3.medium"]
  node_desired        = 2
  node_min            = 1
  node_max            = 3
  create_ecr_repos    = false
  tags                = {}
}

# ── OIDC Provider ─────────────────────────────────────────────────────────────

data "tls_certificate" "eks" {
  url = module.eks.cluster_oidc_issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  url             = module.eks.cluster_oidc_issuer
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
}

# ── AWS Load Balancer Controller IAM ─────────────────────────────────────────

data "http" "lbc_policy" {
  url = "https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json"
}

resource "aws_iam_policy" "lbc" {
  name   = "${local.cluster_name}-lbc-policy"
  policy = data.http.lbc_policy.response_body
}

resource "aws_iam_role" "lbc" {
  name = "${local.cluster_name}-lbc-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.eks.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${replace(module.eks.cluster_oidc_issuer, "https://", "")}:sub" = "system:serviceaccount:kube-system:aws-load-balancer-controller"
          "${replace(module.eks.cluster_oidc_issuer, "https://", "")}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lbc" {
  role       = aws_iam_role.lbc.name
  policy_arn = aws_iam_policy.lbc.arn
}

# ── Outputs ───────────────────────────────────────────────────────────────────

output "cluster_name" { value = module.eks.cluster_name }
output "ecr_registry" { value = module.eks.ecr_registry }
output "lbc_role_arn"  { value = aws_iam_role.lbc.arn }
