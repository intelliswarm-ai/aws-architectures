# Business Logic Documentation - AWS Elastic Beanstalk Hybrid Cloud

## Overview

The AWS Elastic Beanstalk project demonstrates a hybrid cloud enterprise architecture for inventory management. It implements a modern approach to legacy system migration where the application layer runs on AWS Elastic Beanstalk while the data layer remains on-premises with Oracle database.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          HYBRID CLOUD ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                           AWS CLOUD                                     │   │
│   │                                                                         │   │
│   │   ┌──────────────┐    ┌──────────────────────────────────────────────┐  │   │
│   │   │   Internet   │    │              VPC (10.0.0.0/16)               │  │   │
│   │   │   Gateway    │    │                                              │  │   │
│   │   └──────┬───────┘    │   ┌────────────────────────────────────┐     │  │   │
│   │          │            │   │         Public Subnets             │     │  │   │
│   │          ▼            │   │                                    │     │  │   │
│   │   ┌──────────────┐    │   │   ┌─────────┐    ┌────────────┐    │     │  │   │
│   │   │     ALB      │◀───┼───│   │   ALB   │    │    NAT     │    │     │  │   │
│   │   │ (Port 443)   │    │   │   │         │    │  Gateway   │    │     │  │   │
│   │   └──────┬───────┘    │   │   └────┬────┘    └─────┬──────┘    │     │  │   │
│   │          │            │   └────────┼───────────────┼───────────┘     │  │   │
│   │          │            │            │               │                 │  │   │
│   │          ▼            │   ┌────────┼───────────────┼──────────┐      │  │   │
│   │   ┌──────────────┐    │   │        ▼ Private Subnets          │      │  │   │
│   │   │  Auto Scale  │    │   │                                   │      │  │   │
│   │   │    Group     │    │   │   ┌──────────┐   ┌──────────┐     │      │  │   │
│   │   │              │    │   │   │   EC2    │   │   EC2    │     │      │  │   │
│   │   │  ┌────────┐  │    │   │   │ (Spring  │   │ (Spring  │     │      │  │   │
│   │   │  │  EC2   │  │◀───┼───│   │  Boot)   │   │  Boot)   │     │      │  │   │
│   │   │  │        │  │    │   │   └────┬─────┘   └────┬─────┘     │      │  │   │
│   │   │  └────────┘  │    │   │        │              │           │      │  │   │
│   │   └──────────────┘    │   └────────┼──────────────┼───────────┘      │  │   │
│   │                       │            │              │                  │  │   │
│   │   ┌──────────────┐    │            └──────┬───────┘                  │  │   │
│   │   │      S3      │    │                   │                          │  │   │
│   │   │  (Reports)   │◀───┼───────────────────┤                          │  │   │
│   │   └──────────────┘    │                   │                          │  │   │
│   │                       │            ┌──────┴──────┐                   │  │   │
│   │                       │            │VPN Gateway  │                   │  │   │
│   │                       │            │(or Direct   │                   │  │   │
│   │                       │            │ Connect)    │                   │  │   │
│   │                       └────────────┴──────┬──────┴───────────────────┘  │   │
│   └───────────────────────────────────────────┼─────────────────────────────┘   │
│                                               │                                 │
│                                    ╔══════════╧══════════╗                      │
│                                    ║   VPN/DC Tunnel     ║                      │
│                                    ║   (Encrypted)       ║                      │
│                                    ╚══════════╤══════════╝                      │
│                                               │                                 │
│   ┌───────────────────────────────────────────┼───────────────────────────┐     │
│   │                          ON-PREMISES (192.168.0.0/16)                 │     │
│   │                                           │                           │     │
│   │                                    ┌──────┴──────┐                    │     │
│   │                                    │  Customer   │                    │     │
│   │                                    │   Gateway   │                    │     │
│   │                                    └──────┬──────┘                    │     │
│   │                                           │                           │     │
│   │                                    ┌──────┴──────┐                    │     │
│   │                                    │   Oracle    │                    │     │
│   │                                    │  Database   │                    │     │
│   │                                    │  (19c/21c)  │                    │     │
│   │                                    │  Port 1521  │                    │     │
│   │                                    └─────────────┘                    │     │
│   └───────────────────────────────────────────────────────────────────────┘     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Core Data Flows

