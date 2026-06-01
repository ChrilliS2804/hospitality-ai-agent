# Local Development Setup

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.12+ | [python.org](https://python.org) |
| Terraform | 1.7+ | [terraform.io](https://developer.hashicorp.com/terraform/install) |
| AWS CLI | 2.x | [aws.amazon.com/cli](https://aws.amazon.com/cli/) |
| Git | any | system package manager |

---

## 1. Clone and configure

```bash
git clone <repo-url>
cd hospitality-ai-agent
```

---

## 2. Python environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows CMD)
.venv\Scripts\activate.bat

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source .venv/bin/activate

# Install all dev dependencies
pip install -r requirements-dev.txt

# Install the shared library in editable mode
pip install -e services/shared

# Install pre-commit hooks
pre-commit install --install-hooks
```

---

## 3. Run the tests

```bash
# Unit tests only (no AWS needed)
pytest -m unit

# Unit tests with coverage
pytest -m unit --cov=services --cov-report=term-missing

# Integration tests (uses moto — no real AWS needed)
pytest -m integration

# All tests
pytest
```

Expected output: all tests pass, coverage > 80%.

---

## 4. Lint and format

```bash
# Check for lint errors
ruff check services tests

# Auto-fix lint errors
ruff check --fix services tests

# Format code
ruff format services tests

# Type check
mypy services
```

---

## 5. Bootstrap AWS infrastructure (first time only)

> **Requires**: AWS credentials with admin access to the target account.

```bash
# Configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, region (eu-central-1), output (json)

# Bootstrap Terraform remote state (run once per account)
cd terraform/bootstrap
terraform init
terraform apply -var="aws_account_id=$(aws sts get-caller-identity --query Account --output text)"
cd ../..
```

---

## 6. Deploy dev environment

```bash
# Copy and fill in the example config files
cp terraform/environments/dev/backend.tfvars.example terraform/environments/dev/backend.tfvars
cp terraform/environments/dev/terraform.tfvars.example terraform/environments/dev/terraform.tfvars

# Edit both files with your AWS account ID and region
# (backend.tfvars: bucket name; terraform.tfvars: aws_account_id)

# Initialise Terraform
make tf-init env=dev

# Preview changes
make tf-plan env=dev

# Apply infrastructure
make tf-apply env=dev
```

---

## 7. Build and deploy Lambda functions

```bash
# Build the shared layer zip
make build-layer

# Package and upload all Lambda functions
make deploy-functions env=dev
```

---

## 8. Verify the deployment

```bash
# Get the call-handler function name from Terraform output
FUNCTION=$(cd terraform/environments/dev && terraform output -raw call_handler_function_name)

# Run the smoke test
FUNCTION_NAME=$FUNCTION python scripts/smoke_test_call_handler.py
```

Expected: `✓ Smoke test passed`

---

## 9. Useful Make targets

```bash
make help              # List all available targets
make test              # Run all tests
make test-unit         # Unit tests only
make test-integration  # Integration tests (moto)
make coverage          # Coverage report in htmlcov/
make lint              # Ruff lint check
make format            # Ruff auto-format
make typecheck         # Mypy type check
make tf-plan env=dev   # Terraform plan
make tf-apply env=dev  # Terraform apply
make clean             # Remove build artifacts
```

---

## 10. Environment variables reference

| Variable | Default | Description |
|---|---|---|
| `DYNAMODB_TABLE_NAME` | `hospitality-ai-dev-table` | DynamoDB table name |
| `AWS_REGION` | `eu-central-1` | AWS region |
| `LOG_LEVEL` | `DEBUG` (dev) / `INFO` (prod) | Log verbosity |
| `XRAY_ENABLED` | `true` | Enable X-Ray tracing |
| `SESSION_TTL_SECONDS` | `86400` | Session TTL (24h) |

These are set automatically by Terraform in the Lambda environment. For local testing, the `conftest.py` files set safe defaults.

---

## Troubleshooting

**`ModuleNotFoundError: hospitality_shared`**
→ Run `pip install -e services/shared` from the repo root.

**`botocore.exceptions.NoCredentialsError` in tests**
→ The `conftest.py` sets fake credentials. Make sure you're running pytest from the repo root, not from inside a service directory.

**`terraform init` fails with S3 bucket not found**
→ Run the bootstrap step first (`terraform/bootstrap/main.tf`).

**`ruff: command not found`**
→ Activate your virtual environment: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux).
