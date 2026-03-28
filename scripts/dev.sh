#!/usr/bin/env bash
# ── Mini Prism — Dev Helper Scripts ──────────────────────────────────────────
# Usage: ./scripts/dev.sh <command>

set -e

COMMAND=${1:-help}

case "$COMMAND" in

  # Start everything locally with Docker Compose
  up)
    echo "Starting Mini Prism locally..."
    docker-compose up --build -d
    echo ""
    echo "Services running:"
    echo "  Auth service:      http://localhost:8082"
    echo "  Inventory service: http://localhost:8081"
    echo "  POS service:       http://localhost:8080"
    echo ""
    echo "PostgreSQL: localhost:5432"
    echo "Use 'docker-compose logs -f' to tail logs"
    ;;

  # Tear down local stack
  down)
    docker-compose down -v
    echo "Stack stopped and volumes removed."
    ;;

  # Run all tests
  test)
    echo "Running tests across all services..."
    for service in pos-service inventory-service auth-service; do
      echo "Testing $service..."
      mvn test -f services/$service/pom.xml -q
    done
    echo "All tests passed!"
    ;;

  # Quick smoke test against local stack
  smoke)
    BASE_AUTH="http://localhost:8082/api/auth"
    echo "Running smoke tests against local stack..."

    echo "1. Register a user..."
    TOKEN=$(curl -s -X POST "$BASE_AUTH/register" \
      -H "Content-Type: application/json" \
      -d '{"username":"cashier1","password":"Password1!","email":"cashier@prism.nz","role":"CASHIER"}' \
      | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
    echo "   Got token: ${TOKEN:0:20}..."

    echo "2. List products..."
    curl -s http://localhost:8081/api/inventory/products \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

    echo "Smoke tests complete!"
    ;;

  # Build and push images to ECR (requires AWS CLI configured)
  push)
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    REGION="ap-southeast-2"
    TAG=${2:-latest}
    ECR="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

    echo "Logging in to ECR..."
    aws ecr get-login-password --region $REGION | \
      docker login --username AWS --password-stdin $ECR

    for service in pos-service inventory-service auth-service; do
      echo "Building and pushing $service:$TAG..."
      docker build -t $ECR/mini-prism/$service:$TAG ./services/$service
      docker push $ECR/mini-prism/$service:$TAG
    done
    echo "All images pushed!"
    ;;

  help|*)
    echo "Mini Prism Dev Scripts"
    echo ""
    echo "Usage: ./scripts/dev.sh <command>"
    echo ""
    echo "Commands:"
    echo "  up      Start local stack with Docker Compose"
    echo "  down    Stop local stack and remove volumes"
    echo "  test    Run all unit/integration tests"
    echo "  smoke   Quick smoke test against running local stack"
    echo "  push    Build and push Docker images to ECR"
    ;;
esac
