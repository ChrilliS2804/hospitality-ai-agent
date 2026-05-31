# Architecture Decision Record: Serverless-First Architecture

**Status**: Accepted  
**Date**: 2026-05-31  
**Author**: Cloud Architecture Team

## Context

The platform needs to handle variable, unpredictable workloads (restaurant/hotel call volumes vary by time). We must choose between:
- Traditional containers (ECS/EKS)
- Serverless (Lambda, managed services)
- Hybrid approach

Decision criteria:
- Scalability (auto-scale to zero)
- Operational overhead
- Cost efficiency
- Development velocity

## Decision

**We will adopt a Serverless-First architecture using AWS Lambda, managed services, and event-driven patterns.**

## Rationale

1. **Auto-Scale to Zero**: 
   - Lambda scales from 0 to thousands of concurrent invocations automatically
   - During off-peak hours, costs approach zero
   - Perfect for hospitality use case (busy dinner hours, quiet mornings)

2. **Operational Simplicity**: 
   - No servers to provision, patch, or manage
   - AWS handles OS, runtime, security patches
   - Focus on business logic, not infrastructure

3. **Cost Efficiency**:
   - Pay only for compute time (100ms granularity)
   - No reserved capacity overhead
   - Lower total cost of ownership vs. ECS/EKS

4. **Event-Driven Architecture**:
   - Decoupled services via EventBridge, SNS, SQS
   - Enables independent scaling and deployment
   - Async patterns reduce latency for end users

5. **Development Velocity**:
   - Rapid iteration: deploy in seconds
   - Local testing with moto/LocalStack
   - Built-in CI/CD primitives

## Alternatives Considered

- **ECS/Fargate**: More control, but less auto-scaling granularity; higher baseline cost
- **EKS**: Full container orchestration; complex, high operational overhead
- **Hybrid**: Containers for heavy compute, Lambda for light workloads; adds complexity

## Consequences

### Positive
- ✅ Extremely cost-effective for variable workloads
- ✅ Automatic scaling with no configuration
- ✅ Minimal operational burden
- ✅ Fast deployment cycles
- ✅ Built-in integration with AWS services (EventBridge, SNS, DynamoDB)

### Negative
- ⚠️ Cold starts (mitigated by Provisioned Concurrency if needed)
- ⚠️ 15-minute execution limit (not an issue for our use case)
- ⚠️ Stateless functions (state in DynamoDB, not process memory)
- ⚠️ Vendor lock-in to AWS

## Implementation Details

1. **Lambda Functions**:
   - Python 3.12 runtime
   - Each service deployed as independent Lambda function(s)
   - Provisioned Concurrency for critical paths (Connect handler)

2. **Event-Driven Design**:
   - Amazon Connect → Lambda (synchronous)
   - Lambda → EventBridge → Other services (async)
   - DynamoDB Streams → SNS (notifications)

3. **State Management**:
   - Conversation state in DynamoDB
   - No in-process memory for user sessions
   - TTL for automatic cleanup

4. **Performance Optimization**:
   - Lambda layers for shared dependencies
   - Connection pooling (boto3 reuse)
   - CloudFront for static assets

## Monitoring & Alarms

- CloudWatch for Lambda duration, errors, throttling
- X-Ray for distributed tracing
- Alarms for cold start frequency and duration

## Cost Estimation

**Assumptions**: 100K phone calls/month, avg 3 min duration, 128MB Lambda

```
Compute: 100K × 3 min × $0.0000166/GB-second = ~$25/month
Storage: DynamoDB on-demand ≈ $30-50/month
Total: ~$100-150/month baseline
```

## Related ADRs

- ADR-001: Use Terraform
- ADR-003: Use Bedrock for LLM

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-31 | Initial decision |
