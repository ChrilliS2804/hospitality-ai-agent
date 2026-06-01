# System Architecture
# Hospitality AI Voice Agent Platform

**Version**: 1.0  
**Status**: Draft for Review  
**Date**: 2026-05-31  
**Author**: Cloud Architecture Team

---

## Table of Contents

1. [System Context](#1-system-context)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Call Flow — Detailed Sequence](#3-call-flow--detailed-sequence)
4. [AWS Service Mapping](#4-aws-service-mapping)
5. [Microservice Architecture](#5-microservice-architecture)
6. [Data Architecture](#6-data-architecture)
7. [Security Architecture](#7-security-architecture)
8. [Observability Architecture](#8-observability-architecture)
9. [CI/CD Architecture](#9-cicd-architecture)
10. [Terraform Module Structure](#10-terraform-module-structure)
11. [Repository Structure](#11-repository-structure)
12. [Architecture Decisions and Trade-offs](#12-architecture-decisions-and-trade-offs)

---

## 1. System Context

The platform sits between the public telephone network and the hospitality business's backend data. It has no dependency on any existing POS or PMS system for MVP.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL ACTORS                                │
│                                                                         │
│   [Restaurant Guest]          [Hotel Guest]          [Restaurant Staff] │
│   (Phone Caller)              (Phone Caller)         (Human Agent)      │
└──────────┬────────────────────────┬──────────────────────┬─────────────┘
           │ PSTN / VoIP            │ PSTN / VoIP          │ Amazon Connect
           ▼                        ▼                      │ Agent Desktop
┌──────────────────────────────────────────────────────────▼─────────────┐
│                    HOSPITALITY AI VOICE AGENT PLATFORM                  │
│                           (AWS — Serverless)                            │
│                                                                         │
│  ┌──────────────┐   ┌──────────────────┐   ┌──────────────────────┐   │
│  │Amazon Connect│   │  AI Conversation  │   │  Reservation Service │   │
│  │  (Telephony) │──▶│     Engine        │──▶│  (Domain Logic)      │   │
│  └──────────────┘   │  (Lambda+Bedrock) │   └──────────────────────┘   │
│                     └──────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────┘
           │                                          │
           ▼                                          ▼
   [SMS / Email to Guest]                    [DynamoDB — Reservations]
   (SNS / SES)
```

---

## 2. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            VOICE CHANNEL LAYER                               │
│                                                                              │
│   Customer ──PSTN──▶  Amazon Connect  ──▶  Contact Flow  ──▶  Lambda Hook   │
└──────────────────────────────────────────────────────────────────────────────┘
                                                                    │
                                                                    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATION LAYER                                  │
│                                                                              │
│              ┌─────────────────────────────────────────┐                    │
│              │     Call Handler Lambda (Orchestrator)   │                    │
│              │  - Manages conversation state            │                    │
│              │  - Routes to appropriate service         │                    │
│              │  - Calls Bedrock for NLU                 │                    │
│              │  - Returns SSML/text to Connect          │                    │
│              └─────────────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────────────────────────┘
          │                    │                    │                │
          ▼                    ▼                    ▼                ▼
┌──────────────┐  ┌────────────────────┐  ┌──────────────┐  ┌──────────────┐
│   Amazon     │  │  Reservation       │  │  FAQ         │  │  Human       │
│   Bedrock    │  │  Service Lambda    │  │  Service     │  │  Handoff     │
│  (Claude)    │  │  (Domain Logic)    │  │  Lambda      │  │  Lambda      │
└──────────────┘  └────────────────────┘  └──────────────┘  └──────────────┘
                           │                     │
                           ▼                     ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
│                                                                              │
│  ┌─────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐   │
│  │    DynamoDB      │  │  OpenSearch          │  │   Secrets Manager    │   │
│  │  - Reservations  │  │  Serverless          │  │   - API Keys         │   │
│  │  - Sessions      │  │  (FAQ Index)         │  │   - Credentials      │   │
│  │  - Tenants       │  │                      │  │                      │   │
│  └─────────────────┘  └──────────────────────┘  └──────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
          │                                                │
          ▼                                                ▼
┌──────────────────────┐                    ┌─────────────────────────────────┐
│  EVENT / MESSAGING   │                    │        OBSERVABILITY             │
│                      │                    │                                 │
│  EventBridge         │                    │  CloudWatch Logs                │
│  SNS (SMS)           │                    │  CloudWatch Metrics             │
│  SES (Email)         │                    │  CloudWatch Alarms              │
└──────────────────────┘                    │  X-Ray Traces                   │
                                            └─────────────────────────────────┘
```

---

## 3. Call Flow — Detailed Sequence

### Happy Path: Make a Reservation

```
Guest          Connect        Contact Flow    Call Handler    Bedrock       Reservation Svc   DynamoDB   SNS/SES
  │               │               │               │              │               │               │          │
  │──calls──────▶│               │               │              │               │               │          │
  │               │──triggers────▶│               │              │               │               │          │
  │               │               │──invokes─────▶│              │               │               │          │
  │               │               │               │──NLU─────────▶│              │               │          │
  │               │               │               │◀─intent──────│               │               │          │
  │               │               │               │  (MAKE_RESERVATION)          │               │          │
  │               │               │               │──collect slots (multi-turn)──────────────────────────── │
  │               │               │               │  (date, time, party, name, contact)          │          │
  │               │               │               │──check availability──────────▶│               │          │
  │               │               │               │                               │──query───────▶│          │
  │               │               │               │                               │◀─available────│          │
  │               │               │               │◀─available────────────────────│               │          │
  │               │               │               │──confirm with guest (voice)───────────────────────────  │
  │               │               │               │──create reservation───────────▶│               │          │
  │               │               │               │                               │──write────────▶│          │
  │               │               │               │                               │◀─confirmed─────│          │
  │               │               │               │◀─reservation_id───────────────│               │          │
  │               │               │               │──publish ReservationCreated event─────────────────────▶ │
  │               │               │               │                               │               │──SMS────▶│
  │               │               │               │                               │               │──Email──▶│
  │◀─confirmation─│◀─SSML response─│◀─response─────│              │               │               │          │
  │  (voice)      │               │               │              │               │               │          │
```

### Human Handoff Flow

```
Guest          Connect        Call Handler    Bedrock       Handoff Svc    Staff
  │               │               │              │               │            │
  │──"speak to    │               │              │               │            │
  │   someone"───▶│──invokes─────▶│              │               │            │
  │               │               │──NLU─────────▶│              │            │
  │               │               │◀─HUMAN_HANDOFF│              │            │
  │               │               │──invoke──────────────────────▶│            │
  │               │               │               │               │──check agent available
  │               │               │               │               │──generate call summary
  │               │               │               │               │──notify staff via SNS──▶│
  │               │◀─transfer─────│◀─transfer─────│◀──────────────│            │
  │◀─"connecting" │               │               │               │            │
  │──────────────────────────────────────────────────────────────────────────▶│
  │  (live call)  │               │               │               │            │
```

---

## 4. AWS Service Mapping

| AWS Service | Role | Configuration Notes |
|---|---|---|
| **Amazon Connect** | Telephony — inbound call ingestion, IVR, call transfer | One instance per environment; Contact Flows managed via Terraform |
| **AWS Lambda** | Serverless compute for all business logic | Python 3.12; Provisioned Concurrency on Call Handler |
| **Amazon Bedrock (Claude)** | NLU, intent classification, slot filling, summarization | claude-3-5-sonnet; model abstracted for easy swap |
| **Amazon Bedrock Knowledge Bases** | FAQ retrieval with semantic search | Backed by OpenSearch Serverless; S3 data source |
| **Amazon DynamoDB** | Primary data store — reservations, sessions, tenants | On-demand capacity; single-table design per domain |
| **Amazon OpenSearch Serverless** | Vector search for FAQ knowledge base | Managed by Bedrock Knowledge Bases |
| **Amazon S3** | FAQ document storage; Terraform state; Lambda deployment packages | Versioning enabled; server-side encryption |
| **Amazon SNS** | SMS notifications to guests; internal event fan-out | Topic per notification type |
| **Amazon SES** | Email notifications to guests | Domain verification required per tenant |
| **Amazon EventBridge** | Domain event bus — decouples services | Custom event bus per environment |
| **AWS Secrets Manager** | Credentials, API keys, connection strings | Rotation enabled where applicable |
| **AWS KMS** | Encryption keys for DynamoDB, S3, CloudWatch Logs | Customer-managed keys in prod |
| **AWS IAM** | Identity and access control | Least-privilege per Lambda function |
| **Amazon CloudWatch** | Logs, metrics, alarms, dashboards | Structured JSON logs; custom namespace |
| **AWS X-Ray** | Distributed tracing across Lambda and AWS SDK calls | Active tracing on all Lambdas |
| **AWS CloudTrail** | API audit logging | Enabled at account level |
| **Amazon VPC** | Network isolation for sensitive resources | VPC endpoints for DynamoDB, Secrets Manager, Bedrock |
| **GitHub Actions** | CI/CD pipelines | Lint, test, Terraform plan/apply |

---

## 5. Microservice Architecture

Each service is an independent Lambda function following Clean Architecture with DDD.

### Service Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│                    services/                                     │
│                                                                  │
│  ┌──────────────────────┐   ┌──────────────────────────────┐   │
│  │  call-handler/        │   │  reservation-service/         │   │
│  │  (Orchestrator)       │   │  (Domain: Reservations)       │   │
│  │                       │   │                               │   │
│  │  Responsibilities:    │   │  Responsibilities:            │   │
│  │  - Receive Connect    │   │  - Create reservation         │   │
│  │    invocation         │   │  - Cancel reservation         │   │
│  │  - Load session state │   │  - Modify reservation         │   │
│  │  - Call Bedrock NLU   │   │  - Check availability         │   │
│  │  - Route to service   │   │  - Retrieve reservation       │   │
│  │  - Return SSML        │   │                               │   │
│  └──────────────────────┘   └──────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────┐   ┌──────────────────────────────┐   │
│  │  faq-service/         │   │  notification-service/        │   │
│  │  (Domain: Knowledge)  │   │  (Domain: Notifications)      │   │
│  │                       │   │                               │   │
│  │  Responsibilities:    │   │  Responsibilities:            │   │
│  │  - Query Bedrock KB   │   │  - Send SMS via SNS           │   │
│  │  - Return answers     │   │  - Send email via SES         │   │
│  │  - Trigger handoff    │   │  - Triggered by EventBridge   │   │
│  │    on no answer       │   │                               │   │
│  └──────────────────────┘   └──────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────┐   ┌──────────────────────────────┐   │
│  │  handoff-service/     │   │  shared/                      │   │
│  │  (Domain: Escalation) │   │  (Cross-cutting concerns)     │   │
│  │                       │   │                               │   │
│  │  Responsibilities:    │   │  Contents:                    │   │
│  │  - Check agent avail  │   │  - AWS client wrappers        │   │
│  │  - Transfer call      │   │  - Structured logging         │   │
│  │  - Generate summary   │   │  - X-Ray tracing              │   │
│  │  - Callback request   │   │  - Base domain types          │   │
│  └──────────────────────┘   │  - Input validation           │   │
│                              └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Clean Architecture Layers (per service)

```
api/           ← Lambda handler entry point, request/response schemas
application/   ← Use cases, DTOs, application services, domain events
domain/        ← Entities, value objects, repository interfaces, exceptions
infrastructure/← DynamoDB, Bedrock, SNS clients; repository implementations
```

### Inter-Service Communication

| Pattern | Used For |
|---|---|
| **Synchronous Lambda invoke** | Call Handler → Reservation Service, FAQ Service, Handoff Service |
| **EventBridge (async)** | Reservation events → Notification Service |
| **DynamoDB direct** | Session state read/write within Call Handler |
| **Bedrock API** | NLU, summarization (called from Call Handler) |

---

## 6. Data Architecture

### DynamoDB Table Design

**Single global table**: `hospitality-{environment}`

All entities (reservations, sessions, tenants) live in one table using composite key patterns. Entity type is encoded in the key prefix. GSIs support all required access patterns across entity types.

#### Key Schema

| Key | Type | Description |
|---|---|---|
| `PK` | String (Partition Key) | Entity-type-prefixed partition key |
| `SK` | String (Sort Key) | Entity-type-prefixed sort key |
| `GSI1PK` | String | GSI 1 partition key |
| `GSI1SK` | String | GSI 1 sort key |
| `GSI2PK` | String | GSI 2 partition key |
| `GSI2SK` | String | GSI 2 sort key |

#### Entity: Reservation

| Attribute | Value / Type | Notes |
|---|---|---|
| `PK` | `TENANT#{tenant_id}` | |
| `SK` | `RESERVATION#{reservation_id}` | |
| `GSI1PK` | `TENANT#{tenant_id}#DATE#{date}` | Availability check by date |
| `GSI1SK` | `TIME#{time}` | |
| `GSI2PK` | `TENANT#{tenant_id}#PHONE#{phone}` | Lookup by caller phone |
| `GSI2SK` | `DATE#{date}` | |
| `entity_type` | `RESERVATION` | Discriminator |
| `status` | String | PENDING / CONFIRMED / MODIFIED / CANCELLED / COMPLETED |
| `guest_name` | String | |
| `guest_phone` | String | |
| `guest_email` | String | |
| `party_size` | Number | |
| `date` | String | ISO 8601 date |
| `time` | String | HH:MM |
| `reference_number` | String | Human-readable, e.g. RES-20260531-001 |
| `notes` | String | Optional |
| `created_at` | String | ISO 8601 datetime |
| `updated_at` | String | ISO 8601 datetime |

**Access Patterns**:
- Get reservation by ID → `PK + SK`
- List reservations by date (availability check) → `GSI1` query on `TENANT#{id}#DATE#{date}`
- Find reservation by caller phone + date → `GSI2`

#### Entity: ConversationSession

| Attribute | Value / Type | Notes |
|---|---|---|
| `PK` | `SESSION#{session_id}` | Connect Contact ID |
| `SK` | `SESSION#{session_id}` | |
| `GSI1PK` | `TENANT#{tenant_id}#SESSION` | List sessions by tenant |
| `GSI1SK` | `CREATED#{created_at}` | |
| `entity_type` | `SESSION` | |
| `tenant_id` | String | |
| `caller_phone` | String | |
| `intent` | String | |
| `slots` | Map | Collected slot values |
| `turn_history` | List | List of `{role, content, timestamp}` |
| `status` | String | ACTIVE / COMPLETED / TRANSFERRED / ABANDONED |
| `reservation_id` | String | Optional |
| `summary` | String | Optional, generated at end of call |
| `created_at` | String | |
| `updated_at` | String | |
| `ttl` | Number | Unix epoch, 24h from creation — auto-deleted by DynamoDB |

#### Entity: Tenant

| Attribute | Value / Type | Notes |
|---|---|---|
| `PK` | `TENANT#{tenant_id}` | |
| `SK` | `CONFIG` | |
| `entity_type` | `TENANT` | |
| `business_name` | String | |
| `business_type` | String | RESTAURANT / HOTEL |
| `phone_number` | String | |
| `operating_hours` | List | `[{day, open, close}]` per day of week |
| `notification_config` | Map | `{sms_enabled, email_enabled, from_email}` |
| `connect_instance_id` | String | |
| `active` | Boolean | |

### S3 Buckets

| Bucket | Purpose |
|---|---|
| `{env}-hospitality-faq-docs` | FAQ source documents for Bedrock Knowledge Base |
| `{env}-hospitality-tf-state` | Terraform remote state |
| `{env}-hospitality-lambda-packages` | Lambda deployment packages |
| `{env}-hospitality-call-recordings` | Optional call recordings (if enabled) |

---

## 7. Security Architecture

### Principles

- **Least Privilege**: Every Lambda has its own IAM role with only the permissions it needs
- **Zero Trust**: No service trusts another implicitly; all calls authenticated via IAM
- **Encryption Everywhere**: KMS encryption at rest; TLS in transit
- **No Secrets in Code**: All credentials via Secrets Manager or environment variables from SSM
- **Audit Everything**: CloudTrail captures all API calls; CloudWatch logs all Lambda invocations

### IAM Role Design

```
call-handler-role
  ├── dynamodb:GetItem, PutItem, UpdateItem  (sessions table only)
  ├── bedrock:InvokeModel
  ├── lambda:InvokeFunction  (reservation-service, faq-service, handoff-service)
  ├── xray:PutTraceSegments
  └── logs:CreateLogGroup, PutLogEvents

reservation-service-role
  ├── dynamodb:GetItem, PutItem, UpdateItem, Query  (reservations table only)
  ├── events:PutEvents  (EventBridge — reservation events)
  ├── xray:PutTraceSegments
  └── logs:CreateLogGroup, PutLogEvents

notification-service-role
  ├── sns:Publish
  ├── ses:SendEmail
  ├── secretsmanager:GetSecretValue  (SES credentials)
  ├── xray:PutTraceSegments
  └── logs:CreateLogGroup, PutLogEvents

faq-service-role
  ├── bedrock:RetrieveAndGenerate  (Knowledge Base)
  ├── xray:PutTraceSegments
  └── logs:CreateLogGroup, PutLogEvents
```

### Network Architecture

```
VPC (optional for MVP, recommended for prod)
├── Private Subnets
│   └── Lambda functions (VPC-attached)
├── VPC Endpoints
│   ├── com.amazonaws.{region}.dynamodb
│   ├── com.amazonaws.{region}.secretsmanager
│   ├── com.amazonaws.{region}.bedrock-runtime
│   └── com.amazonaws.{region}.execute-api
└── No public subnets required (Lambda + managed services)
```

### Data Protection

| Data Type | Protection |
|---|---|
| Guest PII (name, phone, email) | Encrypted at rest (DynamoDB KMS); masked in logs |
| Reservation data | DynamoDB KMS encryption |
| Conversation transcripts | DynamoDB KMS; TTL 24h for sessions |
| API credentials | Secrets Manager; never in environment variables |
| Terraform state | S3 server-side encryption; DynamoDB lock table |

---

## 8. Observability Architecture

### Logging Strategy

All Lambda functions emit structured JSON logs to CloudWatch:

```json
{
  "timestamp": "2026-05-31T10:00:00Z",
  "level": "INFO",
  "service": "call-handler",
  "trace_id": "1-abc123",
  "session_id": "contact-xyz",
  "tenant_id": "restaurant-001",
  "intent": "MAKE_RESERVATION",
  "turn": 3,
  "message": "Slot collection complete, checking availability",
  "duration_ms": 245
}
```

PII fields (phone, name, email) are masked: `phone: "***-***-1234"`

### Metrics

Custom CloudWatch namespace: `HospitalityAI/{environment}`

| Metric | Unit | Description |
|---|---|---|
| `CallsReceived` | Count | Total inbound calls |
| `CallsResolved` | Count | Calls resolved without handoff |
| `CallsHandedOff` | Count | Calls transferred to human |
| `ReservationsCreated` | Count | Successful bookings |
| `ReservationsCancelled` | Count | Cancellations processed |
| `IntentClassificationLatency` | Milliseconds | Bedrock NLU latency |
| `ReservationWriteLatency` | Milliseconds | DynamoDB write latency |
| `NotificationDeliveryLatency` | Milliseconds | SNS/SES delivery time |
| `ColdStartCount` | Count | Lambda cold starts |

### Alarms

| Alarm | Threshold | Action |
|---|---|---|
| High error rate | Lambda errors > 1% over 5 min | SNS → PagerDuty / email |
| High latency | P95 duration > 10s | SNS alert |
| DynamoDB throttling | ThrottledRequests > 0 | SNS alert |
| Handoff rate spike | HandoffRate > 30% over 15 min | SNS alert (possible AI issue) |
| Lambda concurrency limit | ConcurrentExecutions > 80% of limit | SNS alert |

### X-Ray Tracing

Every call produces a complete trace:
`Connect → Call Handler → Bedrock → Reservation Service → DynamoDB → EventBridge → Notification Service`

Trace annotations: `tenant_id`, `session_id`, `intent`, `reservation_id`

---

## 9. CI/CD Architecture

```
Developer
    │
    ├── git push (feature branch)
    │
    ▼
GitHub Pull Request
    │
    ├── [Trigger] python.yml
    │   ├── ruff lint
    │   ├── mypy type check
    │   ├── pytest unit tests
    │   └── coverage report (must be > 80%)
    │
    ├── [Trigger] terraform.yml
    │   ├── terraform fmt check
    │   ├── terraform validate
    │   ├── terraform plan (dev)
    │   └── checkov security scan
    │
    └── [Trigger] security-scanning.yml
        ├── bandit (Python security)
        └── trivy (dependency scan)

Merge to main
    │
    ├── [Auto] deploy-dev.yml
    │   ├── terraform apply (dev)
    │   ├── deploy Lambda packages
    │   └── run integration tests
    │
    ├── [Manual approval] deploy-test.yml
    │   ├── terraform apply (test)
    │   ├── deploy Lambda packages
    │   ├── run E2E tests
    │   └── run load tests
    │
    └── [Manual approval] deploy-prod.yml
        ├── terraform apply (prod)
        ├── deploy Lambda packages (blue/green via aliases)
        ├── canary traffic shift (10% → 50% → 100%)
        └── production smoke tests
```

### Lambda Deployment Strategy

- Lambda versions and aliases used for blue/green deployments
- `LIVE` alias points to current production version
- Traffic shifting via weighted aliases for canary rollout
- Automatic rollback on CloudWatch alarm breach (CodeDeploy Lambda hooks)

---

## 10. Terraform Module Structure

```
terraform/
├── providers.tf          # AWS provider, required_providers
├── versions.tf           # Terraform and provider version constraints
├── backend.tf            # S3 + DynamoDB remote state
├── variables.tf          # Root input variables
├── outputs.tf            # Root outputs
├── locals.tf             # Common computed values, tags
│
├── modules/
│   ├── connect/          # Amazon Connect instance, phone numbers, contact flows
│   │   ├── main.tf
│   │   ├── contact_flow.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   │
│   ├── lambda/           # Lambda functions, layers, IAM roles, log groups
│   │   ├── main.tf
│   │   ├── iam.tf
│   │   ├── layers.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   │
│   ├── bedrock/          # Bedrock Knowledge Base, data source, S3 bucket
│   │   ├── main.tf
│   │   ├── knowledge_base.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   │
│   ├── dynamodb/         # Single global DynamoDB table, GSIs, KMS key, backups, TTL
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   │
│   ├── messaging/        # SNS topics, SES config, EventBridge bus and rules
│   │   ├── main.tf
│   │   ├── eventbridge.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   │
│   ├── monitoring/       # CloudWatch dashboards, alarms, log metric filters
│   │   ├── main.tf
│   │   ├── alarms.tf
│   │   ├── dashboards.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   │
│   ├── networking/       # VPC, subnets, security groups, VPC endpoints
│   │   ├── main.tf
│   │   ├── endpoints.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── README.md
│   │
│   └── security/         # KMS keys, Secrets Manager secrets, IAM policies
│       ├── main.tf
│       ├── kms.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── README.md
│
└── environments/
    ├── dev/
    │   ├── main.tf       # Module composition for dev
    │   ├── terraform.tfvars
    │   └── backend.tfvars
    ├── test/
    │   ├── main.tf
    │   ├── terraform.tfvars
    │   └── backend.tfvars
    └── prod/
        ├── main.tf
        ├── terraform.tfvars
        ├── backend.tfvars
        └── guard.json    # AWS CloudFormation Guard policies
```

---

## 11. Repository Structure

```
hospitality-ai-agent/
│
├── README.md
├── Makefile                        # Dev convenience: test, lint, deploy, tf-plan
├── pyproject.toml                  # Root Python config (ruff, mypy, pytest)
├── pytest.ini
├── .pre-commit-config.yaml         # ruff, mypy, terraform fmt, conventional commits
├── .gitignore
│
├── docs/
│   ├── PRD.md                      # Product Requirements Document
│   ├── architecture/
│   │   ├── system-architecture.md  # This document
│   │   ├── data-flows.md
│   │   └── adr/                    # Architecture Decision Records
│   │       ├── ADR-001-use-terraform.md
│   │       ├── ADR-002-serverless-first.md
│   │       ├── ADR-003-use-bedrock.md
│   │       └── ADR-004-ddd-architecture.md
│   ├── requirements/
│   │   ├── functional.md
│   │   └── non-functional.md
│   └── runbooks/
│       ├── local-dev-setup.md
│       ├── deployment.md
│       └── troubleshooting.md
│
├── terraform/                      # All infrastructure (see section 10)
│
├── services/
│   ├── shared/                     # Shared library (Lambda layer)
│   │   ├── hospitality_shared/
│   │   │   ├── __init__.py
│   │   │   ├── domain/             # Base types, events, exceptions
│   │   │   ├── infrastructure/     # AWS clients, logging, tracing, secrets
│   │   │   └── application/        # Middleware, validators
│   │   ├── pyproject.toml
│   │   └── requirements.txt
│   │
│   ├── call-handler/               # Orchestrator Lambda
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── api/                    # Lambda handler entry point
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── requirements.txt
│   │
│   ├── reservation-service/        # Reservation domain Lambda
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── api/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── requirements.txt
│   │
│   ├── faq-service/                # FAQ / Knowledge Base Lambda
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── api/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── requirements.txt
│   │
│   ├── notification-service/       # SNS/SES notification Lambda
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   ├── api/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── requirements.txt
│   │
│   └── handoff-service/            # Human handoff Lambda
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       ├── api/
│       ├── tests/
│       ├── pyproject.toml
│       └── requirements.txt
│
├── tests/                          # Cross-service integration and E2E tests
│   ├── integration/
│   └── e2e/
│
└── .github/
    ├── workflows/
    │   ├── python.yml
    │   ├── terraform.yml
    │   ├── deploy-dev.yml
    │   ├── deploy-test.yml
    │   ├── deploy-prod.yml
    │   └── security-scanning.yml
    └── PULL_REQUEST_TEMPLATE.md
```

---

## 12. Architecture Decisions and Trade-offs

### Decision: Synchronous Lambda invocation for Call Handler → Services

**Rationale**: Amazon Connect requires a synchronous response within a timeout window (~8 seconds). The Call Handler must receive service responses before returning SSML to Connect. Async patterns (EventBridge) are used only for post-call events (notifications, analytics) where the caller does not need to wait.

**Trade-off**: Tighter coupling between Call Handler and downstream services. Mitigated by clean interfaces and independent deployability.

### Decision: Single global DynamoDB table

**Rationale**: One table for all entities (reservations, sessions, tenants) using composite key patterns. Simplifies infrastructure, reduces cost, and aligns with DynamoDB single-table design best practices. All items are partitioned by entity type and tenant ID to maintain logical isolation.

**Trade-off**: More complex query patterns and key design upfront. Access patterns must be defined before table creation. Mitigated by thorough key design documented in the data architecture section. Can be split into per-domain tables in a future phase if operational complexity warrants it.

### Decision: Bedrock Knowledge Bases for FAQ (not custom RAG)

**Rationale**: Bedrock Knowledge Bases provides managed vector indexing, embedding, and retrieval without building a custom RAG pipeline. Reduces operational complexity significantly.

**Trade-off**: Less control over chunking strategy and retrieval tuning. Acceptable for MVP; can be replaced with custom RAG if needed.

### Decision: EventBridge for post-call events (not direct Lambda invoke)

**Rationale**: Notifications and analytics are not on the critical call path. EventBridge decouples the Reservation Service from the Notification Service, allowing independent scaling, retries, and future fan-out to additional consumers without changing the producer.

**Trade-off**: Eventual consistency for notifications (acceptable — 30s SLA). Added complexity of event schema management.

### Decision: Provisioned Concurrency on Call Handler only

**Rationale**: Cold starts on the Call Handler directly impact voice response latency (caller hears silence). Downstream services (Reservation, FAQ) are invoked after the first response, so their cold starts are less perceptible. Provisioned Concurrency has a cost; applying it selectively minimises cost impact.

---

*Document Status: Draft — Pending stakeholder review before implementation begins.*
