from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_fill_color(20, 40, 80)
        self.rect(0, 0, 210, 18, 'F')
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(255, 255, 255)
        self.set_y(4)
        self.cell(0, 10, 'Mini-Prism - DevOps Deep Dive', align='C')
        self.set_text_color(0, 0, 0)
        self.ln(14)

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def section_title(self, title):
        self.ln(3)
        self.set_fill_color(220, 230, 255)
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(20, 40, 120)
        self.cell(0, 9, title, fill=True, ln=True)
        self.set_text_color(0, 0, 0)

    def sub_title(self, title):
        self.ln(2)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(40, 70, 170)
        self.cell(0, 7, title, ln=True)
        self.set_text_color(0, 0, 0)

    def body(self, text):
        self.set_font('Helvetica', '', 10)
        self.multi_cell(0, 6, text)

    def bullet(self, items):
        self.set_font('Helvetica', '', 10)
        for item in items:
            self.set_x(self.l_margin + 5)
            self.multi_cell(0, 6, f'*  {item}')

    def code_box(self, lines):
        self.ln(1)
        self.set_fill_color(240, 242, 248)
        self.set_font('Courier', '', 8.5)
        self.set_text_color(30, 30, 30)
        self.rect(self.get_x(), self.get_y(), 190, len(lines) * 5.5 + 4, 'F')
        self.ln(2)
        for line in lines:
            self.cell(4)
            self.cell(0, 5.5, line, ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def need_space(self, h):
        """Add a new page if less than h mm remain on the current page."""
        if self.get_y() + h > self.h - self.b_margin:
            self.add_page()

    def pipeline_diagram(self):
        """Draw the GitHub Actions pipeline flow."""
        self.need_space(45)
        self.ln(4)
        lm = self.l_margin
        pw = 190
        y  = self.get_y()

        stages = [
            ('1. Test', 'Maven test\n3 services', (180, 220, 180), (40, 130, 40)),
            ('2. Terraform', 'provision\nEC2 + RDS', (180, 200, 255), (40, 60, 200)),
            ('3. Build', 'docker build\n4 images', (255, 215, 160), (160, 90, 0)),
            ('4. Push', 'docker push\nto ECR', (255, 185, 185), (180, 40, 40)),
            ('5. Deploy', 'SSM -> EC2\ncompose up', (200, 240, 200), (30, 120, 30)),
        ]

        box_w   = 32
        box_h   = 22
        gap     = (pw - len(stages) * box_w) / (len(stages) - 1)
        arrow_w = 6

        for i, (title, subtitle, fill, text_col) in enumerate(stages):
            bx = lm + i * (box_w + gap)
            self.set_fill_color(*fill)
            self.set_draw_color(*text_col)
            self.rect(bx, y, box_w, box_h, 'FD')
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(*text_col)
            self.set_xy(bx, y + 2)
            self.cell(box_w, 5, title, align='C')
            self.set_font('Helvetica', '', 7)
            for j, line in enumerate(subtitle.split('\n')):
                self.set_xy(bx, y + 9 + j * 5)
                self.cell(box_w, 5, line, align='C')

            # arrow between boxes
            if i < len(stages) - 1:
                ax = bx + box_w + 1
                ay = y + box_h / 2
                self.set_draw_color(100, 100, 100)
                self.line(ax, ay, ax + gap - 2, ay)
                self.line(ax + gap - 2, ay, ax + gap - 5, ay - 2)
                self.line(ax + gap - 2, ay, ax + gap - 5, ay + 2)

        # "needs:" dependency label
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(100, 100, 100)
        self.set_xy(lm, y + box_h + 2)
        self.cell(pw, 5, 'Each job uses "needs:" to run in sequence  -  pipeline stops on any failure', align='C')

        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 0, 0)
        self.set_y(y + box_h + 10)

    def terraform_module_diagram(self):
        """Draw the Terraform module structure."""
        self.need_space(70)
        self.ln(4)
        lm = self.l_margin
        pw = 190
        y  = self.get_y()

        # Root env box
        env_w, env_h = 80, 14
        env_x = lm + (pw - env_w) / 2
        self.set_fill_color(30, 50, 100)
        self.rect(env_x, y, env_w, env_h, 'F')
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(255, 255, 255)
        self.set_xy(env_x, y + 1)
        self.cell(env_w, 6, 'terraform/envs/dev/main.tf', align='C')
        self.set_font('Helvetica', 'I', 7.5)
        self.set_xy(env_x, y + 7)
        self.cell(env_w, 5, '(entry point - calls modules below)', align='C')

        mid = lm + pw / 2
        line_y1 = y + env_h
        line_y2 = line_y1 + 10

        modules = [
            ('modules/vpc', 'VPC, subnets,\nIGW, NAT, routes', (200, 215, 255), (40, 60, 180), lm + 5),
            ('modules/ec2', 'Instance, SG,\nIAM, ECR repos', (255, 220, 180), (160, 80, 0), lm + 68),
            ('modules/rds', 'PostgreSQL,\nsubnet group, SG', (200, 240, 200), (30, 120, 30), lm + 131),
        ]

        mod_w, mod_h = 52, 24
        mod_centers = []
        for label, desc, fill, tcol, mx in modules:
            cx = mx + mod_w / 2
            mod_centers.append(cx)
            # vertical line from root
            self.set_draw_color(100, 100, 120)
            self.line(mid, line_y1, mid, line_y1 + 5)
            self.line(mod_centers[-1], line_y1 + 5, mod_centers[-1], line_y2)
            self.line(mod_centers[-1], line_y2, mod_centers[-1] - 2, line_y2 - 3)
            self.line(mod_centers[-1], line_y2, mod_centers[-1] + 2, line_y2 - 3)

        # horizontal connector
        self.line(mod_centers[0], line_y1 + 5, mod_centers[-1], line_y1 + 5)

        for (label, desc, fill, tcol, mx), cx in zip(modules, mod_centers):
            self.set_fill_color(*fill)
            self.set_draw_color(*tcol)
            self.rect(mx, line_y2, mod_w, mod_h, 'FD')
            self.set_font('Helvetica', 'B', 8)
            self.set_text_color(*tcol)
            self.set_xy(mx, line_y2 + 2)
            self.cell(mod_w, 5, label, align='C')
            self.set_font('Helvetica', '', 7)
            self.set_text_color(50, 50, 50)
            for j, line in enumerate(desc.split('\n')):
                self.set_xy(mx, line_y2 + 9 + j * 5)
                self.cell(mod_w, 5, line, align='C')

        # S3 backend note
        self.set_font('Helvetica', 'I', 7.5)
        self.set_text_color(100, 100, 100)
        self.set_xy(lm, line_y2 + mod_h + 3)
        self.cell(pw, 5, 'State stored remotely in S3  |  backend "s3" { key = "mini-prism/dev/terraform.tfstate" }', align='C')

        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 0, 0)
        self.set_y(line_y2 + mod_h + 10)

    def eks_module_diagram(self):
        """Draw the demo (EKS) Terraform module structure."""
        self.need_space(70)
        self.ln(4)
        lm = self.l_margin
        pw = 190
        y  = self.get_y()

        env_w, env_h = 80, 14
        env_x = lm + (pw - env_w) / 2
        self.set_fill_color(20, 40, 80)
        self.rect(env_x, y, env_w, env_h, 'F')
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(255, 255, 255)
        self.set_xy(env_x, y + 1)
        self.cell(env_w, 6, 'terraform/envs/demo/main.tf', align='C')
        self.set_font('Helvetica', 'I', 7.5)
        self.set_xy(env_x, y + 7)
        self.cell(env_w, 5, '(EKS demo - manual trigger only)', align='C')

        mid = lm + pw / 2
        line_y1 = y + env_h
        line_y2 = line_y1 + 10

        modules = [
            ('modules/vpc', 'VPC, subnets\n(no NAT)', (200, 215, 255), (40, 60, 180), lm + 2),
            ('modules/eks', 'EKS cluster\nnode group, ECR', (220, 190, 255), (100, 30, 180), lm + 57),
            ('OIDC Provider', 'IRSA for\nLBC controller', (255, 230, 180), (150, 90, 0), lm + 112),
            ('LBC IAM Role', 'trust policy\n+ ALB policy', (200, 240, 200), (30, 120, 30), lm + 152),
        ]

        mod_w, mod_h = 36, 24
        mod_centers = []
        for label, desc, fill, tcol, mx in modules:
            cx = mx + mod_w / 2
            mod_centers.append(cx)

        self.set_draw_color(100, 100, 120)
        self.line(mid, line_y1, mid, line_y1 + 5)
        self.line(mod_centers[0], line_y1 + 5, mod_centers[-1], line_y1 + 5)
        for cx in mod_centers:
            self.line(cx, line_y1 + 5, cx, line_y2)
            self.line(cx, line_y2, cx - 2, line_y2 - 3)
            self.line(cx, line_y2, cx + 2, line_y2 - 3)

        for (label, desc, fill, tcol, mx), cx in zip(modules, mod_centers):
            self.set_fill_color(*fill)
            self.set_draw_color(*tcol)
            self.rect(mx, line_y2, mod_w, mod_h, 'FD')
            self.set_font('Helvetica', 'B', 7)
            self.set_text_color(*tcol)
            self.set_xy(mx, line_y2 + 2)
            self.cell(mod_w, 5, label, align='C')
            self.set_font('Helvetica', '', 6.5)
            self.set_text_color(50, 50, 50)
            for j, line in enumerate(desc.split('\n')):
                self.set_xy(mx, line_y2 + 9 + j * 5)
                self.cell(mod_w, 5, line, align='C')

        self.set_font('Helvetica', 'I', 7.5)
        self.set_text_color(100, 100, 100)
        self.set_xy(lm, line_y2 + mod_h + 3)
        self.cell(pw, 5, 'No RDS - PostgreSQL runs as a pod inside the cluster  |  Nodes in public subnets (no NAT cost)', align='C')

        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 0, 0)
        self.set_y(line_y2 + mod_h + 10)

    def k8s_diagram(self):
        """Draw the Kubernetes resource layout."""
        self.need_space(120)
        self.ln(4)
        lm = self.l_margin
        pw = 190
        y  = self.get_y()

        # Outer namespace box
        ns_h = 105
        self.set_fill_color(240, 243, 255)
        self.set_draw_color(80, 110, 200)
        self.rect(lm, y, pw, ns_h, 'FD')

        # Namespace label
        self.set_fill_color(80, 110, 200)
        self.rect(lm, y, pw, 9, 'F')
        self.set_font('Helvetica', 'B', 8.5)
        self.set_text_color(255, 255, 255)
        self.set_xy(lm, y + 1)
        self.cell(pw, 7, 'Kubernetes Namespace: prism', align='C')

        # Ingress row
        ing_y = y + 13
        ing_w, ing_h = 90, 12
        ing_x = lm + (pw - ing_w) / 2
        self.set_fill_color(255, 230, 150)
        self.set_draw_color(160, 110, 0)
        self.rect(ing_x, ing_y, ing_w, ing_h, 'FD')
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(100, 60, 0)
        self.set_xy(ing_x, ing_y + 1)
        self.cell(ing_w, 5, 'Ingress (prism-ingress)', align='C')
        self.set_font('Helvetica', 'I', 7)
        self.set_xy(ing_x, ing_y + 6)
        self.cell(ing_w, 5, 'ALB via AWS Load Balancer Controller', align='C')

        # Service + Deployment rows
        svc_defs = [
            ('auth-service\n:8082\n2 pods', (190, 210, 255), (40, 60, 200)),
            ('inventory-svc\n:8081\n2 pods', (190, 210, 255), (40, 60, 200)),
            ('pos-service\n:8080\n2 pods', (190, 210, 255), (40, 60, 200)),
            ('frontend\n:80\n1 pod', (210, 230, 255), (60, 80, 180)),
        ]

        box_w = (pw - 15) / 4
        box_h = 26
        svc_y = ing_y + ing_h + 8
        centers = []
        mid_ing = ing_x + ing_w / 2

        for i, (label, fill, tcol) in enumerate(svc_defs):
            bx = lm + 3 + i * (box_w + 3)
            cx = bx + box_w / 2
            centers.append(cx)
            self.set_fill_color(*fill)
            self.set_draw_color(*tcol)
            self.rect(bx, svc_y, box_w, box_h, 'FD')
            self.set_font('Helvetica', 'B', 7.5)
            self.set_text_color(*tcol)
            lines = label.split('\n')
            for j, ln in enumerate(lines):
                style = 'B' if j == 0 else ('I' if j == 2 else '')
                self.set_font('Helvetica', style, 7.5 if j == 0 else 7)
                self.set_xy(bx, svc_y + 2 + j * 7)
                self.cell(box_w, 6, ln, align='C')

            # line from ingress to service
            self.set_draw_color(120, 120, 140)
            self.line(cx, ing_y + ing_h, cx, svc_y)

        # Postgres box
        pg_w, pg_h = 50, 20
        pg_x = lm + (pw - pg_w) / 2
        pg_y = svc_y + box_h + 10
        self.set_fill_color(210, 245, 210)
        self.set_draw_color(40, 140, 40)
        self.rect(pg_x, pg_y, pg_w, pg_h, 'FD')
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(20, 110, 20)
        self.set_xy(pg_x, pg_y + 2)
        self.cell(pg_w, 5, 'PostgreSQL pod', align='C')
        self.set_font('Helvetica', '', 7)
        self.set_text_color(40, 40, 40)
        self.set_xy(pg_x, pg_y + 8)
        self.cell(pg_w, 5, 'postgres:5432', align='C')
        self.set_xy(pg_x, pg_y + 13)
        self.cell(pg_w, 5, 'ClusterIP service', align='C')

        # lines from 3 backend services to postgres
        join_y = svc_y + box_h + 5
        pg_cx = pg_x + pg_w / 2
        self.set_draw_color(100, 100, 120)
        for i in range(3):
            self.line(centers[i], svc_y + box_h, centers[i], join_y)
        self.line(centers[0], join_y, centers[2], join_y)
        self.line(pg_cx, join_y, pg_cx, pg_y)
        self.line(pg_cx, pg_y, pg_cx - 2, pg_y + 3)
        self.line(pg_cx, pg_y, pg_cx + 2, pg_y + 3)

        # Secrets label
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(80, 80, 80)
        self.set_xy(lm + 3, y + ns_h - 8)
        self.cell(pw - 6, 6,
            'Secrets: prism-db-secret (DB URLs + credentials)  |  prism-jwt-secret (JWT signing key)',
            align='C')

        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 0, 0)
        self.set_y(y + ns_h + 6)


pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=16)
pdf.add_page()

# ── SECTION 1: Overview ────────────────────────────────────────────────────────
pdf.section_title('1.  DevOps Overview')
pdf.body(
    'Mini-Prism uses a fully automated DevOps pipeline. Every push to main '
    'triggers a GitHub Actions workflow that tests, provisions infrastructure, '
    'builds Docker images, and deploys to AWS without any manual steps. '
    'A separate on-demand workflow deploys the same app to an EKS cluster for '
    'interview demos, and tears it down after.'
)
pdf.bullet([
    'Infrastructure-as-Code: all AWS resources defined in Terraform modules',
    'Containerisation: every service has a multi-stage Dockerfile',
    'Registry: Docker images stored in AWS ECR (private)',
    'Prod deployment: Docker Compose on a single EC2 t3.small via SSM',
    'Demo deployment: Kubernetes on AWS EKS (spin up / tear down on demand)',
    'Pipeline: GitHub Actions with 5 sequential jobs (test -> terraform -> build -> push -> deploy)',
    'Secrets: GitHub Actions Secrets injected at runtime, never in the repository',
])

# ── SECTION 2: Terraform ──────────────────────────────────────────────────────
pdf.section_title('2.  Terraform - Infrastructure as Code')
pdf.body(
    'All AWS infrastructure is defined in Terraform. The code lives in '
    'terraform/ and is split into reusable modules (vpc, ec2, rds, eks) '
    'and two environment entry points (envs/dev for prod, envs/demo for EKS).'
)

