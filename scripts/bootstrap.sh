#!/usr/bin/env bash
# ── Mini Prism Bootstrap ──────────────────────────────────────────────────────
# Run this ONCE before your first deployment.
# It creates the S3 bucket for Terraform state and an SSH key pair.
#
# Usage: ./scripts/bootstrap.sh
# Prerequisites: aws cli, ssh-keygen

set -euo pipefail

REGION="ap-southeast-2"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

info()    { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }
section() { echo ""; echo -e "${YELLOW}── $1 ──────────────────────────────────${NC}"; }

# ── Check prerequisites ───────────────────────────────────────────────────────

section "Checking prerequisites"

command -v aws       >/dev/null 2>&1 || error "aws CLI not found. Install: https://aws.amazon.com/cli/"
command -v terraform >/dev/null 2>&1 || error "Terraform not found. Install: https://developer.hashicorp.com/terraform/install"
command -v docker    >/dev/null 2>&1 || error "Docker not found. Install: https://docs.docker.com/get-docker/"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null) \
  || error "AWS credentials not configured. Run: aws configure"

info "AWS account: $ACCOUNT_ID (region: $REGION)"

# ── SSH key pair ──────────────────────────────────────────────────────────────

section "SSH key pair"

KEY_PATH="$HOME/.ssh/mini-prism"

if [ -f "$KEY_PATH" ]; then
  warn "SSH key already exists at $KEY_PATH — skipping"
else
  ssh-keygen -t rsa -b 4096 -f "$KEY_PATH" -N "" -C "mini-prism-deploy"
  info "SSH key created at $KEY_PATH"
fi

info "Public key: $(cat ${KEY_PATH}.pub)"

# ── S3 bucket for Terraform state ────────────────────────────────────────────

section "Terraform state bucket"

BUCKET="mini-prism-tfstate-${ACCOUNT_ID}"

if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  warn "Bucket $BUCKET already exists — skipping"
else
  aws s3api create-bucket \
    --bucket "$BUCKET" \
    --region "$REGION" \
    --create-bucket-configuration LocationConstraint="$REGION"

  aws s3api put-bucket-versioning \
    --bucket "$BUCKET" \
    --versioning-configuration Status=Enabled

  aws s3api put-bucket-encryption \
    --bucket "$BUCKET" \
    --server-side-encryption-configuration \
    '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

  info "Created S3 bucket: $BUCKET"
fi

# ── Terraform init ────────────────────────────────────────────────────────────

section "Terraform init"

cd "$(dirname "$0")/../terraform/envs/dev"
terraform init -backend-config="bucket=$BUCKET" -reconfigure
info "Terraform initialised"

# ── Summary ───────────────────────────────────────────────────────────────────

section "Bootstrap complete"

echo ""
echo "Next step: run the deploy script"
echo ""
echo "  ./scripts/deploy.sh"
echo ""
echo "You will be prompted for:"
echo "  DB_PASSWORD  — password for your RDS PostgreSQL instance"
echo "  JWT_SECRET   — secret for signing JWTs (run: openssl rand -base64 32)"
echo ""
echo "GitHub Actions secrets to add at:"
echo "  https://github.com/udaydaroch/POSSystem1/settings/secrets/actions"
echo ""
echo "  AWS_ACCESS_KEY_ID      = $(aws configure get aws_access_key_id)"
echo "  AWS_SECRET_ACCESS_KEY  = $(aws configure get aws_secret_access_key)"
echo "  TF_STATE_BUCKET        = $BUCKET"
echo "  SSH_PUBLIC_KEY         = $(cat ${KEY_PATH}.pub)"
echo "  SSH_PRIVATE_KEY        = (contents of ${KEY_PATH})"
echo "  DB_PASSWORD            = <your-db-password>"
echo "  JWT_SECRET             = <your-jwt-secret>"