### 1. Request Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      REQUEST PROCESSING                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Client Request                                                │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Application Load Balancer (ALB)                         │   │
│   │   • SSL termination (HTTPS)                             │   │
│   │   • Health check: /actuator/health                      │   │
│   │   • Route to healthy EC2 instances                      │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Spring Security Filter Chain                            │   │
│   │   • Authentication check (form-based login)             │   │
│   │   • Role-based authorization (ADMIN/MANAGER/STAFF)      │   │
│   │   • CSRF protection (web forms)                         │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ REST Controller                                         │   │
│   │   • Request validation (@Valid)                         │   │
│   │   • Input sanitization                                  │   │
│   │   • Delegate to Service layer                           │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Service Layer (Business Logic)                          │   │
│   │   • Transaction management                              │   │
│   │   • Business rule validation                            │   │
│   │   • Cache management                                    │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Spring Data JPA Repository                              │   │
│   │   • Query generation                                    │   │
│   │   • Hibernate ORM                                       │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ HikariCP Connection Pool                                │   │
│   │   • Connection management (2-30 connections)            │   │
│   │   • Connection validation                               │   │
│   │   • Leak detection (60s threshold)                      │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼ (VPN Tunnel / Direct Connect)                          │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Oracle Database (On-Premises)                           │   │
│   │   • Port 1521                                           │   │
│   │   • Schema: INVENTORY_PRD                               │   │
│   │   • Latency: 1-5ms (DC) / 20-50ms (VPN)                 │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Product Management Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRODUCT MANAGEMENT                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Create Product                                          │   │
│   │                                                         │   │
│   │   POST /api/v1/products                                 │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Validate Input:                                       │   │
│   │     • SKU is required and unique                        │   │
│   │     • Name is required                                  │   │
│   │     • Unit price >= 0                                   │   │
│   │     • Quantity >= 0                                     │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Check SKU Uniqueness:                                 │   │
│   │     IF exists → throw DuplicateResourceException        │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Resolve Relationships:                                │   │
│   │     • Fetch Category by ID                              │   │
│   │     • Fetch Supplier by ID                              │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Set Defaults:                                         │   │
│   │     • Status: ACTIVE                                    │   │
│   │     • Quantity: 0 (if not provided)                     │   │
│   │     • Reorder level: default                            │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Persist and Evict Cache                               │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Update Product                                          │   │
│   │                                                         │   │
│   │   PUT /api/v1/products/{id}                             │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Fetch Existing Product:                               │   │
│   │     IF not found → throw ResourceNotFoundException      │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Validate SKU Change:                                  │   │
│   │     IF new SKU exists for different product             │   │
│   │     → throw DuplicateResourceException                  │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Apply Partial Updates                                 │   │
│   │   Persist and Evict Cache                               │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Delete Product (Soft Delete)                            │   │
│   │                                                         │   │
│   │   DELETE /api/v1/products/{id}                          │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Fetch Product                                         │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Set Status: DISCONTINUED                              │   │
│   │   Set is_active: false                                  │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Persist (no physical deletion)                        │   │
│   │   Product remains for audit trail                       │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Stock Management Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      STOCK MANAGEMENT                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   PATCH /api/v1/products/{id}/stock?quantityChange=N            │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Fetch Current Product                                   │   │
│   │   • Get product by UUID                                 │   │
│   │   • Verify product exists                               │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Calculate New Quantity                                  │   │
│   │                                                         │   │
│   │   newQuantity = currentQuantity + quantityChange        │   │
│   │                                                         │   │
│   │   Examples:                                             │   │
│   │     • Current: 100, Change: +50 → New: 150              │   │
│   │     • Current: 100, Change: -30 → New: 70               │   │
│   │     • Current: 100, Change: -100 → New: 0               │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Validate Stock Level                                    │   │
│   │                                                         │   │
│   │   IF newQuantity < 0:                                   │   │
│   │     throw IllegalArgumentExceptin                       │   │
│   │     "Insufficient stock"                                │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Update Status Automatically                             │   │
│   │                                                         │   │
│   │   IF newQuantity == 0:                                  │   │
│   │     status → OUT_OF_STOCK                               │   │
│   │                                                         │   │
│   │   ELSE IF previousStatus == OUT_OF_STOCK AND            │   │
│   │           newQuantity > 0:                              │   │
│   │     status → ACTIVE                                     │   │
│   │                                                         │   │
│   │   ELSE:                                                 │   │
│   │     maintain current status                             │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Persist and Clear Cache                                 │   │
│   │   • Update quantityInStock                              │   │
│   │   • Update status if changed                            │   │
│   │   • Set updatedAt timestamp                             │   │
│   │   • Evict product cache                                 │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   Return Updated Product                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4. Reorder Detection Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      REORDER DETECTION                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   GET /api/v1/products/reorder                                  │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Query Products Needing Reorder                          │   │
│   │                                                         │   │
│   │   SELECT * FROM products                                │   │
│   │   WHERE quantity_in_stock <= reorder_level              │   │
│   │   AND status != 'DISCONTINUED'                          │   │
│   │   AND is_active = true                                  │   │
│   │                                                         │   │
│   │   Using JPQL: WHERE p.quantityInStock <= p.reorderLevel │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Return Low-Stock Products                               │   │
│   │                                                         │   │
│   │   Each product includes:                                │   │
│   │     • product_id                                        │   │
│   │     • sku                                               │   │
│   │     • name                                              │   │
│   │     • quantityInStock (current)                         │   │
│   │     • reorderLevel (threshold)                          │   │
│   │     • reorderQuantity (suggested order)                 │   │
│   │     • supplier information                              │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   Display for Purchasing Decision                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

   Reorder Logic (Product.needsReorder()):

   ┌────────────────────────────────────────────────┐
   │ IF quantityInStock <= reorderLevel THEN TRUE   │
   │                                                │
   │ Example:                                       │
   │   quantityInStock = 5                          │
   │   reorderLevel = 10                            │
   │   needsReorder() → TRUE                        │
   │                                                │
   │ Example:                                       │
   │   quantityInStock = 50                         │
   │   reorderLevel = 10                            │
   │   needsReorder() → FALSE                       │
   └────────────────────────────────────────────────┘