pdf.sub_title('Directory layout')
pdf.code_box([
    'terraform/',
    '  modules/',
    '    vpc/        - VPC, public/private subnets, IGW, NAT gateway, route tables',
    '    ec2/        - EC2 instance, security group, IAM role, ECR repos, key pair',
    '    rds/        - RDS PostgreSQL instance, subnet group, security group',
    '    eks/        - EKS cluster, managed node group, IAM roles, ECR repos',
    '  envs/',
    '    dev/        - prod environment  (EC2 + RDS, free-tier eligible)',
    '    demo/       - EKS demo environment  (EKS + in-cluster PostgreSQL)',
])

pdf.sub_title('Prod environment (envs/dev) - module wiring')
pdf.terraform_module_diagram()

pdf.sub_title('Demo environment (envs/demo) - module wiring')
pdf.eks_module_diagram()

pdf.sub_title('How Terraform is run')
pdf.body(
    'The CI/CD pipeline runs terraform apply automatically on every push to main. '
    'Terraform is idempotent - if the infrastructure already exists it makes no '
    'changes. Only real diffs trigger AWS API calls. State is stored in an S3 bucket '
    'so multiple developers (and CI) share the same state.'
)
pdf.code_box([
    '# Initialise (downloads providers, connects to S3 backend)',
    'terraform init -backend-config="bucket=<s3-bucket-name>"',
    '',
    '# Preview changes without applying',
    'terraform plan -var="db_password=..." -var="ssh_public_key=..."',
    '',
    '# Apply (used by CI/CD pipeline)',
    'terraform apply -auto-approve -var="db_password=..." -var="ssh_public_key=..."',
    '',
    '# Tear down (used by teardown-demo workflow)',
    'terraform destroy -auto-approve -var="db_password=..."',
])

