# Bookstore Microservices API

A microservice-based implementation of a bookstore API built with a Backend for Frontend (BFF) architecture, including JWT authentication.

## Project Overview

This project implements a bookstore API using modern microservices architecture with dedicated BFFs (Backend for Frontend) for different client types. The system is deployed on AWS infrastructure using CloudFormation and consists of four distinct microservices:

- **Book Service**: Manages book inventory data
- **Customer Service**: Manages customer information
- **Web BFF**: Optimized for web clients
- **Mobile BFF**: Optimized for mobile clients (iOS/Android)

## Architecture

### Components

- **Book Service**: Handles book-related operations (CRUD)
- **Customer Service**: Handles customer-related operations (CRUD)
- **Web BFF**: Interface designed for web clients, passes through original responses
- **Mobile BFF**: Interface designed for mobile clients:
  - Transforms genre "non-fiction" to "3" in book responses
  - Removes address-related fields from customer responses

### Deployment Architecture

The system is deployed on AWS with the following layout:

| Service | Port | EC2 instances |
|---------|------|---------------|
| Web BFF | 80 | EC2BookstoreA, EC2BookstoreB |
| Mobile BFF | 80 | EC2BookstoreC, EC2BookstoreD |
| Customer Service | 3000 | EC2BookstoreA, EC2BookstoreD |
| Book Service | 3000 | EC2BookstoreB, EC2BookstoreC |

### Client Routing

Requests are routed based on the `X-Client-Type` header:
- `Web`: Routes to Web BFF
- `iOS` or `Android`: Routes to Mobile BFF

### Authentication

All endpoints require JWT authentication:
- Token must be sent in the `Authorization` header (format: `Bearer <token>`)
- JWT token must include valid claims:
  - `sub` must be one of: "starlord", "gamora", "drax", "rocket", or "groot"
  - `exp` must be a valid future date
  - `iss` must be "cmu.edu"

## API Endpoints

### Status Endpoint
- `GET /status` - Health check endpoint

### Book Endpoints
- `GET /books` - Get all books
- `GET /books/{ISBN}` - Get a specific book by ISBN
- `GET /books/isbn/{ISBN}` - Get a specific book by ISBN (alternative)
- `POST /books` - Create a new book
- `PUT /books/{ISBN}` - Update a book

### Customer Endpoints
- `GET /customers` - Get customer by userId query parameter
- `GET /customers/{id}` - Get a specific customer by ID
- `POST /customers` - Create a new customer

## Prerequisites

- AWS Account
- Docker
- Node.js and Express (or your chosen backend framework)

## Deployment

### Infrastructure Setup

1. Download the CloudFormation template (CF-A2-cmu.yml)
2. Launch AWS CloudFormation stack:

```bash
aws cloudformation create-stack --stack-name bookstore-dev --template-body file://CF-A2-cmu.yml --parameters ParameterKey=VpcName,ParameterValue=bookstore-dev ParameterKey=DBUsername,ParameterValue=awsadmin ParameterKey=DBPassword,ParameterValue=Weslena99
```

3. Connect to the EC2 instances:

```bash
ssh -i "vockey.pem" ec2-user@<ec2-instance-ip>
```

### Database Setup

1. Connect to the RDS database:

```bash
mysql -h bookstore-db-dev-instance2.cr53viaimges.us-east-1.rds.amazonaws.com -u awsadmin -p
```

2. Create and initialize database:

```sql
CREATE DATABASE BookStore;
USE BookStore;
-- Create tables from A1 schema
```

### Service Deployment

Deploy each microservice to its designated EC2 instances:

1. Book Service (EC2BookstoreB, EC2BookstoreC):

```bash
docker run -d -p 3000:3000 \
  -e DATABASE_URL=mysql://awsadmin:<db password>@bookstore-db-dev-instance2.cr53viaimges.us-east-1.rds.amazonaws.com:3306/BookStore \
  <your-dockerhub-username>/book_service:latest
```

2. Customer Service (EC2BookstoreA, EC2BookstoreD):

```bash
docker run -d -p 3000:3000 \
  -e DATABASE_URL=mysql://awsadmin:<db password>@bookstore-db-dev-instance2.cr53viaimges.us-east-1.rds.amazonaws.com:3306/BookStore \
  <your-dockerhub-username>/customer_service:latest
```

3. Web BFF (EC2BookstoreA, EC2BookstoreB):

```bash
docker run -d -p 80:80 \
  -e BACKEND_URL=internal-bookstore-dev-InternalALB-1695951471.us-east-1.elb.amazonaws.com:3000 \
  <your-dockerhub-username>/web_bff:latest
```

4. Mobile BFF (EC2BookstoreC, EC2BookstoreD):

```bash
docker run -d -p 80:80 \
  -e BACKEND_URL=internal-bookstore-dev-InternalALB-1695951471.us-east-1.elb.amazonaws.com:3000 \
  <your-dockerhub-username>/mobile_bff:latest
```

## Testing

### Example JWT Token for Testing

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzdGFybG9yZCIsInJvbGVzIjoicGlsb3QsaGVybyxkaiIsImlzcyI6ImNtdS5lZHUiLCJleHAiOjE3NzQ4MDUwOTgsInVzcm4iOiJQZXRlciBRdWlsbCIsImlhdCI6MTc0MDkwNjIxNn0.1LITbL7RYIJsTE48G9hGIaTeaNPl_Sx5VvlbaFM0qdk
```

### Sample API Requests

#### Web Client

```bash
# Get all books (Web client)
curl -X GET "http://bookstore-dev-ExternalALB-1194255088.us-east-1.elb.amazonaws.com/books" \
  -H "X-Client-Type: Web" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzdGFybG9yZCIsInJvbGVzIjoicGlsb3QsaGVybyxkaiIsImlzcyI6ImNtdS5lZHUiLCJleHAiOjE3NzQ4MDUwOTgsInVzcm4iOiJQZXRlciBRdWlsbCIsImlhdCI6MTc0MDkwNjIxNn0.1LITbL7RYIJsTE48G9hGIaTeaNPl_Sx5VvlbaFM0qdk"
```

#### Mobile Client

```bash
# Get customer by ID (Mobile client)
curl -X GET "http://bookstore-dev-ExternalALB-1194255088.us-east-1.elb.amazonaws.com/customers/1" \
  -H "X-Client-Type: iOS" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzdGFybG9yZCIsInJvbGVzIjoicGlsb3QsaGVybyxkaiIsImlzcyI6ImNtdS5lZHUiLCJleHAiOjE3NzQ4MDUwOTgsInVzcm4iOiJQZXRlciBRdWlsbCIsImlhdCI6MTc0MDkwNjIxNn0.1LITbL7RYIJsTE48G9hGIaTeaNPl_Sx5VvlbaFM0qdk"
```

## Implementation Details

### Service Structure

Each service is implemented as a separate microservice with its own code repository, database access, and API endpoints:

```
microservices/
├── book_service/
│   ├── database.py
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   └── schemas.py
├── customer_service/
│   ├── database.py
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   └── schemas.py
├── mobile_bff/
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   └── utils.py
└── web_bff/
    ├── Dockerfile
    ├── main.py
    ├── requirements.txt
    └── utils.py
```

### BFF Response Transformations

- **Web BFF**: Passes through original responses
- **Mobile BFF**: 
  - Book responses: Replaces "non-fiction" genre with "3"
  - Customer responses: Removes address, address2, city, state, and zipcode fields

## Future Improvements

- Current implementation requires manual re-deployment if services crash
- Add better logging and monitoring
- Implement circuit breakers and retry logic for service-to-service communication
- Set up CI/CD pipeline for automatic deployment