```

### 5. Report Generation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     REPORT GENERATION                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   GET /api/v1/reports/inventory/pdf                             │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Fetch Report Data                                       │   │
│   │   • Query all active products from Oracle               │   │
│   │   • Calculate totals (inventory value, count)           │   │
│   │   • Identify products needing reorder                   │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Load JasperReports Template                             │   │
│   │                                                         │   │
│   │   Try: Load precompiled .jasper file                    │   │
│   │   Fallback: Compile from .jrxml at runtime              │   │
│   │                                                         │   │
│   │   Templates: /src/main/resources/reports/               │   │
│   │     • inventory_report.jrxml                            │   │
│   │     • low_stock_report.jrxml                            │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Prepare Data Source                                     │   │
│   │                                                         │   │
│   │   JRBeanCollectionDataSource with:                      │   │
│   │     • Product list                                      │   │
│   │                                                         │   │
│   │   Parameters:                                           │   │
│   │     • reportTitle                                       │   │
│   │     • generatedAt (timestamp)                           │   │
│   │     • generatedBy (user)                                │   │
│   │     • companyName                                       │   │
│   │     • totalValue                                        │   │
│   │     • reorderCount                                      │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ▼                                                        │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │ Generate Report                                         │   │
│   │                                                         │   │
│   │   JasperFillManager.fillReport()                        │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   Export to Format:                                     │   │
│   │     PDF: JasperExportManager.exportToPdf()              │   │
│   │     XLSX: JRXlsxExporter                                │   │
│   │        │                                                │   │
│   │        ▼                                                │   │
│   │   ByteArrayOutputStream (in-memory)                     │   │
│   └─────────────────────────────────────────────────────────┘   │
│        │                                                        │
│        ├─────────────────────┬───────────────────────────────   │
│        ▼                     ▼                                  │
│   ┌──────────────────┐ ┌──────────────────────────────────────┐ │
│   │ Return to Client │ │ Upload to S3 (optional)              │ │
│   │                  │ │                                      │ │
│   │ Content-Type:    │ │ Bucket: {env}-inventory-reports      │ │
│   │ application/pdf  │ │ Key: reports/{date}/{type}_{ts}.pdf  │ │
│   │                  │ │                                      │ │
│   │ Content-Disp:    │ │ Lifecycle:                           │ │
│   │ attachment       │ │   90d → STANDARD_IA                  │ │
│   │                  │ │   365d → GLACIER                     │ │
│   │                  │ │   7y → Expire                        │ │
│   └──────────────────┘ └──────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Models

### Product Entity

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key (Oracle RAW(16)) |
| sku | String | Unique stock keeping unit |
| name | String | Product name |
| description | String | Product description |
| unitPrice | BigDecimal | Selling price |
| costPrice | BigDecimal | Purchase cost |
| quantityInStock | Integer | Current stock level |
| reorderLevel | Integer | Threshold for reorder alert |
| reorderQuantity | Integer | Suggested reorder amount |
| status | Enum | ACTIVE, INACTIVE, OUT_OF_STOCK, DISCONTINUED |
| category | Category | Many-to-one relationship |
| supplier | Supplier | Many-to-one relationship |
| createdAt | DateTime | JPA Auditing timestamp |
| updatedAt | DateTime | JPA Auditing timestamp |
| createdBy | String | JPA Auditing user |
| updatedBy | String | JPA Auditing user |
| isActive | Boolean | Soft delete flag |
| version | Long | Optimistic locking |

### Category Entity

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| code | String | Unique category code |
| name | String | Category name |
| description | String | Category description |
| displayOrder | Integer | UI ordering |
| parentCategory | Category | Self-referential for hierarchy |
| products | List | One-to-many with Product |
| subcategories | List | One-to-many self-reference |

### Supplier Entity

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| code | String | Unique supplier code |
| name | String | Supplier name |
| contactPerson | String | Primary contact |
| email | String | Contact email |
| phone | String | Contact phone |
| address | String | Street address |
| city | String | City |
| country | String | Country |
| postalCode | String | Postal code |
| paymentTermsDays | Integer | Default 30 days |
| products | List | One-to-many with Product |

## API Endpoints

### Product Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/products` | GET | All | Paginated product list |
| `/api/v1/products/{id}` | GET | All | Get product by ID |
| `/api/v1/products/sku/{sku}` | GET | All | Get product by SKU |
| `/api/v1/products/search` | GET | All | Search with filters |
| `/api/v1/products/reorder` | GET | All | Low-stock products |
| `/api/v1/products/inventory-value` | GET | All | Total inventory value |
| `/api/v1/products` | POST | Admin/Manager | Create product |
| `/api/v1/products/{id}` | PUT | Admin/Manager | Update product |
| `/api/v1/products/{id}/stock` | PATCH | Admin/Manager/Staff | Adjust stock |
| `/api/v1/products/{id}` | DELETE | Admin | Soft delete product |

