# Networking Decision Tree

> **Purpose:** Choose the right AWS networking service for load balancing, global distribution, content delivery, hybrid connectivity, and DNS management.

## Load Balancer Decision

```mermaid
flowchart TD
    Start([Load Balancer Need]) --> Q1{Protocol?}

    Q1 -->|HTTP/HTTPS| Q2{Need content<br/>routing?}
    Q1 -->|TCP/UDP| NLB[Network Load<br/>Balancer]
    Q1 -->|Legacy EC2-Classic| CLB[Classic LB<br/>⚠️ Deprecated]

    Q2 -->|Yes, path/host based| ALB[Application Load<br/>Balancer]
    Q2 -->|No, simple distribution| ALB

    NLB --> FEAT_NLB[Extreme performance<br/>Static IPs<br/>Preserve source IP]
    ALB --> FEAT_ALB[Content routing<br/>WebSockets<br/>gRPC support]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef feat fill:#E6E6FA,stroke:#9370DB,stroke-width:1px
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px
    classDef deprecated fill:#FFB6C1,stroke:#DC143C,stroke-width:2px

    class Q1,Q2 question
    class ALB,NLB service
    class CLB deprecated
    class FEAT_NLB,FEAT_ALB feat
```

## Global Performance Decision

```mermaid
flowchart TD
    Start([Global Performance]) --> Q1{Traffic Type?}

    Q1 -->|HTTP/HTTPS static| CLOUDFRONT[CloudFront<br/>Edge Caching]
    Q1 -->|HTTP/HTTPS dynamic| Q2{Caching helpful?}
    Q1 -->|UDP/Gaming/Real-time| GA[Global<br/>Accelerator]
    Q1 -->|TCP, non-HTTP| GA

    Q2 -->|Yes| CLOUDFRONT
    Q2 -->|No, always origin| GA

    CLOUDFRONT --> USE_CF[Static assets<br/>API caching<br/>Video streaming]
    GA --> USE_GA[Gaming<br/>VoIP<br/>Real-time apps]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef usecase fill:#E6E6FA,stroke:#9370DB,stroke-width:1px
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px

    class Q1,Q2 question
    class CLOUDFRONT,GA service
    class USE_CF,USE_GA usecase
```

## Hybrid Connectivity Decision

```mermaid
flowchart TD
    Start([Hybrid Connection]) --> Q1{Requirement?}

    Q1 -->|Consistent, dedicated| Q2{Bandwidth?}
    Q1 -->|Encrypted over internet| VPN[Site-to-Site VPN]
    Q1 -->|Quick setup, low cost| VPN

    Q2 -->|High, dedicated| DX[Direct Connect]
    Q2 -->|Medium, encrypted| DX_VPN[Direct Connect<br/>+ VPN]

    DX --> FEAT_DX[1-100 Gbps<br/>Consistent latency<br/>Higher cost]
    VPN --> FEAT_VPN[Up to 1.25 Gbps<br/>Variable latency<br/>Lower cost]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef feat fill:#E6E6FA,stroke:#9370DB,stroke-width:1px
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px

    class Q1,Q2 question
    class DX,VPN,DX_VPN service
    class FEAT_DX,FEAT_VPN feat
```

## DNS & Routing Decision

```mermaid
flowchart TD
    Start([DNS/Routing Need]) --> Q1{Routing Type?}

    Q1 -->|Simple| SIMPLE[Simple Routing]
    Q1 -->|Failover| FAILOVER[Failover Routing<br/>+ Health Checks]
    Q1 -->|By user location| Q2{Geographic?}
    Q1 -->|Weighted distribution| WEIGHTED[Weighted Routing]
    Q1 -->|By latency| LATENCY[Latency Routing]

    Q2 -->|By continent/country| GEO[Geolocation<br/>Routing]
    Q2 -->|By nearest location| GEOPROX[Geoproximity<br/>Routing]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px

    class Q1,Q2 question
    class SIMPLE,FAILOVER,WEIGHTED,LATENCY,GEO,GEOPROX service
```

