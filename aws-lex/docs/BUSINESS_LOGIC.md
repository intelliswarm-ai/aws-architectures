# AWS Lex Airline Chatbot - Business Logic

## Overview

This document describes the business logic implemented in the AWS Lex airline chatbot for handling flight bookings, booking modifications, and passenger check-ins.

## System Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           CONVERSATION FLOW                                │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│    User Input                                                              │
│        │                                                                   │
│        ▼                                                                   │
│   ┌──────────────────────────────────────────────────────────────────┐     │
│   │                      Amazon Lex V2                               │     │
│   │                                                                  │     │
│   │   1. Automatic Speech Recognition (ASR)                          │     │
│   │   2. Natural Language Understanding (NLU)                        │     │
│   │   3. Intent Classification                                       │     │
│   │   4. Slot Filling                                                │     │
│   │                                                                  │     │
│   └──────────────────────────────────────────────────────────────────┘     │
│        │                                                                   │
│        ▼                                                                   │
│   ┌──────────────────────────────────────────────────────────────────┐     │
│   │                   Lambda Fulfillment                             │     │
│   │                                                                  │     │
│   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │     │
│   │   │ DialogCode   │  │ Validation   │  │ Fulfillment  │           │     │
│   │   │ Hook         │──│ Logic        │──│ Logic        │           │     │
│   │   └──────────────┘  └──────────────┘  └──────────────┘           │     │
│   │                                                                  │     │
│   └──────────────────────────────────────────────────────────────────┘     │
│        │                                                                   │
│        ▼                                                                   │
│   ┌──────────────────────────────────────────────────────────────────┐     │
│   │                    Backend Services                              │     │
│   │                                                                  │     │
│   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │     │
│   │   │ Flight       │  │ Booking      │  │ CheckIn      │           │     │
│   │   │ Service      │  │ Service      │  │ Service      │           │     │
│   │   └──────────────┘  └──────────────┘  └──────────────┘           │     │
│   │                                                                  │     │
│   └──────────────────────────────────────────────────────────────────┘     │
│        │                                                                   │
│        ▼                                                                   │
│   ┌──────────────────────────────────────────────────────────────────┐     │
│   │                      DynamoDB                                    │     │
│   │                                                                  │     │
│   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │     │
│   │   │ Flights      │  │ Bookings     │  │ CheckIns     │           │     │
│   │   │ Table        │  │ Table        │  │ Table        │           │     │
│   │   └──────────────┘  └──────────────┘  └──────────────┘           │     │
│   │                                                                  │     │
│   └──────────────────────────────────────────────────────────────────┘     │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## Intent Definitions

### BookFlight Intent

**Purpose**: Allow customers to search and book flights

**Slots**:
| Slot | Type | Required | Description |
|------|------|----------|-------------|
| Origin | AMAZON.City | Yes | Departure city/airport |
| Destination | AMAZON.City | Yes | Arrival city/airport |
| DepartureDate | AMAZON.Date | Yes | Date of departure |
| ReturnDate | AMAZON.Date | No | Return date for round trip |
| Passengers | AMAZON.Number | Yes | Number of passengers (1-9) |
| CabinClass | Custom | No | Economy, Business, or First |

**Conversation Flow**:
```
User: "I want to book a flight"
│
├─► Lex: Elicit Origin slot
│   User: "London"
│
├─► Lex: Elicit Destination slot
│   User: "Paris"
│
├─► Lex: Elicit DepartureDate slot
│   User: "Next Friday"
│
├─► Lex: Elicit Passengers slot
│   User: "2"
│
├─► Lex: Optional - Elicit CabinClass slot
│   User: "Economy" (or skip)
│
├─► Lambda: Search available flights
│   └─► If multiple flights found:
│       Bot: "I found 3 flights: 1. BA304 - 08:00..."
│       User: "The morning one"
│
└─► Lambda: Create booking
    Bot: "Your flight has been booked! Reference: ABC123"
```

### UpdateBooking Intent

**Purpose**: Allow customers to modify existing reservations

**Slots**:
| Slot | Type | Required | Description |
|------|------|----------|-------------|
| BookingReference | Custom | Yes | 6-character booking code |
| UpdateType | Custom | Yes | date, passengers, seats, cabin |
| NewValue | AMAZON.AlphaNumeric | Yes | New value for the update |

**Conversation Flow**:
```
User: "I want to change my booking"
│
├─► Lex: Elicit BookingReference slot
│   User: "ABC123"
│   └─► Lambda: Validate booking exists
│
├─► Lex: Elicit UpdateType slot
│   User: "date"
│
├─► Lex: Elicit NewValue slot
│   User: "March 15th"
│   └─► Lambda: Validate new date
│
└─► Lambda: Update booking
    Bot: "Your booking has been updated!"
```

