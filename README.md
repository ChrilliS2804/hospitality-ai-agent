# Hospitality AI Voice Agent Platform

A production-ready serverless AWS solution that autonomously answers phone calls, understands customer requests using AI, and performs actions such as table reservations, room bookings, modifications, and cancellations.

## 🎯 Project Vision

Enable restaurants and hotels to provide 24/7 intelligent voice-based customer service without human intervention. The platform leverages AWS's managed services and generative AI to create a scalable, secure, and cost-effective solution that handles high call volumes while maintaining exceptional customer experiences.

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Customer (Phone Call)                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │ Amazon Connect
                      │ (IVR + CTI)
                      └──────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────┐
        │    Lambda: Call Handler Orchestrator     │
        │  - Route incoming calls                 │
        │  - Manage conversation state            │
        │  - Coordinate services                  │
        └────────────────────────────────────────┘
                    │              │              │
         ┌──────────┼──────────────┼──────────────┐
         │          │              │              │
         ▼          ▼              ▼              ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
    │Bedrock  │ │DynamoDB │ │SNS/SES  │ │EventBrdge│
    │(Claude) │ │(State)  │ │(Notify) │ │(Events)  │
    └─────────┘ └─────────┘ └─────────┘ └──────────┘
         │          │              │
         ▼          ▼              ▼
    ┌──────────────────────────────────────────┐
    │    Microservices (Python Lambda)         │
    │  ├─ Reservation Service                  │
    │  ├─ Hotel Service                        │
    │  ├─ FAQ Service                          │
    │  └─ Human Handoff Service                │
    └──────────────────────────────────────────┘
         │
         ▼
    ┌──────────────────────────────────────────┐
    │    Data Layer                            │
    │  ├─ DynamoDB (Reservations, State)       │
    │  ├─ OpenSearch Serverless (FAQ Index)    │
    │  └─ Secrets Manager (Credentials)        │
    └──────────────────────────────────────────┘
