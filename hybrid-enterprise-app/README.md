# AWS Elastic Beanstalk - Enterprise Inventory Management System

A migrated full-stack Java enterprise application running on AWS Elastic Beanstalk with hybrid connectivity to an on-premises Oracle database, demonstrating the hybrid cloud pattern for traditional Spring/Hibernate applications.

## Use Case

A company is migrating their legacy on-premises inventory management system to AWS. The application uses traditional Java enterprise technologies (Spring Framework, Hibernate ORM, JasperReports). Due to compliance requirements and existing Oracle investments, the database remains on-premises while the application layer moves to AWS, connected via VPN/Direct Connect.

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                     AWS Cloud                                            │
│                                                                                          │
│  ┌───────────────────────────────────────────────────────────────────────────────────┐   │
│  │                              VPC (10.0.0.0/16)                                    │   │
│  │                                                                                   │   │
│  │   ┌──────────────────────────────────────────────────────────────────────────┐    │   │
│  │   │                    Public Subnets (10.0.1.0/24, 10.0.2.0/24)             │    │   │
│  │   │                                                                          │    │   │
│  │   │    ┌──────────────┐              ┌──────────────┐                        │    │   │
│  │   │    │     ALB      │              │   NAT GW     │                        │    │   │
│  │   │    │ (port 443)   │              │              │                        │    │   │
│  │   │    └──────┬───────┘              └──────────────┘                        │    │   │
│  │   └───────────┼──────────────────────────────────────────────────────────────┘    │   │
│  │               │                                                                   │   │
│  │   ┌───────────┼──────────────────────────────────────────────────────────────┐    │   │
│  │   │           ▼       Private Subnets (10.0.10.0/24, 10.0.11.0/24)           │    │   │
│  │   │                                                                          │    │   │
│  │   │   ┌──────────────────────────────────────────────────────────────────┐   │    │   │
│  │   │   │              Elastic Beanstalk Environment                       │   │    │   │
│  │   │   │                                                                  │   │    │   │
│  │   │   │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │   │    │   │
│  │   │   │   │  EC2 (t3.m)  │    │  EC2 (t3.m)  │    │  EC2 (t3.m)  │       │   │    │   │
│  │   │   │   │  Java 21     │    │  Java 21     │    │  Java 21     │       │   │    │   │
│  │   │   │   │  Spring Boot │    │  Spring Boot │    │  Spring Boot │       │   │    │   │
│  │   │   │   └──────────────┘    └──────────────┘    └──────────────┘       │   │    │   │
│  │   │   │              Auto Scaling Group (min:1, max:4)                   │   │    │   │
│  │   │   └──────────────────────────────────────────────────────────────────┘   │    │   │
│  │   │                              │                                           │    │   │
│  │   └──────────────────────────────┼───────────────────────────────────────────┘    │   │
│  │                                  │                                                │   │
│  │   ┌──────────────────────────────┴───────────────────────────────────────────┐    │   │
│  │   │                              VPN Gateway                                 │    │   │
│  │   │                        (or Direct Connect)                               │    │   │
│  │   └──────────────────────────────┬───────────────────────────────────────────┘    │   │
│  │                                  │                                                │   │
│  └──────────────────────────────────┼────────────────────────────────────────────────┘   │
│                                     │                                                    │
│  ┌────────────┐  ┌────────────┐     │      ┌────────────┐  ┌────────────┐                │
│  │     S3     │  │ CloudWatch │     │      │    IAM     │  │    ACM     │                │
│  │  (reports) │  │   (logs)   │     │      │  (roles)   │  │  (SSL)     │                │
│  └────────────┘  └────────────┘     │      └────────────┘  └────────────┘                │
│                                     │                                                    │
└─────────────────────────────────────┼────────────────────────────────────────────────────┘
                                      │
                              ┌───────┴───────┐
                              │   IPsec VPN   │
                              │ or Direct     │
                              │   Connect     │
                              └───────┬───────┘
                                      │
