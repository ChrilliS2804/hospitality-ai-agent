# Architecture Decision Record: Domain-Driven Design with Clean Architecture

**Status**: Accepted  
**Date**: 2026-05-31  
**Author**: Cloud Architecture Team

## Context

The platform will grow from a single-service MVP to a multi-service, multi-tenant SaaS platform. We need an architectural style that:
- Keeps business logic independent of AWS infrastructure
- Enables unit testing without AWS dependencies
- Supports multiple developers working in parallel
- Scales to new domains (hotel, multi-tenant) without rewrites

## Decision

**We will apply Domain-Driven Design (DDD) with Clean Architecture across all services.**

## Rationale

1. **Testability**: Domain and application layers have zero AWS dependencies. Unit tests run without moto or LocalStack.

2. **Maintainability**: Business rules live in the domain layer. Infrastructure changes (swap DynamoDB for RDS) don't touch business logic.

3. **Bounded Contexts**: Each service (reservation, FAQ, handoff) is a bounded context with its own domain model. No shared mutable state between services.

4. **Ubiquitous Language**: Domain model reflects hospitality terminology (Reservation, Guest, Slot, Tenant). Code reads like the business domain.

5. **Extensibility**: New use cases are new use case classes. New infrastructure is a new repository implementation. Open/Closed Principle applied.

## Layer Responsibilities

```
api/            Lambda handler. Deserialises event, calls use case, serialises response.
                No business logic. Depends on application layer only.

application/    Use cases (commands/queries). Orchestrates domain objects.
                Calls repository interfaces. Publishes domain events.
                No AWS SDK imports.

domain/         Entities, value objects, aggregates, repository interfaces, exceptions.
                Pure Python. No framework dependencies. No AWS imports.

infrastructure/ Repository implementations (DynamoDB). AWS client wrappers.
                Implements domain repository interfaces.
                All AWS SDK usage lives here.
```

## Consequences

### Positive
- ✅ Domain logic fully unit-testable without AWS
- ✅ Infrastructure swappable without touching business logic
- ✅ Clear separation of concerns for team collaboration
- ✅ Consistent structure across all services reduces cognitive load

### Negative
- ⚠️ More boilerplate than a simple script-style Lambda
- ⚠️ Requires team discipline to maintain layer boundaries
- ⚠️ Slight overhead for simple operations (mitigated by code generation templates)

## Implementation Details

1. **Repository Pattern**: Domain defines `IReservationRepository` interface; infrastructure provides `DynamoDBReservationRepository` implementation. Dependency injection via constructor.

2. **Value Objects**: `PhoneNumber`, `Email`, `ReservationSlot` are immutable value objects with validation in `__init__`. Invalid values raise domain exceptions, not HTTP errors.

3. **Domain Events**: Raised by aggregates, collected by use cases, published to EventBridge by infrastructure. Domain layer has no knowledge of EventBridge.

4. **Use Cases**: One class per use case (`CreateReservationUseCase`, `CancelReservationUseCase`). Each has a single `execute(command: DTO) -> DTO` method.

5. **DTOs**: Pydantic models for input/output at application layer boundary. Domain entities are never serialised directly to API responses.

## Related ADRs

- ADR-001: Use Terraform
- ADR-002: Serverless-First Architecture
- ADR-003: Use Bedrock

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-31 | Initial decision |