### CheckIn Intent

**Purpose**: Allow passengers to check in for their flights

**Slots**:
| Slot | Type | Required | Description |
|------|------|----------|-------------|
| BookingReference | Custom | Yes | 6-character booking code |
| PassengerName | AMAZON.FirstName | Yes | First name of passenger |
| SeatPreference | Custom | No | window, middle, or aisle |

**Conversation Flow**:
```
User: "I want to check in"
│
├─► Lex: Elicit BookingReference slot
│   User: "ABC123"
│   └─► Lambda: Validate booking, check window
│
├─► Lex: Elicit PassengerName slot
│   User: "John"
│   └─► Lambda: Validate passenger on booking
│
├─► Lex: Optional - Elicit SeatPreference slot
│   User: "window"
│
└─► Lambda: Complete check-in
    Bot: "Check-in complete! Seat: 12A. Boarding pass: [URL]"
```

## Validation Rules

### Airport Validation

Valid airports are verified against a whitelist:
```python
VALID_AIRPORTS = {
    "LHR", "LONDON", "CDG", "PARIS", "JFK", "NEW YORK",
    "LAX", "LOS ANGELES", "FRA", "FRANKFURT", "AMS", "AMSTERDAM",
    "BCN", "BARCELONA", "MAD", "MADRID", "FCO", "ROME",
    "MUC", "MUNICH", "ZRH", "ZURICH", "VIE", "VIENNA",
    "DXB", "DUBAI", "SIN", "SINGAPORE", "HKG", "HONG KONG",
    "NRT", "TOKYO"
}
```

### Date Validation

```
Departure Date Rules:
├── Must be today or in the future
├── Cannot be more than 365 days in advance
└── Must be parseable from multiple formats:
    ├── YYYY-MM-DD (2024-03-15)
    ├── DD/MM/YYYY (15/03/2024)
    └── MM/DD/YYYY (03/15/2024)
```

### Passenger Count Validation

```
Passenger Rules:
├── Minimum: 1 passenger
├── Maximum: 9 passengers per booking
└── Must be a valid integer
```

### Booking Reference Validation

```
Booking Reference Format:
├── Length: 6 characters
├── Characters: Uppercase alphanumeric
├── Pattern: [A-Z0-9]{6}
└── Must exist in database
```

## Check-In Business Rules

### Check-In Window

```
Check-In Availability:
├── Opens: 24 hours before departure
├── Closes: At departure time
│
├── If > 24 hours before:
│   └── Error: "Check-in opens 24 hours before departure"
│
├── If flight departed:
│   └── Error: "Flight has already departed"
│
└── If booking cancelled:
    └── Error: "Cannot check in for a cancelled booking"
```

### Seat Assignment Algorithm

```
Seat Assignment:
│
├── If preference = "window":
│   └── Assign columns: A or F
│
├── If preference = "aisle":
│   └── Assign columns: C or D
│
├── If preference = "middle" or not specified:
│   └── Assign any available column: A-F
│
└── Row: Random available row (1-30)
```

## Booking State Machine

```
                    ┌─────────────┐
                    │   PENDING   │
                    └──────┬──────┘
                           │ Payment confirmed
                           ▼
                    ┌─────────────┐
          ┌──────── │  CONFIRMED  │────────┐
          │         └──────┬──────┘        │
          │                │               │
          │ Cancel         │ Check-in      │ Update
          │                │ complete      │
          ▼                ▼               │
   ┌─────────────┐ ┌─────────────┐         │
   │  CANCELLED  │ │  COMPLETED  │◄────────┘
   └─────────────┘ └─────────────┘
```

### State Transition Rules

| Current State | Action | New State | Allowed |
|---------------|--------|-----------|---------|
| PENDING | Confirm Payment | CONFIRMED | Yes |
| CONFIRMED | Cancel | CANCELLED | Yes |
| CONFIRMED | Update | CONFIRMED | Yes |
| CONFIRMED | Complete Check-in | COMPLETED | Yes |
| CANCELLED | Any | - | No |
| COMPLETED | Update | - | No |

## Pricing System

Airlines use sophisticated Revenue Management Systems (RMS) with dynamic pricing based on multiple factors. This chatbot integrates with a fare catalog system.

### Fare Class Hierarchy