pdf.sub_title('Key Terraform design decisions')
pdf.bullet([
    'Module separation: vpc/ec2/rds/eks are independent and reusable across environments',
    'S3 remote state: prevents state conflicts when CI and developers run Terraform concurrently',
    'Sensitive variables: db_password and ssh_public_key passed at runtime, never in .tf files',
    'Idempotent apply: safe to run on every push - no-op if nothing changed',
    'deletion_protection = false on RDS for the demo so terraform destroy works cleanly',
    'NAT gateways disabled in prod (EC2 in public subnet) and demo (EKS nodes in public subnets) '
     'to avoid the ~$32/month NAT cost on a portfolio project',
])

# ── SECTION 3: GitHub Actions Pipeline ───────────────────────────────────────
pdf.add_page()
pdf.section_title('3.  GitHub Actions CI/CD Pipeline')
pdf.body(
    'The pipeline lives in .github/workflows/deploy.yml and runs on every push '
    'to main. It has 5 jobs that run in sequence using the "needs:" keyword - '
    'if any job fails the pipeline stops and nothing is deployed.'
)

pdf.sub_title('Pipeline flow')
pdf.pipeline_diagram()

pdf.sub_title('Job 1 - Test')
pdf.body('Runs Maven tests on all three Java services in parallel steps.')
pdf.code_box([
    'runs-on: ubuntu-latest',
    '',
    '- uses: actions/setup-java@v4  (Java 21, Temurin, Maven cache)',
    '- run: mvn test -f services/pos-service/pom.xml',
    '- run: mvn test -f services/inventory-service/pom.xml',
    '- run: mvn test -f services/auth-service/pom.xml',
])

