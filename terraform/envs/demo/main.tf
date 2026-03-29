# ── Mini Prism — Demo Environment (EKS) ───────────────────────────────────────
# Reuses the existing dev VPC and RDS to stay within free-tier limits.
# EKS nodes run in public subnets (no NAT gateway needed).
# ECR repos are shared with the dev environment.
#
# Spin up:   trigger "Deploy Demo (EKS)" workflow in GitHub Actions
# Tear down: trigger "Teardown Demo (EKS)" workflow after the interview
#
# Estimated cost: ~$5-10/day (EKS control plane + 2x t3.medium nodes)

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
}

# ── Reuse existing dev VPC ────────────────────────────────────────────────────

data "aws_vpc" "dev" {
  tags = { Name = "mini-prism-dev-vpc" }
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.dev.id]
  }
  filter {
    name   = "tag:kubernetes.io/role/elb"
    values = ["1"]
  }
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.dev.id]
  }
  filter {
    name   = "tag:kubernetes.io/role/internal-elb"
    values = ["1"]
  }
}

# ── Reuse existing dev RDS ────────────────────────────────────────────────────

data "aws_db_instance" "dev" {
  db_instance_identifier = "mini-prism-dev-db"
}

data "aws_security_group" "dev_rds" {
  name   = "mini-prism-dev-db-sg"
  vpc_id = data.aws_vpc.dev.id
}

# ── EKS cluster in the dev VPC ────────────────────────────────────────────────
# Nodes go in public subnets so they can reach ECR without a NAT gateway.

module "eks" {
  source              = "../../modules/eks"
  cluster_name        = local.cluster_name
  vpc_id              = data.aws_vpc.dev.id
  public_subnet_ids   = data.aws_subnets.public.ids
  private_subnet_ids  = data.aws_subnets.private.ids
  node_subnet_ids     = data.aws_subnets.public.ids
  node_instance_types = ["t3.medium"]
  node_desired        = 2
  node_min            = 1
  node_max            = 3
  create_ecr_repos    = false
  tags                = {}
}

# Allow EKS pods to reach the existing dev RDS
resource "aws_security_group_rule" "eks_to_rds" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = module.eks.cluster_security_group_id
  security_group_id        = data.aws_security_group.dev_rds.id
  description              = "EKS demo cluster to dev RDS"
}

# ── OIDC Provider (for AWS Load Balancer Controller) ─────────────────────────

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
output "rds_endpoint" { value = data.aws_db_instance.dev.address }
output "lbc_role_arn" { value = aws_iam_role.lbc.arn }
