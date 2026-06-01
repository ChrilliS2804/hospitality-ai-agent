# Product Requirements Document (PRD)
# Hospitality AI Voice Agent Platform

**Version**: 1.0  
**Status**: Draft for Review  
**Date**: 2026-05-31  
**Author**: Cloud Architecture Team  
**Classification**: Internal

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals and Non-Goals](#3-goals-and-non-goals)
4. [Target Users and Personas](#4-target-users-and-personas)
5. [Use Cases and User Stories](#5-use-cases-and-user-stories)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [MVP Definition (Phase 1)](#8-mvp-definition-phase-1)
9. [Future Phases](#9-future-phases)
10. [Epics and Features](#10-epics-and-features)
11. [Domain Model](#11-domain-model)
12. [Assumptions, Risks, and Unknowns](#12-assumptions-risks-and-unknowns)
13. [Success Metrics](#13-success-metrics)
14. [Out of Scope](#14-out-of-scope)

---

## 1. Executive Summary

The Hospitality AI Voice Agent Platform is a serverless, AI-powered solution that autonomously handles inbound phone calls for restaurants and hotels. It understands natural language, performs real-time actions against backend systems (reservations, availability checks, cancellations), and delivers a professional customer experience — 24 hours a day, 7 days a week.

The platform is designed as a multi-tenant SaaS-style solution, enabling multiple hospitality businesses to onboard without bespoke infrastructure. It reduces operational workload for front-of-house staff while maintaining or improving customer satisfaction scores.

The MVP focuses on restaurant table reservation management via voice, with hotel and extended capabilities delivered in subsequent phases.

---

## 2. Problem Statement

### Current State

Restaurants and hotels rely heavily on phone-based customer interactions for reservations, inquiries, and modifications. This creates several operational challenges:

- **Staffing cost**: Dedicated staff required to answer phones during all operating hours
- **After-hours gap**: Calls outside business hours go unanswered, resulting in lost bookings
- **Peak-hour overload**: High call volumes during busy periods lead to missed calls and customer frustration
- **Inconsistency**: Service quality varies by staff member, shift, and workload
- **No 24/7 coverage**: Most small-to-medium hospitality businesses cannot afford round-the-clock staffing

### Impact

- Lost revenue from unanswered or mishandled reservation calls
- Customer dissatisfaction from long hold times or unavailable staff
- Staff burnout from repetitive, low-value phone interactions
- Inability to scale during peak seasons without proportional staffing increases

### Opportunity

Advances in conversational AI (LLMs), cloud telephony (Amazon Connect), and serverless compute (AWS Lambda) make it feasible to automate the majority of inbound hospitality calls at a fraction of the cost of human staffing, while maintaining a natural, professional customer experience.

---

## 3. Goals and Non-Goals

### Goals

- **G1**: Automate inbound phone call handling for restaurant table reservations (MVP)
- **G2**: Automate inbound phone call handling for hotel room reservations (Phase 2)
- **G3**: Handle FAQ and general information requests via voice
- **G4**: Provide seamless human handoff when AI cannot resolve a request
- **G5**: Send confirmation notifications via SMS and email
- **G6**: Support multi-language conversations
- **G7**: Deliver a multi-tenant platform supporting multiple hospitality businesses
- **G8**: Achieve full infrastructure automation via Terraform and GitHub Actions
- **G9**: Provide comprehensive observability for operations teams
- **G10**: Design for extensibility — new capabilities should not require architectural changes

### Non-Goals

- Building a custom telephony system (Amazon Connect handles this)
- Building a custom LLM (Amazon Bedrock provides managed models)
- Building a customer-facing web or mobile application (voice-only for MVP)
- Payment processing (out of scope for all phases currently)
- POS system integration (future consideration)
- Building a self-service onboarding portal for hospitality businesses (future phase)

---

## 4. Target Users and Personas

### Primary Users (Callers)

**Persona 1: Restaurant Guest — "Alex"**
- Age: 25–65, broad demographic
- Goal: Make, change, or cancel a table reservation quickly
- Frustration: Being put on hold, calling back multiple times, no after-hours option
- Expectation: Fast, accurate, natural conversation; confirmation via SMS/email

**Persona 2: Hotel Guest — "Jordan"**
- Age: 25–65, business and leisure traveller
- Goal: Book a room, check availability, modify or cancel a booking
- Frustration: Long IVR menus, being transferred multiple times
- Expectation: Efficient, accurate booking with immediate confirmation

### Secondary Users (Operators)

**Persona 3: Restaurant/Hotel Manager — "Sam"**
- Goal: Reduce phone workload on staff, never miss a booking
- Frustration: Staff spending time on repetitive calls instead of in-venue service
- Expectation: Reliable automation, easy configuration, visibility into call activity

**Persona 4: Platform Administrator — "Dev/Ops Team"**
- Goal: Deploy, monitor, and maintain the platform across multiple tenants
- Expectation: Infrastructure as Code, CI/CD pipelines, clear observability, runbooks

---

## 5. Use Cases and User Stories

### Restaurant Use Cases

#### UC-R01: Make a Table Reservation
**As a** restaurant guest,  
**I want to** call the restaurant and make a table reservation by speaking naturally,  
**So that** I can secure a table without waiting for a human to answer.

**Acceptance Criteria**:
- Agent greets caller and identifies intent within 2 conversational turns
- Agent collects: date, time, party size, guest name, contact number
- Agent checks real-time availability against DynamoDB
- Agent confirms booking and provides a reference number
- Confirmation SMS and/or email sent within 30 seconds of booking
- Reservation persisted to DynamoDB with full details

#### UC-R02: Cancel a Reservation
**As a** restaurant guest,  
**I want to** cancel my existing reservation by phone,  
**So that** I can free up the table without needing to speak to a human.

**Acceptance Criteria**:
- Agent identifies caller intent to cancel
- Agent retrieves reservation by reference number or phone number + date
- Agent confirms reservation details before cancellation
- Agent cancels reservation and confirms cancellation verbally
- Cancellation confirmation SMS/email sent to guest
- Reservation status updated in DynamoDB

#### UC-R03: Modify a Reservation
**As a** restaurant guest,  
**I want to** change the date, time, or party size of my reservation,  
**So that** I can update my booking without starting over.

**Acceptance Criteria**:
- Agent identifies modification intent
- Agent retrieves existing reservation
- Agent collects new details (date/time/party size)
- Agent checks availability for new slot
- Agent confirms change and updates reservation
- Updated confirmation sent via SMS/email

#### UC-R04: Check Opening Hours
**As a** restaurant guest,  
**I want to** ask what time the restaurant opens or closes,  
**So that** I can plan my visit.

**Acceptance Criteria**:
- Agent answers opening hours questions accurately from configured knowledge base
- Response delivered within one conversational turn

#### UC-R05: Ask About the Menu
**As a** restaurant guest,  
**I want to** ask about menu items, dietary options, or specials,  
**So that** I can decide whether to visit or what to order.

**Acceptance Criteria**:
- Agent answers menu questions from FAQ/knowledge base
- Agent acknowledges when information is unavailable and offers human handoff

#### UC-R06: Human Handoff
**As a** restaurant guest,  
**I want to** speak to a human when the AI cannot help me,  
**So that** my issue is still resolved.

**Acceptance Criteria**:
- Agent detects inability to resolve request after configurable retry attempts
- Agent offers transfer to human agent
- Call transferred to available staff via Amazon Connect
- If no staff available, agent takes a message and promises callback
- Call summary generated and stored for the receiving human agent

### Hotel Use Cases (Phase 2)

- UC-H01: Book a Room
- UC-H02: Cancel a Room Booking
- UC-H03: Modify a Room Booking
- UC-H04: Check-in / Check-out Information
- UC-H05: Hotel Information (amenities, parking, WiFi, etc.)
- UC-H06: Human Handoff

### General Use Cases

#### UC-G01: Multi-Language Support
**As a** non-English speaking guest,  
**I want to** interact with the agent in my preferred language,  
**So that** I can complete my request without a language barrier.

**Acceptance Criteria**:
- Agent detects caller language automatically
- Agent responds in detected language
- Supported languages: English, Spanish, French (MVP); extensible to others

#### UC-G02: Call Summarization
**As a** restaurant manager,  
**I want** every call to be summarized and stored,  
**So that** I can review interactions and identify improvement areas.

**Acceptance Criteria**:
- Call summary generated by LLM at end of each call
- Summary stored in DynamoDB with call metadata
- Summary accessible via future management interface

---

## 6. Functional Requirements

### FR-01: Voice Call Ingestion
- Platform must receive inbound calls via Amazon Connect
- Amazon Connect Contact Flow must route calls to the AI agent Lambda
- DTMF (keypad) fallback must be available if voice recognition fails

### FR-02: Natural Language Understanding
- Platform must use Amazon Bedrock (Claude) to understand caller intent
- Intent classification must support: reservation, cancellation, modification, FAQ, human handoff
- Confidence threshold must be configurable; low-confidence triggers clarification

### FR-03: Conversation State Management
- Conversation state must be persisted in DynamoDB across Lambda invocations
- State must include: session ID, intent, collected slots, turn history, tenant ID
- State TTL: 24 hours (configurable)

### FR-04: Reservation Management
- Create, read, update, and cancel reservations in DynamoDB
- Availability check must be real-time against existing reservations
- Reservation must include: ID, tenant ID, guest name, phone, email, date, time, party size, status, created/updated timestamps

### FR-05: Notification Delivery
- SMS notifications via Amazon SNS
- Email notifications via Amazon SES
- Notifications triggered on: reservation created, modified, cancelled
- Notification templates must be configurable per tenant

### FR-06: FAQ and Knowledge Base
- FAQ responses served from Amazon Bedrock Knowledge Bases (backed by OpenSearch Serverless)
- Knowledge base content manageable without code changes
- Fallback to human handoff if no relevant answer found

### FR-07: Human Handoff
- Agent must detect escalation triggers: explicit request, repeated failure, sentiment detection
- Call transfer via Amazon Connect
- If no agent available: record callback request, store in DynamoDB, notify staff via SNS

### FR-08: Multi-Tenancy
- All data partitioned by tenant ID
- Tenant configuration (business name, hours, notification settings) stored in DynamoDB
- Platform must support onboarding new tenants without infrastructure changes

### FR-09: Security
- All secrets stored in AWS Secrets Manager
- IAM roles follow least-privilege principle
- All data encrypted at rest (KMS) and in transit (TLS)
- No hardcoded credentials anywhere in codebase

### FR-10: Observability
- Structured JSON logs to CloudWatch for every Lambda invocation
- X-Ray tracing across all service calls
- Custom CloudWatch metrics: call volume, intent distribution, resolution rate, handoff rate
- Alarms on: error rate > 1%, Lambda duration > 10s, DynamoDB throttling

---

## 7. Non-Functional Requirements

### NFR-01: Availability
- Target: 99.9% uptime (aligned with AWS Lambda and Connect SLAs)
- No single point of failure in the call handling path

### NFR-02: Latency
- Voice response latency (Connect → Lambda → Bedrock → response): < 3 seconds P95
- Reservation write to DynamoDB: < 500ms P99
- Notification delivery: < 30 seconds after booking confirmation

### NFR-03: Scalability
- Must handle 0 to 1,000 concurrent calls without configuration changes
- Lambda concurrency limits must be set per environment
- DynamoDB on-demand capacity to handle burst traffic

### NFR-04: Cost Efficiency
- Target: < $200/month at 100K calls/month baseline
- Cost per call must be measurable via CloudWatch custom metrics
- No idle compute costs (serverless-first mandatory)

### NFR-05: Security
- OWASP Top 10 mitigations applied where relevant
- No PII logged in plaintext (phone numbers, names masked in logs)
- CloudTrail enabled for all API calls
- VPC endpoints for DynamoDB, Secrets Manager, Bedrock where applicable

### NFR-06: Maintainability
- Code coverage > 80% (unit + integration)
- All infrastructure changes via Terraform (no console changes)
- All services follow Clean Architecture / DDD patterns
- Linting and formatting enforced via pre-commit hooks and CI

### NFR-07: Deployability
- Full deployment to a new environment achievable in < 30 minutes
- Zero-downtime deployments for Lambda functions
- Rollback achievable in < 5 minutes

### NFR-08: Observability
- Every call traceable end-to-end via X-Ray trace ID
- Business metrics (bookings created, cancelled, handoffs) available in CloudWatch
- Dashboards for operational visibility

---

## 8. MVP Definition (Phase 1)

### Scope

The MVP delivers a working, production-deployable voice agent for **restaurant table reservation management only**.

### MVP Capabilities

| Capability | Included |
|---|---|
| Answer inbound calls via Amazon Connect | ✅ |
| Understand reservation intent (NLU via Bedrock) | ✅ |
| Create table reservation | ✅ |
| Cancel table reservation | ✅ |
| Modify table reservation | ✅ |
| Check availability | ✅ |
| FAQ (opening hours, basic menu info) | ✅ |
| Human handoff | ✅ |
| SMS confirmation (SNS) | ✅ |
| Email confirmation (SES) | ✅ |
| Call summarization | ✅ |
| Multi-language (English only for MVP) | ✅ English only |
| Multi-tenancy | ✅ Single tenant for MVP, architecture supports multi |
| Hotel reservations | ❌ Phase 2 |
| Multi-language (non-English) | ❌ Phase 2 |
| Management dashboard | ❌ Phase 3 |
| Self-service onboarding | ❌ Phase 3 |

### MVP Success Criteria

- Agent successfully handles end-to-end reservation call with no human intervention
- Reservation persisted correctly to DynamoDB
- Confirmation SMS/email delivered within 30 seconds
- Human handoff works when triggered
- All infrastructure deployable via `terraform apply`
- Unit test coverage > 80%
- Integration tests pass against dev environment

---

## 9. Future Phases

### Phase 2: Hotel Reservations
- Room booking, modification, cancellation
- Check-in/check-out information
- Hotel FAQ and amenities information
- Multi-language support (Spanish, French)

### Phase 3: Multi-Tenant SaaS
- Tenant onboarding workflow
- Per-tenant configuration management
- Management dashboard (web UI)
- Billing and usage metering

### Phase 4: Advanced AI Features
- Sentiment analysis and proactive escalation
- Personalisation (returning guest recognition)
- Upselling and cross-selling suggestions
- Voice biometrics for caller identification

### Phase 5: Integrations
- POS system integration (Square, Toast, etc.)
- Property Management System (PMS) integration for hotels
- Google Calendar / OpenTable sync
- CRM integration

---

## 10. Epics and Features

### Epic 1: Voice Channel (E1)
**Goal**: Establish the telephony foundation via Amazon Connect

| Feature ID | Feature | Priority |
|---|---|---|
| E1-F1 | Amazon Connect instance and phone number provisioning | P0 |
| E1-F2 | Contact Flow for inbound call routing | P0 |
| E1-F3 | Lambda integration with Connect Contact Flow | P0 |
| E1-F4 | DTMF fallback handling | P1 |
| E1-F5 | Call recording (optional, configurable) | P2 |

### Epic 2: AI Conversation Engine (E2)
**Goal**: Natural language understanding and conversation management

| Feature ID | Feature | Priority |
|---|---|---|
| E2-F1 | Bedrock Claude integration for intent classification | P0 |
| E2-F2 | Slot filling (collect date, time, party size, name, contact) | P0 |
| E2-F3 | Conversation state management (DynamoDB) | P0 |
| E2-F4 | Multi-turn conversation handling | P0 |
| E2-F5 | Clarification and re-prompt logic | P1 |
| E2-F6 | Call summarization at end of call | P1 |
| E2-F7 | Sentiment detection | P2 |

### Epic 3: Reservation Service (E3)
**Goal**: Core reservation domain logic

| Feature ID | Feature | Priority |
|---|---|---|
| E3-F1 | Create reservation | P0 |
| E3-F2 | Cancel reservation | P0 |
| E3-F3 | Modify reservation | P0 |
| E3-F4 | Check availability | P0 |
| E3-F5 | Retrieve reservation by ID or phone | P0 |
| E3-F6 | Reservation status lifecycle management | P1 |

### Epic 4: Notifications (E4)
**Goal**: Confirmation and update notifications to guests

| Feature ID | Feature | Priority |
|---|---|---|
| E4-F1 | SMS confirmation via SNS (reservation created) | P0 |
| E4-F2 | Email confirmation via SES (reservation created) | P0 |
| E4-F3 | SMS/email on cancellation | P1 |
| E4-F4 | SMS/email on modification | P1 |
| E4-F5 | Configurable notification templates per tenant | P2 |

### Epic 5: FAQ and Knowledge Base (E5)
**Goal**: Answer common questions without human intervention

| Feature ID | Feature | Priority |
|---|---|---|
| E5-F1 | Bedrock Knowledge Base setup (OpenSearch Serverless) | P0 |
| E5-F2 | FAQ ingestion pipeline (S3 → Knowledge Base) | P1 |
| E5-F3 | FAQ query integration in conversation flow | P0 |
| E5-F4 | Fallback to human handoff on no answer | P0 |

### Epic 6: Human Handoff (E6)
**Goal**: Seamless escalation to human agents

| Feature ID | Feature | Priority |
|---|---|---|
| E6-F1 | Detect escalation triggers | P0 |
| E6-F2 | Transfer call via Amazon Connect | P0 |
| E6-F3 | Callback request when no agent available | P1 |
| E6-F4 | Call summary passed to human agent | P1 |

### Epic 7: Infrastructure and Platform (E7)
**Goal**: Production-ready, automated infrastructure

| Feature ID | Feature | Priority |
|---|---|---|
| E7-F1 | Terraform modules for all AWS services | P0 |
| E7-F2 | Multi-environment support (dev, test, prod) | P0 |
| E7-F3 | GitHub Actions CI/CD pipelines | P0 |
| E7-F4 | IAM least-privilege roles | P0 |
| E7-F5 | Secrets Manager integration | P0 |
| E7-F6 | CloudWatch dashboards and alarms | P1 |
| E7-F7 | X-Ray distributed tracing | P1 |
| E7-F8 | KMS encryption for all data stores | P1 |

---

## 11. Domain Model

### Core Aggregates

#### Reservation (Aggregate Root)
```
Reservation
├── reservation_id: UUID
├── tenant_id: String
├── guest: Guest (Value Object)
│   ├── name: String
│   ├── phone: PhoneNumber (Value Object)
│   └── email: Email (Value Object)
├── slot: ReservationSlot (Value Object)
│   ├── date: Date
│   ├── time: Time
│   └── party_size: Integer
├── status: ReservationStatus (Enum)
│   ├── PENDING
│   ├── CONFIRMED
│   ├── MODIFIED
│   ├── CANCELLED
│   └── COMPLETED
├── reference_number: String
├── notes: String (optional)
├── created_at: DateTime
└── updated_at: DateTime
```

#### ConversationSession (Aggregate Root)
```
ConversationSession
├── session_id: String (Connect Contact ID)
├── tenant_id: String
├── caller_phone: PhoneNumber
├── intent: ConversationIntent (Enum)
│   ├── MAKE_RESERVATION
│   ├── CANCEL_RESERVATION
│   ├── MODIFY_RESERVATION
│   ├── FAQ
│   ├── HUMAN_HANDOFF
│   └── UNKNOWN
├── slots: Dict[String, Any]  (collected data)
├── turn_history: List[ConversationTurn]
├── status: SessionStatus (Enum)
│   ├── ACTIVE
│   ├── COMPLETED
│   ├── TRANSFERRED
│   └── ABANDONED
├── reservation_id: UUID (optional, if reservation created)
├── summary: String (optional, generated at end)
├── created_at: DateTime
└── updated_at: DateTime
```

#### Tenant (Aggregate Root)
```
Tenant
├── tenant_id: String
├── business_name: String
├── business_type: BusinessType (Enum: RESTAURANT, HOTEL)
├── phone_number: PhoneNumber
├── operating_hours: List[OperatingHours]
├── notification_config: NotificationConfig
│   ├── sms_enabled: Boolean
│   ├── email_enabled: Boolean
│   └── from_email: Email
├── connect_instance_id: String
└── active: Boolean
```

### Data Storage Note

All domain entities (Reservation, ConversationSession, Tenant) are stored in a **single global DynamoDB table** (`hospitality-{environment}`), using composite key patterns with entity-type prefixes. GSIs support all required access patterns. This is a deliberate architectural choice — see ADR-004 and the system architecture data section for full key design.

### Domain Events

| Event | Trigger | Consumers |
|---|---|---|
| `ReservationCreated` | Reservation confirmed | Notification Service, Analytics |
| `ReservationCancelled` | Reservation cancelled | Notification Service, Analytics |
| `ReservationModified` | Reservation updated | Notification Service, Analytics |
| `CallCompleted` | Call ends | Summarization, Analytics |
| `HumanHandoffRequested` | Escalation triggered | Connect, Staff Notification |
| `CallbackRequested` | No agent available | Staff Notification, DynamoDB |

---

## 12. Assumptions, Risks, and Unknowns

### Assumptions

| ID | Assumption |
|---|---|
| A1 | Amazon Connect is available in the target AWS region |
| A2 | Amazon Bedrock Claude models are available in the target region |
| A3 | Callers have a reasonable mobile signal / audio quality |
| A4 | Restaurant operates a single location per tenant (MVP) |
| A5 | Availability is determined solely by existing reservations (no table management system) |
| A6 | Guest provides phone number and/or email for notifications |
| A7 | English is the only required language for MVP |
| A8 | AWS account has service limits sufficient for expected concurrency |

### Risks

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Bedrock latency causes unacceptable voice response delay | Medium | High | Streaming responses, async patterns, latency testing early |
| R2 | Amazon Connect Contact Flow complexity underestimated | Medium | Medium | Prototype Connect flow in week 1 |
| R3 | LLM hallucination causes incorrect reservation data | Low | High | Strict slot validation, confirmation step before write |
| R4 | AWS service limits hit at scale | Low | High | Request limit increases pre-launch, use on-demand capacity |
| R5 | Multi-tenancy data isolation failure | Low | Critical | Tenant ID in all partition keys, IAM policies, automated tests |
| R6 | Cold start latency on Lambda affects voice experience | Medium | Medium | Provisioned Concurrency on call handler, warm-up strategy |
| R7 | SES/SNS delivery failures for notifications | Low | Medium | Dead letter queues, retry logic, delivery status tracking |
| R8 | Bedrock model deprecation or pricing change | Low | Medium | Abstract model selection, monitor AWS announcements |

### Unknowns

| ID | Unknown | Resolution Approach |
|---|---|---|
| U1 | Exact Amazon Connect Contact Flow design for Bedrock integration | Prototype in Sprint 1 |
| U2 | Bedrock response latency under real telephony conditions | Load test in Sprint 2 |
| U3 | Optimal prompt engineering for hospitality domain | Iterative testing in Sprint 1-2 |
| U4 | DynamoDB table design for availability queries | Design spike in Sprint 1 |
| U5 | SES domain verification requirements for tenant emails | Investigate in Sprint 1 |

---

## 13. Success Metrics

### Business Metrics
- **Call Resolution Rate**: % of calls resolved without human handoff (target: > 80%)
- **Booking Conversion Rate**: % of reservation-intent calls that result in a confirmed booking
- **After-Hours Bookings**: Number of bookings made outside business hours
- **Average Handle Time**: Average call duration (target: < 3 minutes for reservation)

### Technical Metrics
- **Voice Response Latency**: P95 < 3 seconds
- **System Availability**: > 99.9%
- **Error Rate**: < 1% of calls result in system error
- **Cold Start Rate**: < 5% of invocations experience cold start > 1 second

### Quality Metrics
- **Unit Test Coverage**: > 80%
- **Integration Test Pass Rate**: 100% in CI
- **Deployment Frequency**: Multiple times per week (dev), weekly (prod)
- **Mean Time to Recovery (MTTR)**: < 30 minutes

---

## 14. Out of Scope

The following are explicitly out of scope for all current phases unless a change request is raised:

- Payment processing or PCI-DSS compliance
- Outbound calling campaigns
- Real-time table/room inventory management (beyond reservation tracking)
- Native mobile or web application
- Social media or chat channel integration
- Custom wake-word or voice biometrics
- On-premises or hybrid deployment
- Non-AWS cloud providers (Azure, GCP)
- HIPAA or other regulated data compliance (beyond standard security practices)

---

*Document Status: Draft — Pending stakeholder review before implementation begins.*
