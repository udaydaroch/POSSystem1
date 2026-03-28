#!/usr/bin/env bash
# ── Mini Prism Destroy ────────────────────────────────────────────────────────
# Tears down ALL AWS infrastructure: EC2, RDS, VPC, ECR repos.
# The Terraform state S3 bucket is NOT deleted (contains your history).
#
# Usage: ./scripts/destroy.sh
# ⚠ This is IRREVERSIBLE. All data will be lost.

set -euo pipefail

REGION="ap-southeast-2"
TF_DIR="$(dirname "$0")/../terraform/envs/dev"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }
section() { echo ""; echo -e "${YELLOW}── $1 ──────────────────────────────────${NC}"; }

# ── Safety confirmation ───────────────────────────────────────────────────────

echo ""
echo -e "${RED}⚠  WARNING: This will destroy ALL Mini Prism infrastructure${NC}"
echo "   EC2 instance, RDS database, VPC, ECR repos, and all data."
echo ""
read -rp "Type 'destroy' to confirm: " CONFIRM
[ "$CONFIRM" = "destroy" ] || { warn "Cancelled."; exit 0; }

# ── Check prerequisites ───────────────────────────────────────────────────────

section "Checking prerequisites"

command -v aws       >/dev/null 2>&1 || error "aws CLI not installed"
command -v terraform >/dev/null 2>&1 || error "Terraform not installed"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text) \
  || error "AWS credentials not configured"

BUCKET="mini-prism-tfstate-${ACCOUNT_ID}"
info "AWS account: $ACCOUNT_ID"

# ── Delete ECR images (Terraform can't destroy non-empty repos) ───────────────

section "Clearing ECR repositories"

for repo in pos-service inventory-service auth-service frontend; do
  FULL_REPO="mini-prism/$repo"
  echo "  Deleting images in $FULL_REPO..."

  # List all image digests
  IMAGES=$(aws ecr list-images \
    --repository-name "$FULL_REPO" \
    --region "$REGION" \
    --query 'imageIds[*]' \
    --output json 2>/dev/null || echo "[]")

  if [ "$IMAGES" != "[]" ] && [ -n "$IMAGES" ]; then
    aws ecr batch-delete-image \
      --repository-name "$FULL_REPO" \
      --region "$REGION" \
      --image-ids "$IMAGES" >/dev/null
    info "Cleared $FULL_REPO"
  else
    warn "$FULL_REPO is already empty or does not exist"
  fi
done

# ── Terraform destroy ─────────────────────────────────────────────────────────

section "Terraform destroy"

# Need any value for required vars — they won't be used (we're destroying)
DUMMY_KEY="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC dummy@destroy"

cd "$TF_DIR"
terraform init -backend-config="bucket=$BUCKET" -reconfigure

terraform destroy -auto-approve \
  -var="db_password=destroying" \
  -var="ssh_public_key=$DUMMY_KEY"

cd - >/dev/null

info "All infrastructure destroyed"

# ── Done ──────────────────────────────────────────────────────────────────────

section "Done"
echo ""
echo "All AWS resources have been deleted."
echo "The S3 state bucket ($BUCKET) was kept — delete it manually if desired:"
echo "  aws s3 rb s3://$BUCKET --force"
echo ""