```

## 🛠️ Technology Stack

### Infrastructure
- **Terraform**: Infrastructure as Code, GitOps-ready
- **AWS**: Managed, serverless-first approach

### AWS Services
| Service | Purpose |
|---------|---------|
| Amazon Connect | Phone call ingestion, IVR, CTI integration |
| Amazon Bedrock | Multi-model LLM orchestration (Claude, GPT-4o) |
| AWS Lambda | Serverless compute for business logic |
| DynamoDB | NoSQL for reservations, conversation state |
| EventBridge | Event-driven architecture, service decoupling |
| SNS | Async notifications to external systems |
| SES | Email notifications to customers |
| CloudWatch | Logging, monitoring, alarms |
| OpenSearch Serverless | Full-text search for FAQ knowledge base |
| Secrets Manager | Secure credential storage |

### Backend
- **Python 3.12**: Type-safe, async-ready Lambda functions
- **Pydantic**: Data validation and serialization
- **FastAPI** (for local testing): API definitions
- **boto3**: AWS SDK

### Testing
- **pytest**: Unit and integration testing
- **moto**: AWS service mocking
- **pytest-asyncio**: Async test support

### CI/CD
- **GitHub Actions**: Workflows for lint, test, deploy
- **Terraform Cloud/AWS S3**: State management

### Observability
- **CloudWatch**: Centralized logging
- **X-Ray**: Distributed tracing
- **CloudWatch Metrics**: Custom business metrics
- **CloudWatch Alarms**: Threshold-based alerting

## 📂 Repository Structure

```
hospitality-ai-agent/
├── README.md                          # This file
├── docs/
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── data-flows.md
│   │   └── service-mesh.md
│   ├── decisions/                     # Architecture Decision Records
│   │   ├── ADR-001-use-terraform.md
│   │   ├── ADR-002-serverless-first.md
│   │   ├── ADR-003-use-bedrock.md
│   │   └── ADR-004-ddd-architecture.md
│   ├── requirements/
│   │   ├── functional.md
│   │   └── non-functional.md
│   └── runbooks/
│       ├── local-dev-setup.md
│       ├── deployment.md
│       └── troubleshooting.md
│
├── terraform/                         # Infrastructure as Code
│   ├── providers.tf                   # AWS provider config
│   ├── versions.tf                    # Terraform version constraints
│   ├── backend.tf                     # S3 + DynamoDB state
│   ├── variables.tf                   # Root variables
│   ├── outputs.tf                     # Root outputs
│   │
│   ├── modules/
│   │   ├── connect/                   # Amazon Connect resources
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── README.md
│   │   │
│   │   ├── bedrock/                   # Bedrock models & agents
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── README.md
│   │   │
│   │   ├── lambda/                    # Lambda functions & layers
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   ├── iam.tf
│   │   │   └── README.md
│   │   │
│   │   ├── dynamodb/                  # DynamoDB tables
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── README.md
│   │   │
│   │   ├── opensearch/                # OpenSearch Serverless
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── README.md
│   │   │
│   │   ├── monitoring/                # CloudWatch + X-Ray
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── README.md
│   │   │
│   │   ├── networking/                # VPC, Security Groups
│   │   │   ├── main.tf
│   │   │   ├── variables.tf
│   │   │   ├── outputs.tf
│   │   │   └── README.md
│   │   │
│   │   └── sns/                       # SNS topics & subscriptions
│   │       ├── main.tf
│   │       ├── variables.tf
│   │       ├── outputs.tf
│   │       └── README.md
│   │
│   ├── environments/
│   │   ├── dev/
│   │   │   ├── terraform.tfvars
│   │   │   ├── backend.tfvars
│   │   │   └── README.md
│   │   │
│   │   ├── test/
│   │   │   ├── terraform.tfvars
│   │   │   ├── backend.tfvars
│   │   │   └── README.md
│   │   │
│   │   └── prod/
│   │       ├── terraform.tfvars
│   │       ├── backend.tfvars
│   │       ├── README.md
│   │       └── guard.json              # Policy as Code
│   │
│   └── locals.tf                      # Common local values
│
├── services/                          # Microservices (Clean Architecture)
│   │
│   ├── reservation-service/           # Restaurant table reservations
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── models.py              # Domain entities
│   │   │   ├── repositories.py        # Repository interfaces
│   │   │   ├── exceptions.py          # Domain exceptions
│   │   │   └── value_objects.py       # Value objects (e.g., ReservationTime)
│   │   │
│   │   ├── application/
│   │   │   ├── __init__.py
│   │   │   ├── dtos.py                # Data Transfer Objects
│   │   │   ├── services.py            # Application services
│   │   │   ├── use_cases.py           # Use cases (commands)
│   │   │   └── events.py              # Domain events
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── dynamodb/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── client.py          # DynamoDB client wrapper
│   │   │   │   ├── repository.py      # Repository implementation
│   │   │   │   └── serializers.py     # DynamoDB serialization
│   │   │   │
│   │   │   ├── bedrock/
│   │   │   │   ├── __init__.py
│   │   │   │   └── client.py          # Bedrock LLM client
│   │   │   │
│   │   │   ├── sns/
│   │   │   │   ├── __init__.py
│   │   │   │   └── publisher.py       # SNS event publisher
│   │   │   │
│   │   │   └── config.py              # Infrastructure config
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── handlers.py            # Lambda handler entry points
│   │   │   ├── middleware.py          # Logging, tracing, auth
│   │   │   └── schemas.py             # Request/response schemas
│   │   │
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   ├── unit/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_domain.py
│   │   │   │   ├── test_services.py
│   │   │   │   └── test_repositories.py
│   │   │   │
│   │   │   ├── integration/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── test_dynamodb.py
│   │   │   │   ├── test_bedrock.py
│   │   │   │   └── test_sns.py
│   │   │   │
│   │   │   ├── fixtures/
│   │   │   │   ├── __init__.py
│   │   │   │   └── factories.py       # Test data factories
│   │   │   │
│   │   │   └── conftest.py            # Pytest configuration
│   │   │
│   │   ├── lambda_layer/              # Shared dependencies layer
│   │   │   └── python/
│   │   │       └── requirements.txt
│   │   │
│   │   ├── lambda/
│   │   │   ├── __init__.py
│   │   │   └── app.py                 # Lambda handler
│   │   │
│   │   ├── pyproject.toml
│   │   ├── requirements.txt
│   │   ├── requirements-dev.txt
│   │   └── README.md
│   │
│   ├── hotel-service/                 # Hotel room reservations
│   │   └── [Same structure as reservation-service]
│   │
│   ├── faq-service/                   # FAQ & knowledge base
│   │   └── [Same structure as reservation-service]
│   │
│   └── shared/                        # Shared utilities & types
│       ├── __init__.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── events.py              # Base domain events
│       │   ├── exceptions.py          # Shared exceptions
│       │   └── types.py               # Shared types
│       │
│       ├── infrastructure/
│       │   ├── __init__.py
│       │   ├── aws/
│       │   │   ├── __init__.py
│       │   │   ├── clients.py         # AWS SDK wrappers
│       │   │   └── config.py          # AWS configuration
│       │   │
│       │   ├── logging/
│       │   │   ├── __init__.py
│       │   │   └── logger.py          # Structured logging
│       │   │
│       │   ├── tracing/
│       │   │   ├── __init__.py
│       │   │   └── tracer.py          # X-Ray tracing
│       │   │
│       │   └── secrets/
│       │       ├── __init__.py
│       │       └── manager.py         # Secrets Manager wrapper
│       │
│       ├── application/
│       │   ├── __init__.py
│       │   ├── middleware.py          # Cross-cutting concerns
│       │   └── validators.py          # Input validation
│       │
│       └── requirements.txt
│
├── tests/                             # Integration & E2E tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_call_flow.py          # End-to-end call flows
│   │
│   └── performance/
│       ├── __init__.py
│       └── test_load.py               # Load testing
│
├── .github/
│   ├── workflows/
│   │   ├── terraform.yml              # Terraform lint, validate, plan
│   │   ├── python.yml                 # Python lint, test, coverage
│   │   ├── deploy-dev.yml
│   │   ├── deploy-test.yml
│   │   ├── deploy-prod.yml
│   │   └── security-scanning.yml
│   │
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE/
│       ├── bug.md
│       ├── feature.md
│       └── adr.md
│
├── .gitignore
├── .pre-commit-config.yaml
├── Makefile                           # Development convenience commands
├── pyproject.toml                     # Python project configuration
└── pytest.ini                         # Pytest configuration
```

## 🚀 Development Workflow

### Local Development

1. **Setup environment**:
   ```bash
   make setup
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

