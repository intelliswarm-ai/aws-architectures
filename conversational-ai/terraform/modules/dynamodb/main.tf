variable "name_prefix" {
  type = string
}

variable "environment" {
  type = string
}

# Bookings table
resource "aws_dynamodb_table" "bookings" {
  name         = "${var.name_prefix}-bookings"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "booking_reference"

  attribute {
    name = "booking_reference"
    type = "S"
  }

  attribute {
    name = "customer_email"
    type = "S"
  }

  attribute {
    name = "departure_date"
    type = "S"
  }

  global_secondary_index {
    name            = "customer-email-index"
    hash_key        = "customer_email"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "departure-date-index"
    hash_key        = "departure_date"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.name_prefix}-bookings"
  }
}

# Flights table
resource "aws_dynamodb_table" "flights" {
  name         = "${var.name_prefix}-flights"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "flight_id"

  attribute {
    name = "flight_id"
    type = "S"
  }

  attribute {
    name = "route"
    type = "S"
  }

  attribute {
    name = "departure_time"
    type = "S"
  }

  global_secondary_index {
    name            = "route-departure-index"
    hash_key        = "route"
    range_key       = "departure_time"
    projection_type = "ALL"
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.name_prefix}-flights"
  }
}

# Check-ins table
resource "aws_dynamodb_table" "checkins" {
  name         = "${var.name_prefix}-checkins"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "checkin_id"

  attribute {
    name = "checkin_id"
    type = "S"
  }

  attribute {
    name = "booking_reference"
    type = "S"
  }

  global_secondary_index {
    name            = "booking-reference-index"
    hash_key        = "booking_reference"
    projection_type = "ALL"
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.name_prefix}-checkins"
  }
}

output "bookings_table_name" {
  value = aws_dynamodb_table.bookings.name
}

output "bookings_table_arn" {
  value = aws_dynamodb_table.bookings.arn
}

output "flights_table_name" {
  value = aws_dynamodb_table.flights.name
}

output "flights_table_arn" {
  value = aws_dynamodb_table.flights.arn
}

output "checkins_table_name" {
  value = aws_dynamodb_table.checkins.name
}

output "checkins_table_arn" {
  value = aws_dynamodb_table.checkins.arn
}
