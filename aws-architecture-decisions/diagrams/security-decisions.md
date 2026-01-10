# Security Decision Tree

> **Purpose:** Choose the right AWS security service for identity management, threat detection, compliance, encryption, and access control.

## Identity & Access Decision

```mermaid
flowchart TD
    Start([Access Need]) --> Q1{Who needs access?}

    Q1 -->|AWS Service| ROLE_SVC[IAM Service Role]
    Q1 -->|EC2 Instance| ROLE_EC2[IAM Instance Profile]
    Q1 -->|Human User| Q2{Workforce type?}
    Q1 -->|External App| Q3{Temporary?}

    Q2 -->|AWS employees| IAM_USER[IAM Users + MFA]
    Q2 -->|Enterprise SSO| IAM_IC[IAM Identity Center<br/>+ IdP Federation]

    Q3 -->|Yes, short-lived| STS[STS AssumeRole]
    Q3 -->|No, app identity| IAM_USER

    ROLE_EC2 --> NEVER[❌ Never use<br/>access keys on EC2]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px,color:#000000
    classDef never fill:#FFB6C1,stroke:#DC143C,stroke-width:2px,color:#000000
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:#000000

    class Q1,Q2,Q3 question
    class ROLE_SVC,ROLE_EC2,IAM_USER,IAM_IC,STS service
    class NEVER never
```

## Threat Detection Decision

```mermaid
flowchart TD
    Start([Security Monitoring]) --> Q1{What to detect?}

    Q1 -->|Malicious activity/threats| GUARDDUTY[Amazon<br/>GuardDuty]
    Q1 -->|Software vulnerabilities| INSPECTOR[Amazon<br/>Inspector]
    Q1 -->|Config compliance| CONFIG[AWS Config]
    Q1 -->|API audit trail| CLOUDTRAIL[CloudTrail]
    Q1 -->|DDoS attacks| SHIELD[AWS Shield]

    GUARDDUTY --> USE_GD[S3 threats<br/>EC2 compromise<br/>Account anomalies]
    INSPECTOR --> USE_IN[CVE scanning<br/>Network exposure<br/>Container vulns]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px,color:#000000
    classDef usecase fill:#E6E6FA,stroke:#9370DB,stroke-width:1px,color:#000000
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:#000000

    class Q1 question
    class GUARDDUTY,INSPECTOR,CONFIG,CLOUDTRAIL,SHIELD service
    class USE_GD,USE_IN usecase
```

## Encryption Decision

```mermaid
flowchart TD
    Start([Encryption Need]) --> Q1{Key Management?}

    Q1 -->|AWS managed| SSE_S3[SSE-S3<br/>S3 managed keys]
    Q1 -->|Audit trail needed| SSE_KMS[SSE-KMS<br/>KMS managed]
    Q1 -->|Customer controlled| Q2{Key location?}

    Q2 -->|AWS KMS| SSE_KMS_CMK[SSE-KMS<br/>Customer CMK]
    Q2 -->|Customer premises| SSE_C[SSE-C<br/>Customer provided]
    Q2 -->|Before upload| CLIENT[Client-side<br/>encryption]

    SSE_KMS --> AUDIT[Full audit via<br/>CloudTrail]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px,color:#000000
    classDef feat fill:#E6E6FA,stroke:#9370DB,stroke-width:1px,color:#000000
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:#000000

    class Q1,Q2 question
    class SSE_S3,SSE_KMS,SSE_KMS_CMK,SSE_C,CLIENT service
    class AUDIT feat
```

## Web Application Protection

