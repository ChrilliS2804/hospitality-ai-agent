# Architecture Decision Record: Use Amazon Bedrock for Generative AI

**Status**: Accepted  
**Date**: 2026-05-31  
**Author**: Cloud Architecture Team

## Context

The platform requires a Large Language Model (LLM) for:
- Natural language understanding (intent classification, slot filling)
- Conversational response generation
- FAQ retrieval-augmented generation (RAG)
- Call summarization

We must choose between self-hosted models, third-party APIs (OpenAI, Anthropic direct), or a managed cloud AI service.

## Decision

**We will use Amazon Bedrock as the managed AI platform, with Claude 3.5 Sonnet as the primary model.**

## Rationale

1. **AWS-Native Integration**: Bedrock integrates natively with IAM, VPC, CloudWatch, and X-Ray. No external API keys to manage — authentication via IAM roles.

2. **No Data Egress**: Prompts and responses stay within AWS. Critical for hospitality PII (guest names, phone numbers). Data is not used to train foundation models.

3. **Managed Knowledge Bases**: Bedrock Knowledge Bases provides a fully managed RAG pipeline (S3 → embedding → OpenSearch Serverless → retrieval) without building custom infrastructure.

4. **Model Flexibility**: Bedrock supports multiple model providers (Anthropic, Amazon, Meta, Mistral). Switching models requires a config change, not an architectural change.

5. **Claude 3.5 Sonnet**: Strong performance on conversational tasks, instruction following, and structured output (JSON slot extraction). Well-suited for hospitality domain.

6. **Cost**: Pay-per-token with no minimum commitment. Aligns with serverless cost model.

## Alternatives Considered

- **OpenAI API (direct)**: Strong models, but data leaves AWS; requires external secret management; no native AWS integration.
- **Self-hosted (SageMaker)**: Full control, but significant operational overhead; requires GPU instances; not serverless.
- **Amazon Lex**: Purpose-built for conversational AI, but limited LLM capability; rigid intent/slot model; less flexible for complex conversations.

## Consequences

### Positive
- ✅ No PII leaves AWS boundary
- ✅ IAM-based auth — no API key rotation
- ✅ Managed Knowledge Bases reduces RAG complexity
- ✅ Model swap is a config change
- ✅ Native CloudWatch and X-Ray integration

### Negative
- ⚠️ Bedrock model availability varies by AWS region — must verify target region
- ⚠️ Bedrock latency (300–800ms per call) must be accounted for in voice UX design
- ⚠️ Token costs can grow with long conversation histories — context window management required

## Implementation Details

1. **Model**: `anthropic.claude-3-5-sonnet-20241022-v2:0` (configurable via environment variable)
2. **Invocation**: `bedrock-runtime:InvokeModel` for NLU; `bedrock-agent-runtime:RetrieveAndGenerate` for FAQ
3. **Prompt Strategy**: System prompt defines agent persona and constraints; conversation history passed as messages array
4. **Structured Output**: Bedrock responses parsed as JSON for slot extraction; Pydantic models validate output
5. **Knowledge Base**: S3 data source → Bedrock managed embedding → OpenSearch Serverless collection

## Related ADRs

- ADR-002: Serverless-First Architecture
- ADR-004: DDD Architecture

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-31 | Initial decision |