## NAT Gateway vs NAT Instance Decision

```mermaid
flowchart TD
    Start([Internet Access<br/>for Private Subnet]) --> Q1{Need?}

    Q1 -->|Just outbound internet| NAT_GW[NAT Gateway<br/>Managed, HA]
    Q1 -->|Port forwarding| NAT_INST[NAT Instance]
    Q1 -->|Bastion server| NAT_INST
    Q1 -->|Security groups on NAT| NAT_INST

    NAT_GW --> PLACE[Place in<br/>PUBLIC subnet]
    NAT_INST --> PLACE

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef note fill:#E6E6FA,stroke:#9370DB,stroke-width:1px
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px

    class Q1 question
    class NAT_GW,NAT_INST service
    class PLACE note
```

## NAT Gateway vs NAT Instance Comparison

| Feature | NAT Gateway | NAT Instance |
|---------|-------------|--------------|
| Security Groups | ❌ No | ✅ Yes |
| Port Forwarding | ❌ No | ✅ Yes |
| Bastion Server | ❌ No | ✅ Yes |
| Managed | ✅ Yes | ❌ No |
| High Availability | ✅ Built-in | ❌ Manual |
| Bandwidth | Up to 45 Gbps | Instance-dependent |

> **Rule:** Private subnet IPv4 internet → NAT Gateway in PUBLIC subnet

## VPC Endpoints Decision

```mermaid
flowchart TD
    Start([Private AWS<br/>Service Access]) --> Q1{Service?}

    Q1 -->|S3 or DynamoDB| GW_EP[Gateway Endpoint<br/>FREE]
    Q1 -->|Other AWS services| INT_EP[Interface Endpoint<br/>PrivateLink]

    GW_EP --> DESC_GW[Route table entry<br/>No additional cost]
    INT_EP --> DESC_INT[ENI in subnet<br/>Hourly + data cost]

    %% Styling
    classDef service fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef desc fill:#E6E6FA,stroke:#9370DB,stroke-width:1px
    classDef question fill:#FFE4B5,stroke:#FF8C00,stroke-width:2px

    class Q1 question
    class GW_EP,INT_EP service
    class DESC_GW,DESC_INT desc
```

## VPC Endpoint Types

| Type | Services | Cost | Implementation |
|------|----------|------|----------------|
| Gateway Endpoint | S3, DynamoDB only | Free | Route table entry |
| Interface Endpoint | Most AWS services | Hourly + data | ENI with PrivateLink |

> **Rules:**
> - S3/DynamoDB private access → Gateway Endpoint (free)
> - SQS/SNS/other services private access → Interface Endpoint

## Security Groups - Valid Sources

| Valid Source | Example |
|--------------|---------|
| IP address | `10.0.0.1/32` |
| CIDR block | `10.0.0.0/16` |
| Security Group ID | `sg-12345678` |
| Prefix List | `pl-12345678` |

| Invalid Source | Never Use |
|----------------|-----------|
| Internet Gateway ID | ❌ |
| NAT Gateway ID | ❌ |
| Route Table ID | ❌ |

## Security Group Tier Pattern

```
Internet → ALB SG (443 from 0.0.0.0/0) → EC2 SG (80 from ALB SG) → RDS SG (3306 from EC2 SG)
```

> **Rule:** Reference SG IDs between tiers (not CIDRs). DB tier: NEVER allow 0.0.0.0/0

## Common Ports Reference

| Service | Port |
|---------|------|
| HTTP | 80 |
| HTTPS | 443 |
| SSH | 22 |
| RDP | 3389 |
| MySQL/Aurora | 3306 |
| PostgreSQL | 5432 |
| MSSQL | 1433 |
| Oracle | 1521 |
| Redis | 6379 |
| Memcached | 11211 |
| NFS | 2049 |
| SMB | 445 |

## Keyword → Service Mapping

