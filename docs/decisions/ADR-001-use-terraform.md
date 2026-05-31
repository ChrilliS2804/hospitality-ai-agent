# Architecture Decision Record: Use Terraform for IaC

**Status**: Accepted  
**Date**: 2026-05-31  
**Author**: Cloud Architecture Team

## Context

We need Infrastructure as Code tooling for managing AWS resources across multiple environments (dev, test, prod). The decision criteria include:
- Multi-cloud support (we may expand beyond AWS)
- Terraform or CloudFormation/CDK
- Team familiarity and ecosystem maturity
- State management capabilities
- Reusability and modularity

## Decision

**We will use Terraform for all Infrastructure as Code.**

## Rationale

1. **Cloud Agnostic**: Terraform works across AWS, Azure, GCP, and others. If we expand beyond AWS, we have a consistent IaC language.

2. **Modularity**: Terraform modules enable code reuse across environments. We structure as:
   - `modules/`: Reusable components (Connect, Bedrock, Lambda, etc.)
   - `environments/`: Environment-specific configurations (dev, test, prod)

3. **State Management**: 
   - Remote state via S3 + DynamoDB for locking
   - Enables team collaboration without state conflicts
   - Audit trail via CloudTrail

4. **Ecosystem**: 
   - Large community and third-party providers
   - Extensive AWS resource coverage
   - Strong IDE/tooling support (VS Code, Atlantis, Terraform Cloud)

5. **Familiarity**: Team has experience with Terraform; steeper learning curve for CDK/CloudFormation.

## Alternatives Considered

- **CloudFormation**: AWS-native, but vendor lock-in and less readable YAML syntax
- **CDK (TypeScript)**: Modern, programmatic, but adds runtime complexity and requires Node.js
- **Pulumi**: Language-flexible but smaller ecosystem than Terraform

## Consequences

### Positive
- ✅ Consistent, readable IaC language across all environments
- ✅ Easy to version-control and code-review infrastructure changes
- ✅ Modular, DRY code reduces duplication
- ✅ Strong CI/CD integration (terraform plan/apply in GitHub Actions)

### Negative
- ⚠️ State file management is critical; requires discipline
- ⚠️ Larger Terraform state may slow operations (mitigated by modular structure)
- ⚠️ Team needs Terraform expertise

## Implementation Details

1. **State Storage**:
   - Backend: S3 + DynamoDB (per environment)
   - Encryption at rest: Enabled
   - Versioning: Enabled for recovery

2. **Module Structure**:
   ```
   terraform/
   ├── modules/        # Reusable components
   ├── environments/   # Per-environment configs
   └── locals.tf       # Shared values
   ```

3. **CI/CD Integration**:
   - GitHub Actions runs `terraform fmt`, `validate`, `plan` on PRs
   - Manual approval for `terraform apply` in prod

4. **Tools & Utilities**:
   - `terraform-docs`: Auto-generate module documentation
   - `tflint`: Linting for best practices
   - `checkov`: Security scanning for IaC

## Related ADRs

- ADR-002: Serverless-First Architecture

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-31 | Initial decision |