┌─────────────────────────────────────┼──────────────────────────────────────────────────────┐
│                                     │         On-Premises Data Center                      │
│                                     │                                                      │
│  ┌──────────────────────────────────┴─────────────────────────────────────────────────┐    │
│  │                              Corporate Network (192.168.0.0/16)                    │    │
│  │                                                                                    │    │
│  │   ┌─────────────────────────────────────────────────────────────────────────────┐  │    │
│  │   │                        Oracle Database Server                               │  │    │
│  │   │                                                                             │  │    │
│  │   │    ┌─────────────────────────────────────────────────────────────────────┐  │  │    │
│  │   │    │                      Oracle 19c / 21c                               │  │  │    │
│  │   │    │          oracle-prod.company.internal:1521/INVPRD                   │  │  │    │
│  │   │    │                                                                     │  │  │    │
│  │   │    │   - Data Guard for DR                                               │  │  │    │
│  │   │    │   - RMAN backups                                                    │  │  │    │
│  │   │    │   - Existing enterprise licenses                                    │  │  │    │
│  │   │    └─────────────────────────────────────────────────────────────────────┘  │  │    │
│  │   │                                                                             │  │    │
│  │   └─────────────────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                                    │    │
│  └────────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                            │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Key Features

### Application Features
- **Inventory Management**: CRUD operations for products, categories, suppliers
- **Low Stock Alerts**: Automatic detection of products needing reorder
- **Reporting**: Generate PDF/Excel reports using JasperReports
- **User Management**: Role-based access control (Admin, Manager, Staff)
- **Audit Trail**: Track all data modifications with timestamps

### Technical Features
- **Spring Boot 3.2**: Modern Spring framework with embedded Tomcat
- **Hibernate 6.x**: JPA-based ORM with Oracle dialect
- **JasperReports 6.x**: Enterprise reporting with PDF/Excel export
- **Thymeleaf**: Server-side HTML templating
- **Spring Security**: Authentication and authorization
- **HikariCP**: High-performance connection pooling

### AWS Features
- **Elastic Beanstalk**: Managed platform with auto-scaling
- **VPN Gateway**: Secure connectivity to on-premises Oracle
- **S3**: Report storage
- **CloudWatch**: Logs, metrics, and alarms
- **ACM**: SSL/TLS certificates

### Hybrid Architecture Benefits
- **Leverage existing Oracle licenses**: No migration costs
- **Compliance**: Data stays on-premises per regulations
- **Low latency**: VPN/Direct Connect for database access
- **Gradual migration**: Cloud-ready without full database migration

## Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Runtime | Amazon Corretto | 21 |
| Framework | Spring Boot | 3.2.x |
| ORM | Hibernate | 6.4.x |
| Database | Oracle | 19c/21c |
| Reporting | JasperReports | 6.21.x |
| Template | Thymeleaf | 3.1.x |
| Security | Spring Security | 6.2.x |
| Build | Maven | 3.9.x |
| Platform | Elastic Beanstalk | Java 21 |
| IaC | Terraform | 1.5+ |

## Project Structure

```
aws-elasticbeanstalk/
├── application/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/ai/intelliswarm/inventory/
│   │   │   │   ├── config/           # Spring configuration
│   │   │   │   ├── controller/       # REST & MVC controllers
│   │   │   │   ├── service/          # Business logic
│   │   │   │   ├── repository/       # JPA repositories
│   │   │   │   ├── model/            # JPA entities
│   │   │   │   ├── dto/              # Data transfer objects
│   │   │   │   ├── report/           # JasperReports services
│   │   │   │   └── exception/        # Exception handling
│   │   │   └── resources/
│   │   │       ├── templates/        # Thymeleaf templates
│   │   │       ├── reports/          # JRXML report definitions
│   │   │       └── application.yml   # Spring configuration
│   │   └── test/                     # Unit & integration tests
│   ├── .ebextensions/                # EB configuration
│   └── pom.xml                       # Maven configuration
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── modules/
│       ├── vpc/                      # VPC with VPN Gateway
│       ├── elasticbeanstalk/         # EB application & environment
│       ├── security/                 # Security groups
│       ├── s3/                       # Report storage
│       └── cloudwatch/               # Monitoring
├── scripts/
│   ├── build.sh
│   ├── deploy.sh
│   ├── test.sh
│   └── destroy.sh
└── README.md
```

## Prerequisites

- Java 21 (Amazon Corretto recommended)
- Maven 3.9+
- AWS CLI configured with appropriate credentials
- Terraform 1.5+
- VPN or Direct Connect to on-premises network

## Quick Start

### 1. Local Development

```bash
# Run with H2 in-memory database (Oracle compatibility mode)
cd application
./mvnw spring-boot:run -Dspring-boot.run.profiles=local
```

### 2. Deploy to AWS

```bash
# Configure Terraform variables
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your Oracle connection details

# Deploy infrastructure
terraform init
terraform apply

# Build and deploy application
cd ..
./scripts/build.sh
./scripts/deploy.sh -e dev
```