| Keywords / Signals | AWS Service | Reasoning |
|--------------------|-------------|-----------|
| HTTP, path-based, host-based routing | ALB | Layer 7 content routing |
| TCP, UDP, extreme performance | NLB | Layer 4, static IPs |
| WebSockets, gRPC | ALB | Protocol support |
| static content, edge caching | CloudFront | CDN with edge locations |
| UDP, gaming, real-time | Global Accelerator | Anycast, no caching |
| geo-blocking by country | WAF or CloudFront geo-restriction | Content access control |
| dedicated, consistent bandwidth | Direct Connect | Private, dedicated line |
| encrypted, over internet | Site-to-Site VPN | IPsec tunnel |
| DNS failover | Route 53 + health checks | Automatic failover |
| private subnet internet (IPv4) | NAT Gateway in public subnet | Outbound only |
| S3 private access | Gateway Endpoint | Free, route table |
| SQS/SNS private access | Interface Endpoint | PrivateLink |

## Elimination Rules

| Never Choose | When | Because |
|--------------|------|---------|
| ALB | Non-HTTP protocols (TCP/UDP) | ALB is Layer 7 only |
| NLB | Need content-based routing | NLB doesn't inspect content |
| NLB | Need WAF integration | WAF only works with ALB/CloudFront |
| Route 53 alone | Need UDP acceleration | Route 53 is DNS only |
| CloudFront | UDP traffic | CloudFront is HTTP/HTTPS only |
| VPN | Need consistent, high bandwidth | VPN goes over internet |
| Security Groups | Need geo-blocking | SGs don't understand geography |
| Security Groups | API Gateway IP restriction | Use Resource Policy |
| NAT Gateway | Need port forwarding or bastion | NAT Gateway doesn't support these |
| Interface Endpoint | S3 or DynamoDB access | Use Gateway Endpoint (free) |

## ALB vs NLB Comparison

| Feature | ALB | NLB |
|---------|-----|-----|
| Layer | 7 (HTTP/HTTPS) | 4 (TCP/UDP) |
| Routing | Path, host, header | Port only |
| WebSocket | Yes | Yes |
| Static IP | No (use Global Accelerator) | Yes |
| Performance | High | Extreme (millions rps) |
| Source IP | X-Forwarded-For header | Preserved |
| SSL Termination | Yes | Yes (TLS) |
| Cost | Per LCU | Per NLCU |
| WAF Integration | ✅ Yes | ❌ No |

## NLB Target Registration

| Target Type | Routing |
|-------------|---------|
| Instance ID | Routes via primary private IP |
| IP targets | Direct IP routing |

> **Rule:** NLB instance targets → routes via private IP

## CloudFront vs Global Accelerator

| Aspect | CloudFront | Global Accelerator |
|--------|------------|-------------------|
| Traffic | HTTP/HTTPS | TCP/UDP |
| Caching | Yes | No |
| Edge Location | 400+ PoPs | AWS edge network |
| Use Case | Static content, APIs | Gaming, VoIP, real-time |
| Static IPs | No | Yes (anycast) |
| Origin | S3, ALB, custom | ALB, NLB, EC2, EIP |

## Cost Comparison

| Service | Pricing Model | Notes |
|---------|---------------|-------|
| ALB | Per hour + LCU | LCU based on connections, rules, data |
| NLB | Per hour + NLCU | NLCU based on connections, data |
| CloudFront | Per request + data out | Free tier available |
| Global Accelerator | Per hour + data processed | Fixed IP cost |
| Direct Connect | Per port hour + data out | Higher setup, lower data costs |
| VPN | Per connection hour + data | Low fixed cost |

## Trade-off Matrix

| Aspect | ALB | NLB | CloudFront | Global Accelerator |
|--------|-----|-----|------------|-------------------|
| Latency | Low | Very Low | Lowest (cached) | Low |
| Throughput | High | Extreme | Very High | High |
| Caching | No | No | Yes | No |
| Static IP | No | Yes | No | Yes |
| Global | No | No | Yes | Yes |
| Cost | Medium | Low | Variable | Medium |

