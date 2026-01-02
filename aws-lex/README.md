# AWS Lex Airline Chatbot

A conversational AI chatbot for an airline company using Amazon Lex to handle flight bookings, booking updates, and check-ins with Lambda fulfillment hooks.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         AIRLINE CHATBOT PLATFORM                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │                              Amazon Lex V2                                   │  │
│   │   ┌────────────────────────────────────────────────────────────────────────┐ │  │
│   │   │                         Bot: AirlineAssistant                          │ │  │
│   │   │                                                                        │ │  │
│   │   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │ │  │
│   │   │  │  BookFlight     │  │  UpdateBooking  │  │  CheckIn        │         │ │  │
│   │   │  │  Intent         │  │  Intent         │  │  Intent         │         │ │  │
│   │   │  │                 │  │                 │  │                 │         │ │  │
│   │   │  │ Slots:          │  │ Slots:          │  │ Slots:          │         │ │  │
│   │   │  │ - Origin        │  │ - BookingRef    │  │ - BookingRef    │         │ │  │
│   │   │  │ - Destination   │  │ - UpdateType    │  │ - PassengerName │         │ │  │
│   │   │  │ - DepartDate    │  │ - NewValue      │  │                 │         │ │  │
│   │   │  │ - ReturnDate    │  │                 │  │                 │         │ │  │
│   │   │  │ - Passengers    │  │                 │  │                 │         │ │  │
│   │   │  │ - CabinClass    │  │                 │  │                 │         │ │  │
│   │   │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │ │  │
│   │   │           │                    │                    │                  │ │  │
│   │   └───────────┼────────────────────┼────────────────────┼──────────────────┘ │  │
│   │               │                    │                    │                    │  │
│   │   ┌───────────┴────────────────────┴────────────────────┴─────────────────┐  │  │
│   │   │              Lambda Fulfillment (Code Hooks)                          │  │  │
│   │   │                                                                       │  │  │
│   │   │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                │  │  │
│   │   │  │ Validation  │    │ Fulfillment │    │ Dialog      │                │  │  │
│   │   │  │ Hook        │    │ Hook        │    │ Codehook    │                │  │  │
│   │   │  └─────────────┘    └─────────────┘    └─────────────┘                │  │  │
│   │   └───────────────────────────────────────────────────────────────────────┘  │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                            │
│                                        ▼                                            │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │                            Backend Services                                  │  │
│   │                                                                              │  │
│   │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐               │  │
│   │  │    DynamoDB     │  │    DynamoDB     │  │    DynamoDB     │               │  │
│   │  │   Bookings      │  │    Flights      │  │   CheckIns      │               │  │
│   │  │    Table        │  │    Table        │  │    Table        │               │  │
│   │  └─────────────────┘  └─────────────────┘  └─────────────────┘               │  │
│   │                                                                              │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
│   ┌──────────────────────────────────────────────────────────────────────────────┐  │
│   │                          Integration Channels                                │  │
│   │                                                                              │  │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │  │
│   │  │   Website   │  │  Mobile App │  │   Slack     │  │  Facebook   │          │  │
│   │  │   Widget    │  │  (iOS/And)  │  │  Channel    │  │  Messenger  │          │  │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘          │  │
│   │                                                                              │  │
│   └──────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Features

- **Flight Booking**: Search and book flights with natural language conversations
- **Booking Updates**: Modify existing reservations (dates, passengers, seats)
- **Online Check-In**: Complete check-in process via chatbot
- **Multi-Channel Support**: Deploy to web, mobile, Slack, Facebook Messenger
- **Slot Validation**: Real-time validation of user inputs
- **Context Management**: Maintain conversation state across sessions
- **Fallback Handling**: Graceful handling of unrecognized intents

## Use Case

An airline company wants to:
- Reduce call center volume by automating common requests
- Provide 24/7 self-service booking capabilities
- Offer seamless check-in experience through chat
- Enable customers to modify bookings without human assistance
- Support multiple communication channels from a single bot