### 3. Access Application

After deployment:
- **Web UI**: https://your-eb-environment.elasticbeanstalk.com
- **API**: https://your-eb-environment.elasticbeanstalk.com/api/v1
- **Health**: https://your-eb-environment.elasticbeanstalk.com/actuator/health

## Configuration

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SPRING_PROFILES_ACTIVE` | Active profile | dev, staging, prod |
| `DATABASE_URL` | Oracle JDBC URL | jdbc:oracle:thin:@//host:1521/SID |
| `DATABASE_USERNAME` | Database username | inventory_dev |
| `DATABASE_PASSWORD` | Database password | *** |
| `S3_BUCKET_REPORTS` | S3 bucket for reports | dev-inventory-reports |
| `AWS_REGION` | AWS region | eu-central-2 |

### Application Profiles

| Profile | Database | Connection |
|---------|----------|------------|
| `local` | H2 (Oracle mode) | In-memory |
| `dev` | Oracle | VPN |
| `staging` | Oracle | VPN |
| `prod` | Oracle | Direct Connect |

## API Endpoints

### Products
| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/api/v1/products` | List all products | All |
| GET | `/api/v1/products/{id}` | Get product by ID | All |
| GET | `/api/v1/products/sku/{sku}` | Get product by SKU | All |
| GET | `/api/v1/products/reorder` | Get low stock products | All |
| POST | `/api/v1/products` | Create product | Admin, Manager |
| PUT | `/api/v1/products/{id}` | Update product | Admin, Manager |
| PATCH | `/api/v1/products/{id}/stock` | Update stock | Admin, Manager, Staff |
| DELETE | `/api/v1/products/{id}` | Delete product | Admin |

### Reports
| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/api/v1/reports/inventory/pdf` | Inventory report (PDF) | Admin, Manager |
| GET | `/api/v1/reports/inventory/excel` | Inventory report (Excel) | Admin, Manager |
| GET | `/api/v1/reports/low-stock/pdf` | Low stock report | Admin, Manager |
| POST | `/api/v1/reports/generate/{type}` | Generate and upload to S3 | Admin, Manager |

## Scaling

### Auto Scaling Configuration
- **Min Instances**: 1 (dev), 2 (prod)
- **Max Instances**: 4
- **Scale Up**: CPU > 70% for 5 minutes
- **Scale Down**: CPU < 30% for 10 minutes
- **Health Check**: `/actuator/health`

### Database Considerations
- Oracle remains on-premises (managed by DBA team)
- Connection pooling via HikariCP (10-30 connections)
- Read-heavy workloads may benefit from Oracle RAC

## Monitoring

### CloudWatch Dashboards
- Application response times
- Request counts and error rates
- JVM heap usage and GC metrics
- Report generation times

### Alarms
- High CPU utilization (> 80%)
- High memory usage (> 85%)
- Response time > 5 seconds
- 5xx error rate > 1%

## Multi-Cloud Deployment

This hybrid architecture can be implemented on other cloud providers.

### Service Mapping

| Component | AWS | Azure | GCP |
|-----------|-----|-------|-----|
| **PaaS Runtime** | Elastic Beanstalk | App Service | App Engine / Cloud Run |
| **Load Balancer** | ALB | Application Gateway | Cloud Load Balancing |
| **VPN Gateway** | VPN Gateway | VPN Gateway | Cloud VPN |
| **Direct Connect** | Direct Connect | ExpressRoute | Cloud Interconnect |
| **Object Storage** | S3 | Blob Storage | Cloud Storage |
| **Monitoring** | CloudWatch | Azure Monitor | Cloud Monitoring |
| **SSL Certs** | ACM | App Service Certificates | Managed SSL |
| **VPC/Network** | VPC | Virtual Network | VPC |

### Architecture on Azure

```
┌─────────────────────────────────────────────────────────────────────┐
│                              Azure                                    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                      Virtual Network                             │ │
│  │                                                                  │ │
│  │  ┌──────────────┐    ┌──────────────────────────────────────┐   │ │
│  │  │  Application │    │         Azure App Service             │   │ │
│  │  │   Gateway    │───▶│    (Java 21, Spring Boot)             │   │ │
│  │  │    (WAF)     │    │    - Auto-scale: 1-4 instances        │   │ │
│  │  └──────────────┘    └──────────────────────────────────────┘   │ │
│  │                                    │                             │ │
│  │                      ┌─────────────┴──────────────┐              │ │
│  │                      │      VPN Gateway           │              │ │
│  │                      │   (or ExpressRoute)        │              │ │
│  │                      └─────────────┬──────────────┘              │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                       │                               │
│  ┌───────────┐  ┌───────────┐         │                              │
│  │   Blob    │  │   Azure   │         │                              │
│  │  Storage  │  │  Monitor  │         │                              │
│  └───────────┘  └───────────┘         │                              │
└───────────────────────────────────────┼───────────────────────────────┘
                                        │
                                ┌───────┴───────┐
                                │  ExpressRoute │
                                │   or VPN      │
                                └───────┬───────┘
                                        ▼
                            ┌───────────────────────┐
                            │   On-Premises Oracle  │
                            └───────────────────────┘