### Report Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/reports/inventory/pdf` | GET | Admin/Manager | Inventory PDF report |
| `/api/v1/reports/inventory/excel` | GET | Admin/Manager | Inventory Excel report |
| `/api/v1/reports/low-stock/pdf` | GET | Admin/Manager | Low-stock PDF report |
| `/api/v1/reports/generate/{type}` | POST | Admin/Manager | Generate and upload to S3 |

## Security Configuration

### Role-Based Access Control

```
┌─────────────────────────────────────────────────────────────────┐
│                   SECURITY CONFIGURATION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Roles:                                                        │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │ ADMIN                                                    │  │
│   │   • Full CRUD on products                                │  │
│   │   • Delete products (soft delete)                        │  │
│   │   • View and generate reports                            │  │
│   │   • System configuration                                 │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │ MANAGER                                                  │  │
│   │   • Create and update products                           │  │
│   │   • View and generate reports                            │  │
│   │   • Stock adjustments                                    │  │
│   │   • Cannot delete products                               │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │ STAFF                                                    │  │
│   │   • View inventory                                       │  │
│   │   • Stock adjustments only                               │  │
│   │   • Cannot modify product details                        │  │
│   │   • Cannot access reports                                │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│   Authentication:                                               │
│     • Form-based login with BCrypt password hashing             │
│     • Session-based authentication                              │
│     • CSRF protection for web forms                             │
│     • CSRF disabled for REST API endpoints                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Hybrid Connectivity

### VPN Configuration (Development/Staging)

```
┌─────────────────────────────────────────────────────────────────┐
│                      VPN CONNECTIVITY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Characteristics:                                              │
│     • IPsec tunneling through public internet                   │
│     • Encryption overhead: ~20-50ms latency                     │
│     • Cost: ~$36/month for VPN Gateway + data transfer          │
│     • Suitable for non-critical workloads                       │
│                                                                 │
│   Components:                                                   │
│     aws_vpn_gateway       → AWS-side VPN termination            │
│     aws_customer_gateway  → On-premises VPN endpoint            │
│     aws_vpn_connection    → Static routing to 192.168.0.0/16    │
│                                                                 │
│   Connection String:                                            │
│     jdbc:oracle:thin:@//oracle-dev.company.internal:1521/INVDEV │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Direct Connect Configuration (Production)