## Project Structure

```
aws-lex/
├── README.md
├── pyproject.toml
├── src/
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── fulfillment_handler.py    # Main Lex fulfillment router
│   │   ├── book_flight_handler.py    # BookFlight intent handler
│   │   ├── update_booking_handler.py # UpdateBooking intent handler
│   │   └── check_in_handler.py       # CheckIn intent handler
│   ├── services/
│   │   ├── __init__.py
│   │   ├── booking_service.py        # Booking operations
│   │   ├── flight_service.py         # Flight search & availability
│   │   ├── checkin_service.py        # Check-in operations
│   │   └── lex_response_service.py   # Lex response formatting
│   └── common/
│       ├── __init__.py
│       ├── models.py                 # Pydantic data models
│       ├── config.py                 # Configuration settings
│       └── exceptions.py             # Custom exceptions
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
│       ├── lex/                      # Lex bot & intents
│       ├── lambda/                   # Lambda functions
│       ├── dynamodb/                 # DynamoDB tables
│       ├── iam/                      # IAM roles & policies
│       ├── cloudwatch/               # Monitoring & alarms
│       └── api_gateway/              # Optional REST API
├── cloudformation/
│   ├── main.yaml                     # Main stack template
│   ├── deploy-cfn.sh                 # CloudFormation deploy script
│   └── nested/
│       ├── iam.yaml                  # IAM roles & policies
│       ├── dynamodb.yaml             # DynamoDB tables
│       ├── lambda.yaml               # Lambda functions
│       ├── lex.yaml                  # Lex bot & intents
│       ├── cloudwatch.yaml           # Monitoring & alarms
│       └── api-gateway.yaml          # REST API
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
│   ├── build.sh
│   ├── deploy.sh
│   ├── test.sh
│   └── destroy.sh
└── docs/
    └── BUSINESS_LOGIC.md
```

## Intents and Slots

### BookFlight Intent

| Slot | Type | Required | Prompt |
|------|------|----------|--------|
| Origin | AMAZON.City | Yes | "Where would you like to fly from?" |
| Destination | AMAZON.City | Yes | "Where would you like to fly to?" |
| DepartureDate | AMAZON.Date | Yes | "When do you want to depart?" |
| ReturnDate | AMAZON.Date | No | "When would you like to return?" |
| Passengers | AMAZON.Number | Yes | "How many passengers?" |
| CabinClass | Custom | No | "Which cabin class? Economy, Business, or First?" |

**Sample Utterances:**
- "I want to book a flight"
- "Book me a flight from {Origin} to {Destination}"
- "I need tickets from {Origin} to {Destination} on {DepartureDate}"
- "Find flights for {Passengers} passengers"

### UpdateBooking Intent

| Slot | Type | Required | Prompt |
|------|------|----------|--------|
| BookingReference | Custom | Yes | "What's your booking reference?" |
| UpdateType | Custom | Yes | "What would you like to update? Date, passengers, or seats?" |
| NewValue | AMAZON.AlphaNumeric | Yes | "What's the new value?" |

**Sample Utterances:**
- "I want to change my booking"
- "Update booking {BookingReference}"
- "Change my flight date"
- "Add a passenger to my reservation"

### CheckIn Intent

| Slot | Type | Required | Prompt |
|------|------|----------|--------|
| BookingReference | Custom | Yes | "What's your booking reference?" |
| PassengerName | AMAZON.FirstName | Yes | "What's the passenger's first name?" |
| SeatPreference | Custom | No | "Do you prefer window, middle, or aisle?" |

**Sample Utterances:**
- "I want to check in"
- "Check in for flight {BookingReference}"
- "Online check-in please"
- "Check in {PassengerName} for booking {BookingReference}"

## Prerequisites

- Python 3.12+
- AWS CLI configured
- Terraform 1.5+
- pip or uv for package management

## Quick Start

### 1. Deploy Infrastructure

Choose either Terraform or CloudFormation:

