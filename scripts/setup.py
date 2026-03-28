#!/usr/bin/env python3
"""
Mini Prism — Full AWS Setup Script
===================================
Run this once you have:
  1. AWS CLI configured  (aws configure)
  2. GitHub secrets added (the script tells you exactly what to add)

Usage:
  python3 scripts/setup.py              # full setup
  python3 scripts/setup.py --destroy    # tear down everything
  python3 scripts/setup.py --skip-build # redeploy without rebuilding images
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ── Colours ────────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"

def ok(msg):      print(f"{GREEN}  ✓  {RESET}{msg}")
def info(msg):    print(f"{CYAN}  →  {RESET}{msg}")
def warn(msg):    print(f"{YELLOW}  !  {RESET}{msg}")
def step(msg):    print(f"\n{BOLD}{YELLOW}── {msg} {'─' * max(0, 50 - len(msg))}{RESET}")
def die(msg):     print(f"\n{RED}  ✗  {msg}{RESET}\n"); sys.exit(1)
def header(msg):  print(f"\n{BOLD}{CYAN}{'═' * 55}\n  {msg}\n{'═' * 55}{RESET}\n")

# ── Paths ───────────────────────────────────────────────────────────────────────

SCRIPT_DIR  = Path(__file__).resolve().parent
REPO_ROOT   = SCRIPT_DIR.parent
TF_DIR      = REPO_ROOT / "terraform" / "envs" / "dev"
COMPOSE_SRC = REPO_ROOT / "docker-compose.prod.yml"
SSH_KEY     = Path.home() / ".ssh" / "mini-prism"
REGION      = "ap-southeast-2"

# ── Shell helpers ───────────────────────────────────────────────────────────────

def run(cmd, *, capture=False, check=True, env=None, cwd=None, input=None):
    """Run a shell command. Streams output unless capture=True."""
    kwargs = dict(
        shell=True, check=check,
        env={**os.environ, **(env or {})},
        cwd=cwd or REPO_ROOT,
    )
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
        kwargs["text"]   = True
    if input is not None:
        kwargs["input"] = input
        kwargs["stdin"] = subprocess.PIPE
    return subprocess.run(cmd, **kwargs)


def run_out(cmd, **kwargs) -> str:
    """Run and return stripped stdout."""
    return run(cmd, capture=True, **kwargs).stdout.strip()


def tf(cmd, *, extra_vars=None, cwd=TF_DIR):
    """Run a terraform command in the dev env directory."""
    var_flags = " ".join(f'-var="{k}={v}"' for k, v in (extra_vars or {}).items())
    run(f"terraform {cmd} {var_flags}", cwd=cwd)


def tf_out(key) -> str:
    """Read a single Terraform output value."""
    return run_out(f"terraform output -raw {key}", cwd=TF_DIR)


def prompt_secret(name, description, generate_cmd=None) -> str:
    """Prompt for a secret, with optional auto-generation."""
    while True:
        if generate_cmd:
            val = input(f"  {CYAN}{name}{RESET} ({description}) [enter to generate]: ").strip()
            if not val:
                val = run_out(generate_cmd)
                ok(f"Generated {name}")
                return val
        else:
            val = input(f"  {CYAN}{name}{RESET} ({description}): ").strip()
        if val:
            return val
        warn("Value cannot be empty — try again.")

# ── Step 1: Prerequisites ───────────────────────────────────────────────────────

def check_prerequisites():
    step("Checking prerequisites")

    tools = {
        "aws":       "brew install awscli  /  https://aws.amazon.com/cli/",
        "terraform": "brew install terraform  /  https://developer.hashicorp.com/terraform/install",
        "docker":    "https://www.docker.com/products/docker-desktop/",
        "ssh":       "built into macOS/Linux",
        "ssh-keygen":"built into macOS/Linux",
    }
    for tool, install_hint in tools.items():
        if not shutil.which(tool):
            die(f"'{tool}' not found.\nInstall: {install_hint}")
        ok(tool)

    # AWS credentials
    result = run("aws sts get-caller-identity", capture=True, check=False)
    if result.returncode != 0:
        die("AWS credentials not configured.\nRun: aws configure")

    identity = json.loads(result.stdout)
    ok(f"AWS account {identity['Account']} ({REGION})")
    return identity["Account"]


# ── Step 2: SSH key ─────────────────────────────────────────────────────────────

def ensure_ssh_key():
    step("SSH key pair")

    if SSH_KEY.exists():
        warn(f"SSH key already exists at {SSH_KEY} — reusing")
    else:
        run(f'ssh-keygen -t rsa -b 4096 -f "{SSH_KEY}" -N "" -C "mini-prism-deploy"')
        ok(f"Created {SSH_KEY}")

    pub = SSH_KEY.with_suffix(".pub").read_text().strip()
    ok(f"Public key: {pub[:60]}...")
    return pub


# ── Step 3: S3 state bucket ─────────────────────────────────────────────────────

def ensure_s3_bucket(account_id: str) -> str:
    step("Terraform state S3 bucket")

    bucket = f"mini-prism-tfstate-{account_id}"

    result = run(f"aws s3api head-bucket --bucket {bucket}", capture=True, check=False)
    if result.returncode == 0:
        warn(f"Bucket {bucket} already exists — skipping")
    else:
        run(f"aws s3api create-bucket --bucket {bucket} --region {REGION} "
            f"--create-bucket-configuration LocationConstraint={REGION}")
        run(f"aws s3api put-bucket-versioning --bucket {bucket} "
            f"--versioning-configuration Status=Enabled")
        run(f"aws s3api put-bucket-encryption --bucket {bucket} "
            f"--server-side-encryption-configuration "
            f'"{{\"Rules\":[{{\"ApplyServerSideEncryptionByDefault\":{{\"SSEAlgorithm\":\"AES256\"}}}}]}}"')
        ok(f"Created {bucket}")

    return bucket


# ── Step 4: GitHub secrets prompt ───────────────────────────────────────────────

def print_github_secrets(account_id: str, bucket: str, pub_key: str):
    step("GitHub Actions secrets")

    aws_key_id     = run_out("aws configure get aws_access_key_id")
    aws_secret     = run_out("aws configure get aws_secret_access_key")
    priv_key       = SSH_KEY.read_text().strip()

    print(f"""
  {BOLD}Add these secrets at:{RESET}
  {CYAN}https://github.com/udaydaroch/POSSystem1/settings/secrets/actions{RESET}

  {BOLD}{'Secret':<24} Value{RESET}
  {'─'*60}
  {'AWS_ACCESS_KEY_ID':<24} {aws_key_id}
  {'AWS_SECRET_ACCESS_KEY':<24} {aws_secret[:8]}... (your secret key)
  {'TF_STATE_BUCKET':<24} {bucket}
  {'SSH_PUBLIC_KEY':<24} {pub_key[:40]}...
  {'SSH_PRIVATE_KEY':<24} (multi-line — see below)
  {'DB_PASSWORD':<24} (you'll set this next)
  {'JWT_SECRET':<24} (you'll set this next)

  {BOLD}SSH_PRIVATE_KEY{RESET} — copy the ENTIRE output of:
  {YELLOW}cat {SSH_KEY}{RESET}

  {BOLD}DB_PASSWORD{RESET} — choose a password like: MyPass123!
  {BOLD}JWT_SECRET{RESET}  — run: {YELLOW}openssl rand -base64 32{RESET}
""")

    input(f"  {BOLD}Press Enter once you've added all 7 secrets to GitHub...{RESET}")


# ── Step 5: Collect secrets locally ─────────────────────────────────────────────

def collect_local_secrets() -> dict:
    step("Local deployment secrets")
    print("  (These are used to provision RDS and configure the app)\n")

    db_password = prompt_secret("DB_PASSWORD", "PostgreSQL password e.g. MyPass123!")
    jwt_secret  = prompt_secret("JWT_SECRET",  "JWT signing secret",
                                generate_cmd="openssl rand -base64 32")
    return {"db_password": db_password, "jwt_secret": jwt_secret}


# ── Step 6: Terraform ───────────────────────────────────────────────────────────

def run_terraform(bucket: str, pub_key: str, secrets: dict):
    step("Terraform — provisioning infrastructure")
    info("This takes ~10 minutes on first run (RDS startup is slow)...")

    # Escape the public key for shell
    safe_key = pub_key.replace('"', '\\"')

    run(f'terraform init -backend-config="bucket={bucket}" -reconfigure', cwd=TF_DIR)
    ok("Terraform initialised")

    run(
        f'terraform apply -auto-approve '
        f'-var="db_password={secrets["db_password"]}" '
        f'-var="ssh_public_key={safe_key}"',
        cwd=TF_DIR,
    )
    ok("Infrastructure provisioned")


# ── Step 7: Read outputs ────────────────────────────────────────────────────────

def read_outputs() -> dict:
    step("Reading infrastructure outputs")

    outputs = {
        "ec2_ip":       tf_out("ec2_public_ip"),
        "rds_host":     tf_out("rds_endpoint"),
        "ecr_registry": tf_out("ecr_registry"),
        "app_url":      tf_out("app_url"),
    }

    ok(f"EC2:  {outputs['ec2_ip']}")
    ok(f"RDS:  {outputs['rds_host']}")
    ok(f"ECR:  {outputs['ecr_registry']}")
    return outputs


# ── Step 8: Build & push images ─────────────────────────────────────────────────

def build_and_push(ecr_registry: str) -> str:
    step("Building and pushing Docker images")

    # ECR login
    token = run_out(f"aws ecr get-login-password --region {REGION}")
    run(f"docker login --username AWS --password-stdin {ecr_registry}", input=token)
    ok("ECR login successful")

    tag = run_out("git rev-parse --short HEAD") or "latest"
    info(f"Image tag: {tag}")

    services = ["pos-service", "inventory-service", "auth-service"]
    for service in services:
        info(f"Building {service}...")
        run(
            f"docker build --platform linux/amd64 "
            f"-t {ecr_registry}/mini-prism/{service}:{tag} "
            f"-t {ecr_registry}/mini-prism/{service}:latest "
            f"./services/{service}"
        )
        run(f"docker push {ecr_registry}/mini-prism/{service}:{tag}")
        run(f"docker push {ecr_registry}/mini-prism/{service}:latest")
        ok(f"{service} pushed")

    info("Building frontend...")
    run(
        f"docker build --platform linux/amd64 "
        f"-t {ecr_registry}/mini-prism/frontend:{tag} "
        f"-t {ecr_registry}/mini-prism/frontend:latest "
        f"./frontend"
    )
    run(f"docker push {ecr_registry}/mini-prism/frontend:{tag}")
    run(f"docker push {ecr_registry}/mini-prism/frontend:latest")
    ok("frontend pushed")

    return tag


# ── Step 9: Deploy to EC2 via SSH ───────────────────────────────────────────────

def ssh(ec2_ip: str, command: str, *, input_text=None):
    """Run a command on the EC2 instance."""
    ssh_cmd = (
        f'ssh -i "{SSH_KEY}" '
        f"-o StrictHostKeyChecking=no "
        f"-o ConnectTimeout=15 "
        f"ec2-user@{ec2_ip} {repr(command)}"
    )
    run(ssh_cmd, input=input_text)


def scp_file(ec2_ip: str, local: Path, remote: str):
    run(
        f'scp -i "{SSH_KEY}" -o StrictHostKeyChecking=no '
        f'"{local}" ec2-user@{ec2_ip}:{remote}'
    )


def wait_for_ssh(ec2_ip: str):
    info("Waiting for EC2 to be reachable via SSH...")
    for attempt in range(1, 25):
        result = run(
            f'ssh -i "{SSH_KEY}" -o StrictHostKeyChecking=no -o ConnectTimeout=10 '
            f"ec2-user@{ec2_ip} echo ok",
            capture=True, check=False,
        )
        if result.returncode == 0:
            ok("EC2 is reachable")
            return
        info(f"Attempt {attempt}/24 — retrying in 15s...")
        time.sleep(15)
    die("Could not reach EC2 after 6 minutes. Check the AWS console.")


def deploy_to_ec2(outputs: dict, secrets: dict, image_tag: str):
    step("Deploying to EC2")

    ec2_ip       = outputs["ec2_ip"]
    ecr_registry = outputs["ecr_registry"]
    rds_host     = outputs["rds_host"]

    wait_for_ssh(ec2_ip)

    # Copy docker-compose file
    scp_file(ec2_ip, COMPOSE_SRC, "/opt/mini-prism/docker-compose.yml")
    ok("docker-compose.yml copied")

    # Write .env file
    env_content = "\n".join([
        f"ECR_REGISTRY={ecr_registry}",
        f"IMAGE_TAG={image_tag}",
        f"DB_HOST={rds_host}",
        f"DB_PASSWORD={secrets['db_password']}",
        f"JWT_SECRET={secrets['jwt_secret']}",
    ])
    ssh(ec2_ip, "cat > /opt/mini-prism/.env", input_text=env_content)
    ok(".env written")

    # Log in to ECR and start services
    remote_script = f"""
set -e
aws ecr get-login-password --region {REGION} \\
  | docker login --username AWS --password-stdin {ecr_registry}
cd /opt/mini-prism
docker compose pull
docker compose --env-file .env up -d --remove-orphans
docker compose ps
"""
    ssh(ec2_ip, f"bash -c {repr(remote_script)}")
    ok("Services started")


# ── Destroy ─────────────────────────────────────────────────────────────────────

def destroy(account_id: str):
    header("Mini Prism — Destroy All Infrastructure")

    print(f"  {RED}{BOLD}⚠  WARNING: This deletes EVERYTHING — EC2, RDS, VPC, all data.{RESET}\n")
    confirm = input("  Type 'destroy' to confirm: ").strip()
    if confirm != "destroy":
        warn("Cancelled.")
        return

    bucket = f"mini-prism-tfstate-{account_id}"

    # Delete ECR images first (terraform can't destroy non-empty repos)
    step("Clearing ECR repositories")
    for repo in ["pos-service", "inventory-service", "auth-service", "frontend"]:
        full = f"mini-prism/{repo}"
        result = run(
            f"aws ecr list-images --repository-name {full} "
            f"--region {REGION} --query 'imageIds[*]' --output json",
            capture=True, check=False,
        )
        if result.returncode != 0 or result.stdout.strip() in ("", "[]"):
            warn(f"{full} — empty or not found, skipping")
            continue
        images = result.stdout.strip()
        run(
            f"aws ecr batch-delete-image --repository-name {full} "
            f"--region {REGION} --image-ids '{images}'",
            capture=True, check=False,
        )
        ok(f"Cleared {full}")

    # Terraform destroy
    step("Terraform destroy")
    dummy_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC dummy@destroy"
    run(f'terraform init -backend-config="bucket={bucket}" -reconfigure', cwd=TF_DIR)
    run(
        f'terraform destroy -auto-approve '
        f'-var="db_password=destroying" '
        f'-var="ssh_public_key={dummy_key}"',
        cwd=TF_DIR,
    )
    ok("All infrastructure destroyed")

    step("Done")
    print(f"\n  The S3 state bucket ({bucket}) was kept.")
    print(f"  Delete it manually if you want:")
    print(f"  {YELLOW}aws s3 rb s3://{bucket} --force{RESET}\n")


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Mini Prism AWS setup")
    parser.add_argument("--destroy",    action="store_true", help="Tear down all infrastructure")
    parser.add_argument("--skip-build", action="store_true", help="Skip Docker build, redeploy existing images")
    args = parser.parse_args()

    header("Mini Prism — AWS Setup")

    account_id = check_prerequisites()

    if args.destroy:
        destroy(account_id)
        return

    pub_key = ensure_ssh_key()
    bucket  = ensure_s3_bucket(account_id)

    print_github_secrets(account_id, bucket, pub_key)

    secrets = collect_local_secrets()

    run_terraform(bucket, pub_key, secrets)

    outputs = read_outputs()

    if args.skip_build:
        image_tag = run_out("git rev-parse --short HEAD") or "latest"
        warn(f"Skipping build — using existing images with tag: {image_tag}")
    else:
        image_tag = build_and_push(outputs["ecr_registry"])

    deploy_to_ec2(outputs, secrets, image_tag)

    step("All done!")
    print(f"""
  {GREEN}{BOLD}✓ Mini Prism is live!{RESET}

  {BOLD}App URL:{RESET}   {CYAN}{outputs['app_url']}{RESET}
  {BOLD}SSH in:{RESET}    ssh -i {SSH_KEY} ec2-user@{outputs['ec2_ip']}
  {BOLD}Logs:{RESET}      ssh -i {SSH_KEY} ec2-user@{outputs['ec2_ip']} 'cd /opt/mini-prism && docker compose logs -f'
  {BOLD}Destroy:{RESET}   python3 scripts/setup.py --destroy
""")


if __name__ == "__main__":
    main()