```

### Architecture on Google Cloud

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Google Cloud                                 │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                        VPC Network                               │ │
│  │                                                                  │ │
│  │  ┌──────────────┐    ┌──────────────────────────────────────┐   │ │
│  │  │    Cloud     │    │         Cloud Run / App Engine        │   │ │
│  │  │    Load      │───▶│      (Java 21 Container)              │   │ │
│  │  │   Balancing  │    │      - Auto-scale: 0-10 instances     │   │ │
│  │  └──────────────┘    └──────────────────────────────────────┘   │ │
│  │                                    │                             │ │
│  │                      ┌─────────────┴──────────────┐              │ │
│  │                      │        Cloud VPN           │              │ │
│  │                      │  (or Cloud Interconnect)   │              │ │
│  │                      └─────────────┬──────────────┘              │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                       │                               │
│  ┌───────────┐  ┌───────────┐         │                              │
│  │   Cloud   │  │   Cloud   │         │                              │
│  │  Storage  │  │ Monitoring│         │                              │
│  └───────────┘  └───────────┘         │                              │
└───────────────────────────────────────┼───────────────────────────────┘
                                        │
                                ┌───────┴───────┐
                                │    HA VPN /   │
                                │  Interconnect │
                                └───────┬───────┘
                                        ▼
                            ┌───────────────────────┐
                            │   On-Premises Oracle  │
                            └───────────────────────┘
```

### Hybrid Connectivity Comparison

| Aspect | AWS | Azure | GCP |
|--------|-----|-------|-----|
| **VPN** | Site-to-Site VPN | VPN Gateway | Cloud VPN |
| **Dedicated Line** | Direct Connect | ExpressRoute | Cloud Interconnect |
| **Max Bandwidth** | 100 Gbps | 100 Gbps | 100 Gbps |
| **Redundancy** | Multi-tunnel | Active-Active | HA VPN |
| **Latency (VPN)** | ~20-50ms | ~20-50ms | ~20-50ms |
| **Latency (DC)** | ~1-5ms | ~1-5ms | ~1-5ms |

## Troubleshooting

### Common Issues

1. **Database Connection Timeout**
   - Verify VPN tunnel is active
   - Check security groups allow 1521 to on-premises CIDR
   - Verify Oracle listener is accessible
   - Check HikariCP connection pool settings

2. **Slow Database Queries**
   - Network latency via VPN (~20-50ms per round-trip)
   - Consider Direct Connect for production
   - Optimize queries, reduce round-trips
   - Use connection pooling effectively

3. **Report Generation Slow**
   - Increase JVM heap size in .ebextensions
   - Use async report generation for large reports
   - Cache frequently-used reports in S3

4. **VPN Connection Issues**
   - Check customer gateway configuration
   - Verify IPsec parameters match
   - Check route table entries
   - Review CloudWatch VPN metrics

## Cost Estimation

| Resource | Dev | Staging | Prod |
|----------|-----|---------|------|
| EC2 (t3.medium) | $30/mo | $60/mo | $120/mo |
| VPN Gateway | $36/mo | $36/mo | $36/mo |
| NAT Gateway | $35/mo | $35/mo | $70/mo |
| ALB | $20/mo | $20/mo | $20/mo |
| S3 + CloudWatch | $10/mo | $15/mo | $30/mo |
| **Total AWS** | **~$131/mo** | **~$166/mo** | **~$276/mo** |

*Note: Oracle licensing and on-premises infrastructure costs are separate.*

For production with Direct Connect instead of VPN:
- Direct Connect port: $220/mo (1Gbps)
- Partner fees: Varies by location

## License

This project is licensed under the MIT License.