```
┌─────────────────────────────────────────────────────────────────┐
│                   DIRECT CONNECT CONNECTIVITY                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Characteristics:                                              │
│     • Dedicated network connection (1-10 Gbps)                  │
│     • Low latency: 1-5ms                                        │
│     • Consistent bandwidth (no internet congestion)             │
│     • Cost: ~$220/month for 1Gbps port + partner fees           │
│     • Suitable for mission-critical production                  │
│                                                                 │
│   Migration Path:                                               │
│     1. VPN as initial connectivity                              │
│     2. Direct Connect provisioned in parallel                   │
│     3. Route traffic to Direct Connect                          │
│     4. VPN as failover backup                                   │
│                                                                 │
│   Connection String:                                            │
│     jdbc:oracle:thin:@//oracle-prod.company.internal:1521/INVPRD│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Database Connection Configuration

### Connection Pool Settings by Environment

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| Minimum Idle | 2 | 5 | 10 |
| Maximum Pool | 10 | 20 | 30 |
| Connection Timeout | 30s | 30s | 20s |
| Idle Timeout | 600s | 300s | 180s |
| Max Lifetime | 1800s | 1200s | 900s |
| Leak Detection | - | - | 60s |
| Expected Latency | 20-50ms | 20-50ms | 1-5ms |

### Hibernate Configuration

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| DDL Auto | create-drop | validate | none |
| Show SQL | true | false | false |
| Batch Size | 25 | 25 | 25 |
| Statistics | true | false | false |

## Caching Strategy

```
┌─────────────────────────────────────────────────────────────────┐
│                      CACHING STRATEGY                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Cache Provider: Spring Cache (Simple in-memory)               │
│                                                                 │
│   Cached Operations:                                            │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │ @Cacheable("products")                                   │  │
│   │   • findById(UUID)                                       │  │
│   │   • Caches product lookups by ID                         │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│   Cache Eviction:                                               │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │ @CacheEvict(value = "products", allEntries = true)       │  │
│   │   • On create()                                          │  │
│   │   • On update()                                          │  │
│   │   • On updateStock()                                     │  │
│   │   • On delete()                                          │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│   Benefits:                                                     │
│     • Reduces VPN/DC round-trips for frequently accessed data   │
│     • Improves response times for read-heavy operations         │
│     • Reduces Oracle database load                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Error Handling

### Exception Mapping

| Exception | HTTP Status | Description |
|-----------|-------------|-------------|
| ResourceNotFoundException | 404 | Product/Category/Supplier not found |
| DuplicateResourceException | 409 | SKU/Code uniqueness violation |
| MethodArgumentNotValidException | 400 | Bean validation failure |
| AccessDeniedException | 403 | Authorization failure |
| IllegalArgumentException | 400 | Business logic violation |
| Generic Exception | 500 | Unexpected error |

### Error Response Format

```json
{
  "status": 400,
  "message": "Validation failed",
  "errors": {
    "sku": "SKU is required",
    "unitPrice": "Price must be positive"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Infrastructure Configuration

### Terraform Modules

| Module | Purpose |
|--------|---------|
| vpc | VPC, subnets, routing, VPN Gateway |
| security | Security groups for ALB and EC2 |
| elasticbeanstalk | EB application, environment, IAM |
| s3 | Reports bucket with lifecycle rules |
| cloudwatch | Dashboards, alarms, SNS notifications |

### Auto Scaling Configuration

| Setting | Development | Production |
|---------|-------------|------------|
| Min Instances | 1 | 2 |
| Max Instances | 4 | 4 |
| Scale Up Trigger | CPU > 70% for 5min | CPU > 70% for 5min |
| Scale Down Trigger | CPU < 30% for 10min | CPU < 30% for 10min |

## Monitoring

### CloudWatch Metrics

- Environment health (green/yellow/red)
- Instance CPU utilization
- Application latency (p50, p90, p99)
- Request count (total, 4xx, 5xx)
- ALB target health

### Alarms

| Alarm | Threshold | Action |
|-------|-----------|--------|
| High Latency | p99 > 5000ms for 3 periods | SNS notification |
| High Error Rate | 5xx > 10 errors/min | SNS notification |
| Environment Degradation | Health not green | SNS notification |

## Cost Estimation

### Monthly AWS Costs

| Resource | Development | Staging | Production |
|----------|-------------|---------|------------|
| EC2 (t3.medium) | $30 | $60 | $120 |
| VPN Gateway | $36 | $36 | $36 |
| NAT Gateway | $35 | $35 | $70 |
| ALB | $20 | $20 | $20 |
| S3 + CloudWatch | $10 | $15 | $30 |
| **Total AWS** | **$131** | **$166** | **$276** |

Note: Oracle database costs are on-premises and separate.