pdf.sub_title('Job 2 - Terraform')
pdf.body(
    'Provisions or updates the AWS infrastructure. Outputs the EC2 instance ID, '
    'public IP, RDS endpoint, and ECR registry URL for downstream jobs to use.'
)
pdf.code_box([
    'needs: test',
    'if: github.ref == "refs/heads/main"   <- skipped on pull requests',
    '',
    '- terraform init  -backend-config="bucket=${{ secrets.TF_STATE_BUCKET }}"',
    '- terraform apply -auto-approve \\',
    '    -var="db_password=${{ secrets.DB_PASSWORD }}" \\',
    '    -var="ssh_public_key=${{ secrets.SSH_PUBLIC_KEY }}"',
    '',
    '# Outputs passed to later jobs via $GITHUB_OUTPUT',
    'ec2_instance_id, ec2_public_ip, rds_endpoint, ecr_registry',
])

pdf.sub_title('Job 3 - Build & Push')
pdf.body(
    'Builds a Docker image for each service and the frontend, then pushes two tags '
    'to ECR: the short commit SHA (immutable, for rollbacks) and "latest".'
)
pdf.code_box([
    'needs: terraform',
    '',
    'IMAGE_TAG = first 8 chars of GITHUB_SHA  (e.g. "a1b2c3d4")',
    '',
    'for service in pos-service inventory-service auth-service:',
    '  docker build --platform linux/amd64 \\',
    '    -t $ECR_REGISTRY/mini-prism/$service:$IMAGE_TAG \\',
    '    -t $ECR_REGISTRY/mini-prism/$service:latest \\',
    '    ./services/$service',
    '  docker push $ECR_REGISTRY/mini-prism/$service:$IMAGE_TAG',
    '  docker push $ECR_REGISTRY/mini-prism/$service:latest',
    '',
    '# Same pattern for the frontend image',
])