```mermaid
flowchart TD
    Start([Web Protection]) --> Q1{Attack Type?}

    Q1 -->|SQL injection, XSS| WAF[AWS WAF]
    Q1 -->|DDoS Layer 3/4| SHIELD_STD[Shield Standard<br/>Free, automatic]
    Q1 -->|DDoS Layer 7| SHIELD_ADV[Shield Advanced<br/>+ WAF]
    Q1 -->|Bot traffic| WAF_BOT[WAF Bot Control]

    WAF --> ATTACH[Attach to:<br/>ALB, CloudFront,<br/>API Gateway]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px,color:#000000
    classDef feat fill:#E6E6FA,stroke:#9370DB,stroke-width:1px,color:#000000
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:#000000

    class Q1 question
    class WAF,SHIELD_STD,SHIELD_ADV,WAF_BOT service
    class ATTACH feat
```

## Keyword → Service Mapping

| Keywords / Signals | AWS Service | Reasoning |
|--------------------|-------------|-----------|
| temporary credentials | IAM Roles / STS | No long-lived keys |
| EC2 needs AWS access | IAM Instance Profile | Never use access keys |
| multi-account, enterprise SSO | IAM Identity Center | Centralized access |
| threat detection, malicious activity | GuardDuty | ML-based threat detection |
| vulnerability scanning, CVE | Inspector | Software vulnerability detection |
| API audit, who did what | CloudTrail | API logging |
| compliance rules | AWS Config | Configuration compliance |
| DDoS protection | Shield | Layer 3/4/7 protection |
| SQL injection, XSS | WAF | Web app firewall |
| secrets storage | Secrets Manager | Automatic rotation |
| parameters, config | Parameter Store | Simple key-value |
| encryption audit | SSE-KMS | CloudTrail integration |

## Elimination Rules

| Never Choose | When | Because |
|--------------|------|---------|
| Hard-coded credentials | Ever | Security anti-pattern |
| IAM User for EC2 | Instance needs AWS access | Use Instance Profile |
| Root account | Day-to-day operations | MFA + emergency only |
| Inspector | Need threat detection | Inspector scans vulns, not threats |
| GuardDuty | Need vuln scanning | GuardDuty detects threats, not CVEs |
| Shield Standard | Layer 7 DDoS protection | Use Shield Advanced + WAF |
| SSE-S3 | Need audit trail | No CloudTrail logging |

## Security Services Comparison

| Service | Purpose | Scope |
|---------|---------|-------|
| GuardDuty | Threat detection | S3 suspicious access, crypto mining, EC2 compromise |
| Inspector | Vulnerability scanning | EC2, ECR, Lambda CVE detection |
| Config | Resource compliance | Configuration history, compliance rules |
| CloudTrail | API call logging | Who did what, when |
| Security Hub | Centralized findings | Aggregate from all security services |
| Security Lake | Centralized security logs | Multi-account security data lake |

> **Key Rules:**
> - Threat detection → GuardDuty
> - Vulnerability scanning → Inspector
> - Resource configuration compliance → AWS Config
> - API audit → CloudTrail
> - Multi-account security logs → Security Lake

## Secrets Management Comparison

| Service | Use Case | Rotation |
|---------|----------|----------|
| Secrets Manager | DB passwords, API keys | Built-in automatic |
| Parameter Store | Config values, simple secrets | Manual |
| KMS | Encryption keys | Automatic (yearly) |

## Organization Guardrails Decision

```mermaid
flowchart TD
    Start([Access Control]) --> Q1{Scope?}

    Q1 -->|Organization/OU/Account| SCP[Service Control<br/>Policy SCP]
    Q1 -->|IAM principal max| BOUNDARY[Permissions<br/>Boundary]
    Q1 -->|User/Role/Group| IAM[IAM Policy]

    SCP --> DESC_SCP[Restrict even<br/>root users]
    BOUNDARY --> DESC_B[Max permissions<br/>ceiling]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px,color:#000000
    classDef desc fill:#E6E6FA,stroke:#9370DB,stroke-width:1px,color:#000000
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px,color:#000000

    class Q1 question
    class SCP,BOUNDARY,IAM service
    class DESC_SCP,DESC_B desc
```

## Organization Guardrails Comparison

