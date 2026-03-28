# ── EC2 Module ────────────────────────────────────────────────────────────────
# Single t2.micro instance running Docker Compose.
# Free-tier eligible: 750 hrs/month for 12 months.

# ── IAM: allow EC2 to pull from ECR ──────────────────────────────────────────

resource "aws_iam_role" "ec2" {
  name = "${var.name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ecr_read" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.name}-ec2-profile"
  role = aws_iam_role.ec2.name
  tags = var.tags
}

# ── Security group ────────────────────────────────────────────────────────────

resource "aws_security_group" "ec2" {
  name        = "${var.name}-ec2-sg"
  description = "HTTP, HTTPS and SSH inbound"
  vpc_id      = var.vpc_id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.name}-ec2-sg" })
}

# ── Key pair ──────────────────────────────────────────────────────────────────

resource "aws_key_pair" "main" {
  key_name   = "${var.name}-key"
  public_key = var.public_key
  tags       = var.tags
}

# ── AMI: latest Amazon Linux 2023 ─────────────────────────────────────────────

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ── EC2 instance ──────────────────────────────────────────────────────────────

resource "aws_instance" "main" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = var.instance_type
  subnet_id                   = var.public_subnet_id
  vpc_security_group_ids      = [aws_security_group.ec2.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2.name
  key_name                    = aws_key_pair.main.key_name
  associate_public_ip_address = true

  user_data = <<-EOF
    #!/bin/bash
    dnf install -y docker
    systemctl enable --now docker
    usermod -aG docker ec2-user
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-linux-x86_64 \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    mkdir -p /opt/mini-prism
    systemctl enable --now amazon-ssm-agent
  EOF

  user_data_replace_on_change = true

  root_block_device {
    volume_size = 8
    volume_type = "gp2"
  }

  # Replace the instance if the key pair changes — new key only takes effect at launch time
  lifecycle {
    replace_triggered_by = [aws_key_pair.main]
  }

  tags = merge(var.tags, { Name = var.name })
}

# ── ECR repositories ──────────────────────────────────────────────────────────

resource "aws_ecr_repository" "services" {
  for_each = toset(["pos-service", "inventory-service", "auth-service", "frontend"])

  name                 = "mini-prism/${each.key}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = var.tags
}