#### Option A: Terraform

```bash
cd aws-lex

# Build and deploy
./scripts/build.sh
./scripts/deploy.sh -e dev
```

#### Option B: CloudFormation

```bash
cd aws-lex

# Deploy using CloudFormation (requires S3 bucket for templates)
./cloudformation/deploy-cfn.sh -e dev -b my-deployment-bucket

# With alarm notifications
./cloudformation/deploy-cfn.sh -e dev -b my-deployment-bucket --alarm-email alerts@company.com

# Delete stack
./cloudformation/deploy-cfn.sh -e dev --delete
```

### 2. Test the Bot

Use AWS Console or Lex V2 API to test:

```bash
# Via AWS CLI
aws lexv2-runtime recognize-text \
    --bot-id <bot-id> \
    --bot-alias-id <alias-id> \
    --locale-id en_US \
    --session-id test-session \
    --text "I want to book a flight from London to Paris"
```

### 3. Integrate with Channels

After deployment, configure channel integrations in the AWS Console:
- Web: Use Lex Web UI or custom implementation
- Slack: Configure Slack channel integration
- Facebook: Set up Facebook Messenger integration

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| BOOKINGS_TABLE | DynamoDB table for bookings | - |
| FLIGHTS_TABLE | DynamoDB table for flights | - |
| CHECKINS_TABLE | DynamoDB table for check-ins | - |
| LOG_LEVEL | Logging level | INFO |

### Terraform Variables

```hcl
# terraform.tfvars
environment     = "dev"
aws_region      = "eu-central-2"
bot_locale      = "en_US"
idle_timeout    = 300
```

### CloudFormation Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| Environment | Environment name (dev, staging, prod) | dev |
| NamePrefix | Prefix for resource names | airline |
| BotLocale | Lex bot locale | en_US |
| IdleSessionTTL | Session timeout in seconds | 300 |
| LambdaMemorySize | Lambda memory in MB | 256 |
| LambdaS3Bucket | S3 bucket for Lambda code | (required) |
| AlarmEmail | Email for alarm notifications | (optional) |

## Conversation Flow Example

```
User: I want to book a flight
Bot:  Where would you like to fly from?
User: London
Bot:  Where would you like to fly to?
User: Paris
Bot:  When do you want to depart?
User: Next Friday
Bot:  How many passengers?
User: 2
Bot:  I found 3 flights from London to Paris on Friday:
      1. BA304 - 08:00 - $150/person
      2. AF1081 - 12:30 - $180/person
      3. BA308 - 18:00 - $140/person
      Which flight would you prefer?
User: The morning one
Bot:  Perfect! I've booked BA304 for 2 passengers.
      Your booking reference is: ABC123
      Total: $300
      Is there anything else I can help you with?
```

## Lambda Response Format

```json
{
  "sessionState": {
    "dialogAction": {
      "type": "Close"
    },
    "intent": {
      "name": "BookFlight",
      "state": "Fulfilled"
    }
  },
  "messages": [
    {
      "contentType": "PlainText",
      "content": "Your flight has been booked! Reference: ABC123"
    }
  ]
}
```

## Cost Considerations

| Service | Pricing |
|---------|---------|
| Amazon Lex | $0.004/speech request, $0.00075/text request |
| Lambda | $0.20/1M requests |
| DynamoDB | On-demand: $1.25/1M write, $0.25/1M read |
| CloudWatch | $0.30/GB logs ingestion |

**Tip**: Use text-based requests for development/testing to minimize costs.

## Security

- Lambda functions with least-privilege IAM roles
- DynamoDB encryption at rest
- Lex conversation logs encrypted
- Input validation in fulfillment handlers
- Session timeout configuration

## Monitoring

CloudWatch dashboards provide:
- Lex bot metrics (missed utterances, conversation success)
- Lambda invocation metrics
- DynamoDB read/write capacity
- Error rates and latency

## License

This project is for educational and demonstration purposes.
