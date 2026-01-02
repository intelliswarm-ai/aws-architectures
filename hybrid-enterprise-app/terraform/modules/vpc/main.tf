# ============================================
# VPC Module - Hybrid Connectivity
# ============================================

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.environment}-inventory-vpc"
  }
}

# ============================================
# Subnets
# ============================================

resource "aws_subnet" "public" {
  count = length(var.availability_zones)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.environment}-public-${var.availability_zones[count.index]}"
    Type = "public"
  }
}

resource "aws_subnet" "private" {
  count = length(var.availability_zones)

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + length(var.availability_zones))
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name = "${var.environment}-private-${var.availability_zones[count.index]}"
    Type = "private"
  }
}

# ============================================
# Internet Gateway
# ============================================

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.environment}-igw"
  }
}

# ============================================
# NAT Gateway
# ============================================

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "${var.environment}-nat-eip"
  }

  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "${var.environment}-nat"
  }
}

# ============================================
# Route Tables
# ============================================

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.environment}-public-rt"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  # Route to on-premises via VPN
  dynamic "route" {
    for_each = var.enable_vpn_gateway ? [1] : []
    content {
      cidr_block = var.on_premises_cidr
      gateway_id = aws_vpn_gateway.main[0].id
    }
  }

  tags = {
    Name = "${var.environment}-private-rt"
  }
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# ============================================
# VPN Gateway (for On-Premises Connectivity)
# ============================================

resource "aws_vpn_gateway" "main" {
  count = var.enable_vpn_gateway ? 1 : 0

  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.environment}-vpn-gateway"
  }
}

resource "aws_customer_gateway" "on_premises" {
  count = var.enable_vpn_gateway && var.customer_gateway_ip != "" ? 1 : 0

  bgp_asn    = 65000
  ip_address = var.customer_gateway_ip
  type       = "ipsec.1"

  tags = {
    Name = "${var.environment}-customer-gateway"
  }
}

resource "aws_vpn_connection" "main" {
  count = var.enable_vpn_gateway && var.customer_gateway_ip != "" ? 1 : 0

  vpn_gateway_id      = aws_vpn_gateway.main[0].id
  customer_gateway_id = aws_customer_gateway.on_premises[0].id
  type                = "ipsec.1"
  static_routes_only  = true

  tags = {
    Name = "${var.environment}-vpn-connection"
  }
}

resource "aws_vpn_connection_route" "on_premises" {
  count = var.enable_vpn_gateway && var.customer_gateway_ip != "" ? 1 : 0

  destination_cidr_block = var.on_premises_cidr
  vpn_connection_id      = aws_vpn_connection.main[0].id
}

# ============================================
# VPC Endpoints (for AWS Services)
# ============================================

resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.${data.aws_region.current.name}.s3"

  route_table_ids = [aws_route_table.private.id]

  tags = {
    Name = "${var.environment}-s3-endpoint"
  }
}

data "aws_region" "current" {}