| Guardrail | Scope | Use Case |
|-----------|-------|----------|
| SCP | Organization/OU/Account | Restrict even root users |
| Permissions Boundary | IAM principal | Max permissions ceiling |
| IAM Policy | User/Role/Group | Standard permissions |

> **Rules:**
> - Org-wide restriction → SCP
> - Prevent users escalating permissions → Permissions Boundary
> - SCP = only way to restrict root users in member accounts

## IAM Policy Evaluation Logic

```
1. Explicit Deny (wins everything)
2. Explicit Allow
3. Implicit Deny (default)
```

> **Rule:** Explicit Deny > Explicit Allow > Implicit Deny

## IAM Condition Keys

| Key | Purpose | Example |
|-----|---------|---------|
| aws:SourceIp | Caller's IP address | Restrict API calls by location |
| aws:RequestedRegion | Region for resource creation | Restrict deployments to regions |
| aws:VpcSourceIp | Private IP within VPC | Internal service restrictions |
| aws:PrincipalOrgID | Organization restriction | Cross-account within org |

> **Rule:** aws:SourceIp = WHERE API call originates | aws:RequestedRegion = WHERE resource is created

## API Gateway Authorization

| Method | Use Case | Token Type |
|--------|----------|------------|
| Resource Policy | IP/VPC restriction | N/A |
| IAM Authorization | AWS credentials | SigV4 |
| Cognito Authorizer | User pools | Cognito tokens |
| Lambda Authorizer | Custom logic | Any |
| JWT Authorizer (HTTP API) | OIDC/JWT tokens | JWT |

> **Rules:**
> - API Gateway IP restriction → Resource Policy (not SGs)
> - JWT/OIDC native validation → HTTP API JWT Authorizer
> - API Gateway has no security groups

## EC2 Credentials - Best Practice

| ✅ Do | ❌ Never |
|-------|---------|
| IAM Role + Instance Profile | Hardcoded credentials |
| | Credentials in config files |
| | Credentials in S3 |
| | Credentials in environment variables |

> **Rule:** EC2 accessing AWS services → IAM Instance Profile. Never store credentials on instances.

## Cross-Account Access Patterns

| Type | Method |
|------|--------|
| Human access | IAM Identity Center |
| Programmatic | IAM Role + AssumeRole |
| Hybrid AD | IAM Identity Center + AD Connector |

> **Rule:** Cross-account programmatic → IAM Role + AssumeRole

## Certificate Management

| Scenario | Solution |
|----------|----------|
| Certificate expiration alerts | AWS Config managed rule + SNS |
| Auto-renewal | ACM-issued certificates (not imported) |
| Imported certificates | Manual renewal required |

> **Rule:** Certificate expiration alerts → AWS Config managed rule + SNS

## Root Account Best Practices

| ✅ Do | ❌ Never |
|-------|---------|
| Strong password | Create access keys |
| MFA enabled | Share credentials |
| | Store credentials anywhere |

> **Rule:** Root: MFA + password only, NO access keys ever

## IAM Best Practices Checklist

| Practice | Implementation |
|----------|----------------|
| ✅ Least privilege | Minimal permissions per role |
| ✅ MFA for humans | Require MFA for console |
| ✅ No root access keys | Delete root access keys |
| ✅ Temporary credentials | Use IAM roles, not users |
| ✅ Permissions boundaries | Limit max permissions |
| ✅ Audit logging | Enable CloudTrail |

## S3 Encryption Comparison

| Method | Key Management | Audit Trail | Cost |
|--------|---------------|-------------|------|
| SSE-S3 | S3 managed | No | Free |
| SSE-KMS | KMS managed | Yes (CloudTrail) | KMS API calls |
| SSE-KMS (CMK) | Customer CMK | Yes | KMS + key cost |
| SSE-C | Customer provided | No | Free |
| Client-side | Customer managed | N/A | Varies |

## Trade-off Matrix