```
Fare Classes (Booking Classes):
│
├── First Class
│   ├── F - Full Fare First (refundable, changeable)
│   ├── A - Discounted First (limited changes)
│   └── P - Premium First (award upgrades)
│
├── Business Class
│   ├── J - Full Fare Business (refundable)
│   ├── C - Business Flexible
│   ├── D - Business Standard
│   └── I - Business Saver (restricted)
│
└── Economy Class
    ├── Y - Full Fare Economy (refundable)
    ├── B - Economy Flexible
    ├── M - Economy Standard
    ├── H - Economy Saver
    ├── K - Economy Discount
    ├── L - Economy Super Saver
    └── Q - Economy Basic (no changes, no refunds)
```

### Pricing Factors

```
Dynamic Pricing Components:
│
├── Base Fare
│   ├── Route distance and competition
│   ├── Operating costs (fuel, crew, airport fees)
│   └── Seasonal baseline
│
├── Demand Multipliers
│   ├── Days to departure (closer = higher)
│   ├── Day of week (Fri/Sun premium)
│   ├── Time of day (peak hours)
│   ├── Current load factor (% seats sold)
│   └── Historical demand patterns
│
├── Inventory Controls
│   ├── Fare class availability (buckets)
│   ├── Nested availability (higher classes include lower)
│   └── Bid price thresholds
│
├── Taxes and Fees
│   ├── Government taxes (varies by country)
│   ├── Airport charges (departure/arrival)
│   ├── Security fees
│   ├── Fuel surcharges
│   └── Carrier-imposed fees
│
└── Ancillaries (optional)
    ├── Seat selection ($15-$75)
    ├── Extra legroom ($50-$150)
    ├── Checked baggage ($30-$50/bag)
    ├── Priority boarding ($15-$25)
    └── Lounge access ($50-$75)
```

### Fare Lookup Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    FARE CATALOG LOOKUP                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Search Request                                                 │
│  ├── Origin: LHR                                                │
│  ├── Destination: CDG                                           │
│  ├── Date: 2024-03-15                                           │
│  ├── Passengers: 2                                              │
│  └── Cabin: Economy                                             │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Fare Catalog Service                        │   │
│  │                                                          │   │
│  │  1. Query available fare classes for route/date          │   │
│  │  2. Check inventory (seats available per class)          │   │
│  │  3. Apply demand-based pricing rules                     │   │
│  │  4. Calculate taxes and fees                             │   │
│  │  5. Return sorted fare options                           │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│           │                                                     │
│           ▼                                                     │
│  Available Fares Response                                       │
│  ├── BA304 Economy Basic (Q): $89 + $45 taxes = $134            │
│  ├── BA304 Economy Saver (L): $129 + $45 taxes = $174           │
│  ├── BA304 Economy Standard (M): $189 + $45 taxes = $234        │
│  └── AF1081 Economy Saver (H): $149 + $52 taxes = $201          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Fare Rules by Class

| Fare Class | Change Fee | Refundable | Advance Purchase | Min Stay |
|------------|------------|------------|------------------|----------|
| Y (Full Economy) | Free | Yes | None | None |
| M (Standard) | $75 | Partial | 7 days | None |
| H (Saver) | $150 | No | 14 days | Sat night |
| Q (Basic) | Not allowed | No | 21 days | Sat night |

### Price Calculation Example

```
Booking: LHR → CDG, 2 passengers, Economy Saver (L class)

Base Fare (per passenger):
├── Published fare (L class): $129.00
├── Fuel surcharge: $28.00
└── Subtotal: $157.00

Taxes & Fees (per passenger):
├── UK Air Passenger Duty: $13.00
├── UK Passenger Service Charge: $18.50
├── France Civil Aviation Tax: $8.20
├── Security fee: $5.30
└── Subtotal: $45.00

Per Passenger Total: $202.00
Passengers: 2
─────────────────────────
Grand Total: $404.00
```

### Integration Note

In production, this chatbot would integrate with:
- **ATPCO** (Airline Tariff Publishing Company) for fare rules
- **GDS** (Amadeus, Sabre, Travelport) for real-time availability
- **Airline's RMS** for dynamic pricing decisions
- **PSS** (Passenger Service System) for booking creation

For this prototype, fares are stored in DynamoDB with simplified pricing.

## Session Management

### Session Attributes

Session attributes persist across conversation turns:

```json
{
  "booking_reference": "ABC123",
  "selected_flight_id": "FL001",
  "available_flights": "FL001,FL002,FL003",
  "passengers": "John,Jane",
  "booking_status": "confirmed"
}
```

### Session Timeout

```
Session Lifecycle:
├── Idle timeout: 300 seconds (5 minutes)
├── On timeout: Session cleared
└── Session can be resumed with same session ID
```

## Error Handling

### Error Response Format

