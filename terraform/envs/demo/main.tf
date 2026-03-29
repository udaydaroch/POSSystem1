# ── Mini Prism — Demo Environment (EKS) ───────────────────────────────────────
# Used for interview demos only. Spin up before the demo, destroy after.
#
#   terraform init -backend-config="bucket=<your-s3-bucket>"
#   terraform apply -var="db_password=<password>"
#
# Estimated cost: ~$5-10/day. Run terraform destroy when done.

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
  name         = "mini-prism-demo"
  cluster_name = "mini-prism-demo"
  region       = var.aws_region
  azs          = ["${var.aws_region}a", "${var.aws_region}b"]
}

# ── VPC ───────────────────────────────────────────────────────────────────────
# NAT gateway required — EKS nodes in private subnets need internet to pull ECR images

module "vpc" {
  source             = "../../modules/vpc"
  name               = local.name
  vpc_cidr           = "10.1.0.0/16"
  availability_zones = local.azs
  create_nat_gateway = true
  tags               = {}
}

# ── EKS ───────────────────────────────────────────────────────────────────────

module "eks" {
  source              = "../../modules/eks"
  cluster_name        = local.cluster_name
  vpc_id              = module.vpc.vpc_id
  public_subnet_ids   = module.vpc.public_subnet_ids
  private_subnet_ids  = module.vpc.private_subnet_ids
  node_instance_types = ["t3.medium"]
  node_desired        = 2
  node_min            = 1
  node_max            = 3
  tags                = {}
}

# ── RDS ───────────────────────────────────────────────────────────────────────

module "rds" {
  source                = "../../modules/rds"
  identifier            = "${local.name}-db"
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  app_security_group_id = module.eks.cluster_security_group_id
  db_password           = var.db_password
  db_username           = "prism"
  instance_class        = "db.t3.micro"
  allocated_storage     = 20
  multi_az              = false
  deletion_protection   = false
  tags                  = {}
}

# ── OIDC Provider ─────────────────────────────────────────────────────────────
# Allows K8s service accounts to assume IAM roles (needed for AWS LBC)

data "tls_certificate" "eks" {
  url = module.eks.cluster_oidc_issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  url             = module.eks.cluster_oidc_issuer
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
}

# ── AWS Load Balancer Controller IAM ─────────────────────────────────────────
# The LBC runs inside the cluster and creates the ALB for the Ingress resource.

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

output "cluster_name"  { value = module.eks.cluster_name }
output "ecr_registry"  { value = module.eks.ecr_registry }
output "rds_endpoint"  { value = module.rds.endpoint }
output "lbc_role_arn"  { value = aws_iam_role.lbc.arn }