2. **Run tests**:
   ```bash
   make test              # Run all tests
   make test-unit         # Unit tests only
   make test-integration  # Integration tests
   make coverage          # Generate coverage report
   ```

3. **Lint and format**:
   ```bash
   make lint              # Run linters
   make format            # Auto-format code
   ```

4. **Local infrastructure** (using LocalStack or moto):
   ```bash
   make local-infra       # Start local AWS services
   ```

### Git Workflow

1. Create feature branch: `git checkout -b feat/your-feature`
2. Make changes and commit with conventional commits
3. Push and create a Pull Request
4. GitHub Actions runs: linting, tests, Terraform validation
5. After approval, merge to main
6. CD pipeline deploys to staging/prod

## 📦 Deployment Overview

### Deployment Stages

```
main branch
    │
    ├──► Push to GitHub
    │
    ├──► GitHub Actions: Lint, Test, Validate
    │
    ├──► [Auto or Manual] Deploy to Dev
    │    └──► Run integration tests
    │    └──► Validate metrics
    │
    ├──► [Manual] Deploy to Test
    │    └──► Run E2E tests
    │    └──► Load testing
    │
    └──► [Manual] Deploy to Prod
         └──► Blue-green deployment
         └──► Canary rollout
         └──► Production validation
```

### Deployment Commands

```bash
# Terraform
make tf-plan env=dev
make tf-apply env=dev
make tf-destroy env=dev

# Lambda functions
make deploy-functions env=prod
make deploy-layers env=prod
```

## 📚 Key Documentation

- **[Architecture Decisions](docs/decisions/)**: ADRs for all major technical choices
- **[Functional Requirements](docs/requirements/functional.md)**: Use cases and features
- **[Non-Functional Requirements](docs/requirements/non-functional.md)**: Performance, security, scalability
- **[Local Development Setup](docs/runbooks/local-dev-setup.md)**: Getting started
- **[Deployment Guide](docs/runbooks/deployment.md)**: Production deployments
- **[Troubleshooting](docs/runbooks/troubleshooting.md)**: Common issues and fixes

## 🔐 Security

- ✅ Secrets Manager for all credentials
- ✅ IAM least-privilege policies
- ✅ VPC endpoints for private communication
- ✅ CloudTrail for audit logging
- ✅ Encryption at rest (DynamoDB, S3)
- ✅ Encryption in transit (TLS)
- ✅ API request signing (AWS SigV4)

## 🔍 Observability

- **Logs**: CloudWatch Logs with structured JSON
- **Traces**: X-Ray for distributed tracing
- **Metrics**: CloudWatch custom metrics
- **Alarms**: Threshold-based alerts to SNS

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the [development workflow](#development-workflow)
4. Ensure all tests pass and coverage > 80%
5. Submit a PR with clear description

## 📄 License

Proprietary - For authorized use only

## 👥 Support

For questions or issues, please:
1. Check the [troubleshooting guide](docs/runbooks/troubleshooting.md)
2. Open an issue with details
3. Contact the platform team

---

**Last Updated**: 2026-05-31  
**Maintained By**: AWS Cloud Architecture Team