| Aspect | IAM User | IAM Role | Identity Center |
|--------|----------|----------|-----------------|
| Credential Type | Long-lived | Temporary | Federated |
| Use Case | Simple/legacy | Services, EC2 | Enterprise SSO |
| Security | Lower | Higher | Highest |
| Management | Per-account | Per-account | Centralized |

## Real-World Scenarios

### Scenario 1: EC2 Application Needs S3 Access
**Requirement:** App on EC2 must read from S3
**Decision:** IAM Instance Profile with S3 read policy
**Reasoning:** Never store credentials on EC2

### Scenario 2: Detect S3 Data Exfiltration
**Requirement:** Alert on suspicious S3 access patterns
**Decision:** Amazon GuardDuty
**Reasoning:** GuardDuty analyzes CloudTrail + VPC Flow Logs

### Scenario 3: Scan Containers for CVEs
**Requirement:** Check ECR images for vulnerabilities
**Decision:** Amazon Inspector
**Reasoning:** Built-in container image scanning

### Scenario 4: Enterprise Multi-Account SSO
**Requirement:** 500 employees, 20 AWS accounts, Active Directory
**Decision:** IAM Identity Center + AD Connector
**Reasoning:** Centralized SSO, no password sync

### Scenario 5: Prevent Over-Privileged Roles
**Requirement:** Developers can create roles but not admin access
**Decision:** IAM Permissions Boundaries
**Reasoning:** Cap maximum permissions developers can grant

### Scenario 6: Encryption with Audit Trail
**Requirement:** S3 encryption, need to track key usage
**Decision:** SSE-KMS
**Reasoning:** CloudTrail logs every encryption/decryption

### Scenario 7: Block SQL Injection on ALB
**Requirement:** Protect web app from OWASP Top 10
**Decision:** AWS WAF on ALB
**Reasoning:** WAF managed rules for SQLi, XSS

## Common Mistakes

1. **Mistake:** Storing AWS credentials in code/environment
   **Correct approach:** Use IAM roles for services

2. **Mistake:** Using GuardDuty for vulnerability scanning
   **Correct approach:** Use Inspector for CVE detection

3. **Mistake:** Using root account for daily tasks
   **Correct approach:** Create IAM users/roles, use root only for emergencies

4. **Mistake:** Sharing IAM credentials between users
   **Correct approach:** One IAM user per person, use roles for sharing

5. **Mistake:** SSE-S3 when audit trail needed
   **Correct approach:** Use SSE-KMS for CloudTrail integration

## Network Security Layers

| Layer | Service | Controls |
|-------|---------|----------|
| Edge | Shield, WAF, CloudFront | DDoS, web attacks |
| VPC | NACLs | Subnet-level, stateless |
| Instance | Security Groups | Instance-level, stateful |
| Application | IAM, Cognito | Identity, authorization |
| Data | KMS, Secrets Manager | Encryption, secrets |

## Related Decisions

- [Networking Decisions](./networking-decisions.md) - WAF placement
- [Database Decisions](./database-decisions.md) - Encryption at rest
- [Compute Decisions](./compute-decisions.md) - Instance profiles

---

## Quick Reference

1. **Temporary credentials** → IAM Roles (always)
2. **EC2 AWS access** → Instance Profile (never keys)
3. **Threat detection** → GuardDuty
4. **Vulnerability scanning** → Inspector
5. **Audit trail for encryption** → SSE-KMS
6. **SQL injection/XSS** → WAF
7. **DDoS** → Shield (Standard free, Advanced paid)
8. **Root account** → MFA + strong password only
9. **Prevent excessive permissions** → Permissions Boundaries
10. **Org-wide restriction** → SCP (even restricts root)
11. **API Gateway IP restriction** → Resource Policy (not SGs)
12. **Cross-account programmatic** → IAM Role + AssumeRole
13. **Certificate expiration alerts** → AWS Config rule + SNS
14. **Multi-account security logs** → Security Lake
15. **Explicit Deny** → Always wins in IAM evaluation