pdf.sub_title('Job 4 - Deploy (SSM -> EC2)')
pdf.body(
    'Sends shell commands to the EC2 instance over AWS SSM (no SSH required). '
    'The commands write the .env file, pull the new images, and restart the '
    'stack with Docker Compose. The job polls SSM until the command completes '
    'or times out after 15 minutes (image pulls are slow on first deploy).'
)
pdf.code_box([
    'needs: [terraform, build-and-push]',
    '',
    '1. Wait for SSM agent to come online (polls every 15s, max 5 min)',
    '2. Base64-encode docker-compose.prod.yml and .env contents',
    '3. Send SSM RunShellScript command:',
    '   - decode + write /opt/mini-prism/docker-compose.yml',
    '   - decode + write /opt/mini-prism/.env',
    '   - aws ecr get-login-password | docker login ...',
    '   - docker compose pull',
    '   - docker compose up -d --remove-orphans',
    '4. Poll SSM command status every 10s (max 15 min)',
    '5. Print stdout/stderr and fail if status != Success',
])

pdf.sub_title('Why SSM instead of SSH?')
pdf.bullet([
    'No inbound port 22 required on the EC2 security group - smaller attack surface',
    'No SSH key management in CI - only AWS IAM credentials needed',
    'SSM logs all commands to CloudWatch automatically - full audit trail',
    'Works even if the instance IP changes after a restart',
])

pdf.sub_title('Secrets used by the pipeline')
pdf.code_box([
    'Secret name           Used in job       Purpose',
    '---------------------------------------------------------',
    'AWS_ACCESS_KEY_ID     terraform,         AWS authentication',
    '                      build, deploy',
    'AWS_SECRET_ACCESS_KEY terraform,         AWS authentication',
    '                      build, deploy',
    'TF_STATE_BUCKET       terraform          S3 bucket for Terraform state',
    'DB_PASSWORD           terraform          RDS master password',
    'SSH_PUBLIC_KEY        terraform          EC2 key pair (for manual SSH)',
    'JWT_SECRET            deploy             JWT signing secret (32+ chars)',
])

# ── SECTION 4: Demo Pipeline (EKS) ───────────────────────────────────────────
pdf.add_page()
pdf.section_title('4.  Demo Pipeline - EKS (deploy-demo.yml)')
pdf.body(
    'A separate workflow at .github/workflows/deploy-demo.yml is triggered '
    'manually from the GitHub Actions UI. It spins up a full EKS cluster, '
    'deploys all services, and prints the ALB URL. The teardown-demo.yml '
    'workflow destroys everything after the interview.'
)

pdf.sub_title('Demo pipeline flow')
pdf.code_box([
    'Trigger: workflow_dispatch  (manual button in GitHub Actions UI)',
    '',
    'Job 1 - Terraform (EKS)',
    '  terraform apply on terraform/envs/demo/',
    '  -> provisions EKS cluster, VPC, OIDC provider, LBC IAM role',
    '  -> outputs: cluster_name, ecr_registry, lbc_role_arn',
    '',
    'Job 2 - Build & Push',
    '  Same as prod pipeline - builds 4 images, pushes to shared ECR repos',
    '  -> outputs: image_tag (short SHA)',
    '',
    'Job 3 - Deploy to EKS',
    '  aws eks update-kubeconfig  (configures kubectl)',
    '  helm install aws-load-balancer-controller  (provisions ALB from Ingress)',
    '  kubectl apply -f kubernetes/services/services.yaml  (namespace + services)',
    '  kubectl create secret generic prism-db-secret  (DB URLs point to postgres:5432)',
    '  kubectl create secret generic prism-jwt-secret',
    '  kubectl apply -f kubernetes/postgres/postgres.yaml  (in-cluster PostgreSQL)',
    '  kubectl rollout status deployment/postgres  (wait for DB to be ready)',
    '  sed ACCOUNT_ID + IMAGE_TAG into manifests, kubectl apply deployments',
    '  kubectl apply -f kubernetes/ingress/ingress.yaml',
    '  Poll ingress for ALB hostname (30 attempts x 10s = max 5 min)',
    '  Print: "Demo is live at: http://<alb-hostname>"',
])

