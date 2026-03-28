#!/usr/bin/env bash
# ── Mini Prism Deploy ─────────────────────────────────────────────────────────
# Full deploy: Terraform → build images → push to ECR → restart on EC2.
#
# Usage:
#   ./scripts/deploy.sh                        # interactive (prompts for secrets)
#   ./scripts/deploy.sh --tag v1.2.3           # deploy specific image tag
#   ./scripts/deploy.sh --skip-terraform       # skip infra, just redeploy app
#   ./scripts/deploy.sh --skip-build           # skip build, redeploy existing images
#
# Prerequisites: aws cli, terraform, docker, ssh

set -euo pipefail

REGION="ap-southeast-2"
KEY_PATH="${HOME}/.ssh/mini-prism"
TF_DIR="$(dirname "$0")/../terraform/envs/dev"
IMAGE_TAG="${GITHUB_SHA:0:8}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo latest)}"
SKIP_TERRAFORM=false
SKIP_BUILD=false

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()    { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }
section() { echo ""; echo -e "${YELLOW}── $1 ──────────────────────────────────${NC}"; }

# ── Parse arguments ───────────────────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
  case $1 in
    --tag)             IMAGE_TAG="$2"; shift 2 ;;
    --skip-terraform)  SKIP_TERRAFORM=true; shift ;;
    --skip-build)      SKIP_BUILD=true; shift ;;
    *) error "Unknown argument: $1" ;;
  esac
done

# ── Check prerequisites ───────────────────────────────────────────────────────

section "Checking prerequisites"

command -v aws       >/dev/null 2>&1 || error "aws CLI not installed"
command -v terraform >/dev/null 2>&1 || error "Terraform not installed"
command -v docker    >/dev/null 2>&1 || error "Docker not installed"
command -v ssh       >/dev/null 2>&1 || error "ssh not installed"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text) \
  || error "AWS credentials not configured. Run: aws configure"

[ -f "$KEY_PATH" ] || error "SSH key not found at $KEY_PATH. Run: ./scripts/bootstrap.sh"

info "Deploying as AWS account: $ACCOUNT_ID"
info "Image tag: $IMAGE_TAG"

# ── Secrets ───────────────────────────────────────────────────────────────────

section "Secrets"

# Use env vars if set (CI), otherwise prompt
if [ -z "${DB_PASSWORD:-}" ]; then
  read -rsp "Enter DB_PASSWORD: " DB_PASSWORD; echo
fi
if [ -z "${JWT_SECRET:-}" ]; then
  read -rsp "Enter JWT_SECRET (or press enter to generate): " JWT_SECRET; echo
  [ -z "$JWT_SECRET" ] && JWT_SECRET=$(openssl rand -base64 32)
fi

BUCKET="mini-prism-tfstate-${ACCOUNT_ID}"

# ── Terraform ─────────────────────────────────────────────────────────────────

if [ "$SKIP_TERRAFORM" = false ]; then
  section "Terraform"

  cd "$TF_DIR"
  terraform init -backend-config="bucket=$BUCKET" -reconfigure

  terraform apply -auto-approve \
    -var="db_password=$DB_PASSWORD" \
    -var="ssh_public_key=$(cat ${KEY_PATH}.pub)"

  info "Terraform apply complete"
  cd - >/dev/null
fi

# ── Read Terraform outputs ────────────────────────────────────────────────────

section "Reading infrastructure details"

cd "$TF_DIR"
EC2_IP=$(terraform output -raw ec2_public_ip)
RDS_HOST=$(terraform output -raw rds_endpoint)
ECR_REGISTRY=$(terraform output -raw ecr_registry)
cd - >/dev/null

info "EC2:  $EC2_IP"
info "RDS:  $RDS_HOST"
info "ECR:  $ECR_REGISTRY"

# ── Build and push Docker images ──────────────────────────────────────────────

if [ "$SKIP_BUILD" = false ]; then
  section "Building and pushing images"

  aws ecr get-login-password --region "$REGION" \
    | docker login --username AWS --password-stdin "$ECR_REGISTRY"

  REPO_ROOT="$(dirname "$0")/.."

  for service in pos-service inventory-service auth-service; do
    echo "  Building $service..."
    docker build --platform linux/amd64 \
      -t "$ECR_REGISTRY/mini-prism/$service:$IMAGE_TAG" \
      -t "$ECR_REGISTRY/mini-prism/$service:latest" \
      "$REPO_ROOT/services/$service"
    docker push "$ECR_REGISTRY/mini-prism/$service:$IMAGE_TAG"
    docker push "$ECR_REGISTRY/mini-prism/$service:latest"
    info "$service pushed"
  done

  echo "  Building frontend..."
  docker build --platform linux/amd64 \
    -t "$ECR_REGISTRY/mini-prism/frontend:$IMAGE_TAG" \
    -t "$ECR_REGISTRY/mini-prism/frontend:latest" \
    "$REPO_ROOT/frontend"
  docker push "$ECR_REGISTRY/mini-prism/frontend:$IMAGE_TAG"
  docker push "$ECR_REGISTRY/mini-prism/frontend:latest"
  info "frontend pushed"
fi

# ── Deploy to EC2 ─────────────────────────────────────────────────────────────

section "Deploying to EC2 ($EC2_IP)"

SSH_OPTS="-i $KEY_PATH -o StrictHostKeyChecking=no -o ConnectTimeout=30"

# Wait for EC2 to be reachable (first deploy user-data may still be running)
echo "  Waiting for EC2 to be ready..."
for i in {1..20}; do
  ssh $SSH_OPTS ec2-user@"$EC2_IP" "echo ok" >/dev/null 2>&1 && break
  echo "  Attempt $i/20 — retrying in 15s..."
  sleep 15
done
ssh $SSH_OPTS ec2-user@"$EC2_IP" "echo ok" >/dev/null 2>&1 \
  || error "Cannot reach EC2 after 5 minutes"

# Copy docker-compose file
scp $SSH_OPTS \
  "$(dirname "$0")/../docker-compose.prod.yml" \
  ec2-user@"$EC2_IP":/opt/mini-prism/docker-compose.yml

# Write .env file
ssh $SSH_OPTS ec2-user@"$EC2_IP" "cat > /opt/mini-prism/.env" <<EOF
ECR_REGISTRY=${ECR_REGISTRY}
IMAGE_TAG=${IMAGE_TAG}
DB_HOST=${RDS_HOST}
DB_PASSWORD=${DB_PASSWORD}
JWT_SECRET=${JWT_SECRET}
EOF

# Log in to ECR on the instance, pull images, restart
ssh $SSH_OPTS ec2-user@"$EC2_IP" "bash -s" <<REMOTE
set -e
aws ecr get-login-password --region ${REGION} \
  | docker login --username AWS --password-stdin ${ECR_REGISTRY}

cd /opt/mini-prism
docker compose pull
docker compose --env-file .env up -d --remove-orphans
docker compose ps
REMOTE

info "Deployment complete!"

# ── Done ──────────────────────────────────────────────────────────────────────

section "Done"
echo ""
echo "  App URL:  http://${EC2_IP}"
echo "  SSH in:   ssh -i ${KEY_PATH} ec2-user@${EC2_IP}"
echo "  Logs:     ssh -i ${KEY_PATH} ec2-user@${EC2_IP} 'cd /opt/mini-prism && docker compose logs -f'"
echo ""