```python
Error Categories:
│
├── VALIDATION_ERROR
│   ├── Invalid slot value
│   └── Response: Re-elicit slot with explanation
│
├── BOOKING_NOT_FOUND
│   ├── Booking reference doesn't exist
│   └── Response: "I couldn't find booking {ref}"
│
├── FLIGHT_NOT_FOUND
│   ├── No flights match criteria
│   └── Response: "No flights found from {origin} to {dest}"
│
├── CHECKIN_WINDOW_ERROR
│   ├── Outside check-in window
│   └── Response: "Check-in opens 24 hours before departure"
│
└── INTERNAL_ERROR
    ├── Unexpected system error
    └── Response: "Sorry, something went wrong. Please try again."
```

## Data Models

### Flight Model

```python
Flight:
├── flight_id: str (PK)
├── flight_number: str (e.g., "BA304")
├── airline: str
├── origin: str (airport code)
├── destination: str (airport code)
├── departure_time: datetime
├── arrival_time: datetime
├── duration_minutes: int
├── price_per_person: Decimal
├── available_seats: int
└── cabin_class: enum (economy|business|first)
```

### Booking Model

```python
Booking:
├── booking_reference: str (PK, 6 chars)
├── flight_id: str
├── flight_number: str
├── origin: str
├── destination: str
├── departure_date: date
├── return_date: date (optional)
├── passengers: list[Passenger]
├── cabin_class: enum
├── total_price: Decimal
├── status: enum (pending|confirmed|cancelled|completed)
├── created_at: datetime
├── updated_at: datetime
├── customer_email: str (optional)
└── customer_phone: str (optional)
```

### Passenger Model

```python
Passenger:
├── first_name: str
├── last_name: str
├── date_of_birth: date (optional)
├── passport_number: str (optional)
├── seat_number: str (optional)
├── seat_preference: enum (window|middle|aisle)
└── checked_in: bool
```

### CheckIn Model

```python
CheckIn:
├── checkin_id: str (PK)
├── booking_reference: str
├── passenger_name: str
├── flight_number: str
├── seat_number: str
├── boarding_pass_url: str
├── status: enum (pending|checked_in|boarded)
└── checked_in_at: datetime
```

## DynamoDB Schema

### Bookings Table

```
Primary Key: booking_reference (String)

Global Secondary Indexes:
├── customer-email-index
│   └── Hash: customer_email
└── departure-date-index
    └── Hash: departure_date
```

### Flights Table

```
Primary Key: flight_id (String)

Global Secondary Index:
└── route-departure-index
    ├── Hash: route (origin-destination)
    └── Range: departure_time
```

### CheckIns Table

```
Primary Key: checkin_id (String)

Global Secondary Index:
└── booking-reference-index
    └── Hash: booking_reference
```

## Lex Response Types

### Close Response

Used when intent is fulfilled or failed:
```python
{
    "sessionState": {
        "dialogAction": {"type": "Close"},
        "intent": {"name": "BookFlight", "state": "Fulfilled"}
    },
    "messages": [{"contentType": "PlainText", "content": "..."}]
}
```

### ElicitSlot Response

Used to ask for a specific slot value:
```python
{
    "sessionState": {
        "dialogAction": {
            "type": "ElicitSlot",
            "slotToElicit": "Origin"
        },
        "intent": {"name": "BookFlight", "state": "InProgress"}
    },
    "messages": [{"contentType": "PlainText", "content": "..."}]
}
```

### Delegate Response

Used to let Lex handle the next step:
```python
{
    "sessionState": {
        "dialogAction": {"type": "Delegate"},
        "intent": {"name": "BookFlight", "state": "InProgress"}
    }
}
```

## Monitoring and Metrics

### Key Metrics

```
Chatbot Metrics:
├── Conversation Success Rate
│   └── Formula: Fulfilled / (Fulfilled + Failed)
│
├── Missed Utterance Rate
│   └── Formula: Missed / Total Utterances
│
├── Average Turns per Conversation
│   └── Formula: Total Turns / Total Conversations
│
└── Intent Classification Confidence
    └── Target: > 0.7 (70%)
```

### CloudWatch Alarms

| Alarm | Threshold | Description |
|-------|-----------|-------------|
| Lambda Errors | > 5 in 5min | Fulfillment failures |
| Missed Utterances | > 20 in 5min | NLU training needed |
| Lambda Duration | > 25s avg | Performance degradation |

## Security Considerations

```
Security Measures:
├── Input Validation
│   ├── All slots validated before processing
│   └── SQL injection prevention (parameterized queries)
│
├── Data Protection
│   ├── DynamoDB encryption at rest
│   ├── TLS in transit
│   └── PII handled per GDPR
│
├── Access Control
│   ├── Least-privilege IAM roles
│   └── API Gateway authentication
│
└── Logging
    ├── Conversation logs encrypted
    └── PII redacted from CloudWatch
```