pdf.sub_title('Teardown')
pdf.code_box([
    'Trigger: workflow_dispatch  (manual - run after the interview)',
    '',
    'terraform destroy -auto-approve -var="db_password=..."',
    '  -> destroys EKS cluster, VPC, node groups, OIDC, IAM roles',
    '  -> ECR repos are NOT destroyed (shared with prod)',
    '  -> takes ~10-15 min',
])

# ── SECTION 5: Kubernetes ─────────────────────────────────────────────────────
pdf.add_page()
pdf.section_title('5.  Kubernetes - Resource Layout')
pdf.body(
    'All Kubernetes manifests live under kubernetes/. Every resource is deployed '
    'into the "prism" namespace. The AWS Load Balancer Controller (installed via '
    'Helm) watches the Ingress resource and automatically provisions an '
    'internet-facing AWS ALB.'
)

pdf.sub_title('Resource layout in the cluster')
pdf.k8s_diagram()

pdf.sub_title('Manifest files')
pdf.code_box([
    'kubernetes/',
    '  deployments/',
    '    pos-service.yaml       - 2 replicas, liveness/readiness probes, env from secrets',
    '    other-services.yaml    - auth (x2) and inventory (x2) deployments',
    '    frontend.yaml          - 1 replica, serves the React SPA',
    '  services/',
    '    services.yaml          - ClusterIP services + namespace definition',
    '  ingress/',
    '    ingress.yaml           - ALB Ingress with path-based routing',
    '  secrets/',
    '    secrets.template.yaml  - template only (real values injected by CI)',
    '  postgres/',
    '    postgres.yaml          - PostgreSQL deployment + service + init ConfigMap',
])

pdf.sub_title('Ingress routing rules')
pdf.code_box([
    'Path prefix        ->  Service           Port',
    '----------------------------------------------------',
    '/api/auth          ->  auth-service      8082',
    '/api/inventory     ->  inventory-service 8081',
    '/api/pos           ->  pos-service       8080',
    '/  (catch-all)     ->  frontend          80',
])

pdf.sub_title('Health probes on every service')
pdf.body(
    'Each Java service exposes Spring Boot Actuator health endpoints. '
    'Kubernetes uses two separate probes:'
)
pdf.bullet([
    'livenessProbe  - hits /actuator/health/liveness  (restarts pod if app hangs)',
    'readinessProbe - hits /actuator/health/readiness  (removes pod from load balancer '
     'until app is fully started - prevents traffic during Flyway migrations)',
    'initialDelaySeconds: 30 for liveness, 20 for readiness (Java startup takes ~15s)',
])

pdf.sub_title('Rolling update strategy')
pdf.code_box([
    'strategy:',
    '  type: RollingUpdate',
    '  rollingUpdate:',
    '    maxUnavailable: 0   <- always keep at least one pod serving traffic',
    '    maxSurge: 1         <- spin up one extra pod before taking the old one down',
    '',
    'Result: zero-downtime deployments even with only 2 replicas',
])

pdf.sub_title('Secrets injection')
pdf.body(
    'Real secret values are never stored in the repository. The deploy job '
    'creates them with kubectl at deploy time using values from GitHub Actions Secrets:'
)
pdf.code_box([
    'kubectl create secret generic prism-db-secret \\',
    '  --from-literal=pos-db-url="jdbc:postgresql://postgres:5432/prism_pos" \\',
    '  --from-literal=inventory-db-url="jdbc:postgresql://postgres:5432/prism_inventory" \\',
    '  --from-literal=auth-db-url="jdbc:postgresql://postgres:5432/prism_auth" \\',
    '  --from-literal=db-username="prism" \\',
    '  --from-literal=db-password="$DB_PASSWORD" \\',
    '  --namespace prism --dry-run=client -o yaml | kubectl apply -f -',
    '',
    '# --dry-run=client -o yaml | kubectl apply -f -',
    '# makes it idempotent: updates the secret if it already exists',
])