## Real-World Scenarios

### Scenario 1: Microservices API Gateway
**Requirement:** Route /api/users to User Service, /api/orders to Order Service
**Decision:** Application Load Balancer
**Reasoning:** Path-based routing at Layer 7

### Scenario 2: Gaming Server
**Requirement:** UDP traffic, low latency, global players
**Decision:** Global Accelerator → NLB → Game Servers
**Reasoning:** UDP support, anycast IPs, edge optimization

### Scenario 3: Static Website
**Requirement:** Serve HTML/CSS/JS globally with low latency
**Decision:** S3 + CloudFront
**Reasoning:** Edge caching, HTTPS, cost-effective

### Scenario 4: Block Access by Country
**Requirement:** Restrict video content to USA only
**Decision:** CloudFront with geo-restriction
**Reasoning:** Built-in geo-blocking feature

### Scenario 5: Hybrid Cloud (Predictable Performance)
**Requirement:** Connect data center to AWS, consistent latency
**Decision:** Direct Connect
**Reasoning:** Dedicated bandwidth, no internet variability

### Scenario 6: Cross-Account Private Service Access
**Requirement:** Expose RDS to partner account without internet
**Decision:** NLB + AWS PrivateLink
**Reasoning:** Private, secure, scalable service endpoint

## Route 53 Routing Policies

| Policy | Use Case | Health Checks |
|--------|----------|---------------|
| Simple | Single resource | No |
| Failover | Active-passive DR | Yes |
| Geolocation | Content by country | Optional |
| Geoproximity | Shift traffic by bias | Optional |
| Latency | Lowest latency region | Optional |
| Weighted | A/B testing, blue-green | Optional |
| Multivalue | Multiple healthy resources | Yes |

## Common Mistakes

1. **Mistake:** Using Route 53 for performance acceleration
   **Correct approach:** Use CloudFront or Global Accelerator

2. **Mistake:** Expecting ALB to handle UDP traffic
   **Correct approach:** Use NLB for UDP

3. **Mistake:** Using Security Groups for geo-blocking
   **Correct approach:** Use WAF or CloudFront geo-restriction

4. **Mistake:** CloudFront for all dynamic content
   **Correct approach:** CloudFront with 0 TTL or Global Accelerator

5. **Mistake:** VPN for high-bandwidth, consistent needs
   **Correct approach:** Direct Connect for dedicated bandwidth

## VPC Connectivity Patterns

| Need | Solution |
|------|----------|
| VPC to VPC (same region) | VPC Peering |
| VPC to VPC (cross-region) | Transit Gateway |
| VPC to on-premises | VPN or Direct Connect |
| VPC to many VPCs | Transit Gateway |
| Private AWS service access | VPC Endpoints |
| Cross-account service | PrivateLink |

## Related Decisions

- [Security Decisions](./security-decisions.md) - WAF, Shield
- [Compute Decisions](./compute-decisions.md) - Load balancing targets
- [Caching Decisions](./caching-decisions.md) - CloudFront caching

---

## Quick Reference

1. **HTTP content routing** → ALB
2. **TCP/UDP extreme performance** → NLB
3. **Global HTTP caching** → CloudFront
4. **Global UDP/gaming** → Global Accelerator
5. **Geo-blocking** → WAF or CloudFront
6. **Dedicated hybrid** → Direct Connect
7. **DNS failover** → Route 53 + health checks
8. **Cross-account private** → PrivateLink
9. **Private subnet internet (IPv4)** → NAT Gateway in PUBLIC subnet
10. **S3/DynamoDB private access** → Gateway Endpoint (free)
11. **Other AWS services private** → Interface Endpoint
12. **Port forwarding/bastion** → NAT Instance (not NAT Gateway)
13. **WAF requirement** → ALB or CloudFront (not NLB)
14. **API Gateway IP restriction** → Resource Policy (not SGs)
15. **CloudFront has no security groups** → Use WAF
