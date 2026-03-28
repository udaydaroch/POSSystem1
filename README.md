# Mini Prism — ERP & Point of Sale System

A production-grade mini ERP/POS system built with Java (Spring Boot), deployed on AWS using Terraform, Docker, and Kubernetes. Inspired by real-world enterprise systems like Noel Leeming's Prism platform.

## Architecture

```
Client (POS Terminal / Browser)
        │
        ▼
AWS ALB (Application Load Balancer)
        │
        ▼
EKS Cluster (Kubernetes)
  ├── pos-service        :8080  — Sales, checkout, receipts
  ├── inventory-service  :8081  — Products, stock levels
  └── auth-service       :8082  — JWT auth, user roles
        │
        ▼
AWS RDS (PostgreSQL) + ElastiCache (Redis) + S3
```

## Tech Stack

| Layer        | Technology                              |
|--------------|-----------------------------------------|
| Backend      | Java 21, Spring Boot 3, Spring Security |
| Database     | PostgreSQL (AWS RDS)                    |
| Cache        | Redis (AWS ElastiCache)                 |
| Container    | Docker, AWS ECR                         |
| Orchestration| Kubernetes (AWS EKS)                    |
| Infra as Code| Terraform                               |
| CI/CD        | GitHub Actions                          |
| Storage      | AWS S3 (receipts, reports)              |

## Project Structure

```
mini-prism/
├── services/
│   ├── pos-service/          # Point of Sale — checkout, sales, receipts
│   ├── inventory-service/    # Inventory management — products, stock
│   └── auth-service/         # Authentication — JWT, roles, users
├── terraform/
│   ├── modules/
│   │   ├── vpc/              # VPC, subnets, security groups
│   │   ├── eks/              # EKS cluster + node groups
│   │   └── rds/              # PostgreSQL database
│   └── envs/
│       └── dev/              # Dev environment config
├── kubernetes/
│   ├── deployments/          # K8s Deployment manifests
│   ├── services/             # K8s Service manifests
│   └── ingress/              # ALB Ingress rules
└── .github/
    └── workflows/
        └── deploy.yml        # CI/CD pipeline
```

## Getting Started

### Prerequisites
- Java 21+, Maven
- Docker Desktop
- AWS CLI configured (`aws configure`)
- Terraform 1.6+
- kubectl

### Run locally with Docker Compose
```bash
docker-compose up --build
```

### Deploy to AWS
```bash
cd terraform/envs/dev
terraform init
terraform apply

# Push images to ECR
./scripts/build-and-push.sh

# Apply Kubernetes manifests
kubectl apply -f kubernetes/
```

## API Overview

### Auth Service (`/api/auth`)
| Method | Endpoint        | Description            |
|--------|-----------------|------------------------|
| POST   | /register       | Register a new user    |
| POST   | /login          | Login, returns JWT     |
| GET    | /me             | Get current user info  |

### POS Service (`/api/pos`)
| Method | Endpoint        | Description            |
|--------|-----------------|------------------------|
| POST   | /sale           | Process a sale         |
| GET    | /sale/{id}      | Get sale details       |
| GET    | /sales          | List all sales         |
| POST   | /sale/{id}/void | Void a sale            |

### Inventory Service (`/api/inventory`)
| Method | Endpoint          | Description            |
|--------|-------------------|------------------------|
| GET    | /products         | List all products      |
| POST   | /products         | Create a product       |
| GET    | /products/{id}    | Get product details    |
| PUT    | /products/{id}    | Update product         |
| PATCH  | /products/{id}/stock | Adjust stock level  |
# POSSystem1