# ── SECTION 6: Docker & ECR ───────────────────────────────────────────────────
pdf.add_page()
pdf.section_title('6.  Docker & ECR')

pdf.sub_title('Multi-stage Dockerfile pattern (Java services)')
pdf.code_box([
    '# Stage 1: build',
    'FROM maven:3.9-eclipse-temurin-21 AS builder',
    'WORKDIR /app',
    'COPY pom.xml .',
    'RUN mvn dependency:go-offline    <- cache dependencies as a separate layer',
    'COPY src ./src',
    'RUN mvn package -DskipTests',
    '',
    '# Stage 2: runtime',
    'FROM eclipse-temurin:21-jre-alpine',
    'RUN addgroup -S prism && adduser -S prism -G prism',
    'USER prism                        <- run as non-root',
    'COPY --from=builder /app/target/*.jar app.jar',
    'ENTRYPOINT ["java", "-jar", "app.jar"]',
    '',
    '# Result: ~200 MB image vs ~600 MB if built in a single stage',
    '# The Maven/JDK build tools are not present in the final image',
])

pdf.sub_title('ECR repository structure')
pdf.code_box([
    'Registry:  352438994873.dkr.ecr.ap-southeast-2.amazonaws.com',
    '',
    'Repositories:',
    '  mini-prism/auth-service',
    '  mini-prism/inventory-service',
    '  mini-prism/pos-service',
    '  mini-prism/frontend',
    '',
    'Tags per image:',
    '  :a1b2c3d4   <- short git SHA (immutable, used for rollback)',
    '  :latest     <- always points to the most recent build',
    '',
    'Image scanning: scan_on_push = true  (ECR scans for CVEs on every push)',
    'Shared: both prod (EC2) and demo (EKS) pull from the same repos',
])

pdf.sub_title('ECR login in CI')
pdf.code_box([
    '# GitHub Actions step',
    '- uses: aws-actions/amazon-ecr-login@v2',
    '',
    '# On the EC2 instance (via SSM)',
    'aws ecr get-login-password --region ap-southeast-2 \\',
    '  | docker login --username AWS --password-stdin $ECR_REGISTRY',
    '',
    '# On EKS (automatic via IAM role attached to node group)',
    '# AmazonEC2ContainerRegistryReadOnly policy on the node IAM role',
])

# ── SECTION 7: Key Interview Points ───────────────────────────────────────────
pdf.section_title('7.  Key DevOps Points for the Interview')
pdf.bullet([
    'WHY Terraform modules? - reusable, testable, separate concerns. The vpc module '
     'is shared between prod and demo without duplication.',
    'WHY S3 remote state? - CI and developers can run Terraform concurrently without '
     'corrupting state. State locking via DynamoDB can be added if needed.',
    'WHY SSM not SSH? - no open port 22, no key rotation headaches, audit trail in CloudWatch.',
    'WHY "needs:" in GitHub Actions? - strict sequencing prevents deploying broken code. '
     'Terraform must succeed before we build images (need ECR to exist).',
    'WHY short SHA as image tag? - every build is uniquely tagged so rollback is trivial: '
     'just deploy the previous tag. "latest" alone makes rollbacks impossible.',
    'WHY EKS only for demo? - EKS control plane costs ~$73/month. EC2 + Docker Compose '
     'achieves the same result for ~$20/month for a portfolio project.',
    'WHY in-cluster PostgreSQL for the demo? - AWS free tier allows only 1 RDS instance '
     '(used by prod). Running postgres as a pod costs nothing extra.',
    'WHY maxUnavailable=0 in K8s rolling updates? - with only 2 replicas, taking one '
     'down before the new one is ready would halve capacity. This ensures zero downtime.',
    'Trade-off acknowledged: emptyDir postgres loses data on pod restart. Acceptable for '
     'a 1-hour demo, not for production. Production would use RDS or EBS PVC.',
])

out_path = '/Users/udaydaroch/Downloads/mini-prism/mini-prism-devops.pdf'
pdf.output(out_path)
print(f'PDF written to {out_path}')
