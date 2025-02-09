# 🛍️ E-Commerce Platform API

A production-grade RESTful API for an e-commerce platform built with Django REST Framework. The API supports user authentication, product management, and order processing with proper stock validation.

## 📋 Table of Contents
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [API Documentation](#-api-documentation)
- [Authentication & Permissions](#-authentication--permissions)
- [Database Schema](#-database-schema)
- [Testing](#-testing)
- [Development Tools](#-development-tools)
- [Error Handling](#-error-handling)
- [API Response Examples](#-api-response-examples)
- [License](#-license)
- [Contributing](#-contributing)
- [Support](#-support)

## ✨ Features
- JWT Authentication
- Product Management
- Order Processing with Stock Validation
- User Role Management (Admin/Customer)
- Comprehensive Test Coverage
- Dockerized Development and Deployment
- PostgreSQL Database

## 🛠 Tech Stack
- Python 3.12.3
- Django 5.1.6
- Django REST Framework 3.15.2
- PostgreSQL
- Docker & Docker Compose
- JWT Authentication

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose installed
- Git

### Installation & Setup

1. Clone the repository
```bash
git clone <repository-url>
cd e-commerce-api
```
Note: When you create a superuser for the first time, please update the User's user_type to Admin.

2. Create .env file
```bash
SECRET_KEY=your_secret_key
DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
DB_ENGINE=django.db.backends.postgresql
DB_NAME=e_commerce
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
```

3. Build and run with Docker Compose
```bash
# Build and start services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f
```

4. Run migrations and create superuser
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## 📡 API Documentation

### Authentication

#### Register New User
```bash
curl -X POST http://localhost:8000/api/register/ \
-H "Content-Type: application/json" \
-d '{
    "username": "newuser",
    "password": "password123",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile": {
        "phone": "1234567890",
        "address": "123 Street"
    }
}'
```

Response:
```json
{
    "id": 1,
    "username": "newuser",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile": {
        "phone": "1234567890",
        "address": "123 Street",
        "user_type": "customer"
    }
}
```

#### Get JWT Token
```bash
curl -X POST http://localhost:8000/api/token/ \
-H "Content-Type: application/json" \
-d '{
    "username": "newuser",
    "password": "password123"
}'
```

Response:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Products API

#### List Products (No Auth Required)
```bash
curl http://localhost:8000/api/products/
```

Response:
```json
{
    "count": 2,
    "results": [
        {
            "id": 1,
            "name": "Product 1",
            "description": "Description 1",
            "price": "99.99",
            "stock": 100
        },
        {
            "id": 2,
            "name": "Product 2",
            "description": "Description 2",
            "price": "149.99",
            "stock": 50
        }
    ]
}
```

#### Create Product (Admin Only)
```bash
curl -X POST http://localhost:8000/api/products/ \
-H "Authorization: Bearer <your_access_token>" \
-H "Content-Type: application/json" \
-d '{
    "name": "New Product",
    "description": "Product Description",
    "price": "199.99",
    "stock": 100
}'
```

### Orders API

#### Create Order
```bash
curl -X POST http://localhost:8000/api/orders/ \
-H "Authorization: Bearer <your_access_token>" \
-H "Content-Type: application/json" \
-d '{
    "items": [
        {
            "product": 1,
            "quantity": 2
        }
    ]
}'
```

#### List Orders
```bash
curl http://localhost:8000/api/orders/ \
-H "Authorization: Bearer <your_access_token>"
```

## 🔑 Authentication & Permissions

### User Types
- **Admin**: Full access to product management and order viewing
- **Customer**: Can view products and manage their own orders
- **Anonymous**: Can only view products

### Endpoints & Permissions
| Endpoint | Method | Auth Required | Role |
|----------|---------|---------------|------|
| /api/products/ | GET | No | Any |
| /api/products/ | POST | Yes | Admin |
| /api/products/{id}/ | GET | No | Any |
| /api/products/{id}/ | PUT/PATCH | Yes | Admin |
| /api/orders/ | GET | Yes | Any Auth |
| /api/orders/ | POST | Yes | Any Auth |
| /api/orders/{id}/ | GET | Yes | Owner/Admin |

## 💾 Database Schema

### Models
- **UserProfile**
  - OneToOne relationship with Django User
  - Fields: user_type, phone, address

- **Product**
  - Fields: name, description, price, stock

- **Order**
  - Fields: customer, status, total_price

- **OrderItem**
  - Fields: order, product, quantity, price

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
docker-compose exec web python manage.py test

# Run specific test file
docker-compose exec web python manage.py test api.tests.ProductTests

# Run with coverage
docker-compose exec web coverage run manage.py test
docker-compose exec web coverage report
```

## 🔧 Development Tools

### Access PostgreSQL Shell
```bash
docker-compose exec db psql -U postgres -d e_commerce
```

### Database Backup & Restore
```bash
# Backup
docker-compose exec db pg_dump -U postgres e_commerce > backup.sql

# Restore
docker-compose exec -T db psql -U postgres e_commerce < backup.sql
```

### View Logs
```bash
docker-compose logs -f web
```

## ❌ Error Handling

### Common Error Responses

#### Authentication Error (401)
```json
{
    "detail": "Authentication credentials were not provided."
}
```

#### Permission Error (403)
```json
{
    "detail": "You do not have permission to perform this action."
}
```

#### Insufficient Stock Error (400)
```json
{
    "error": "Insufficient stock for product: Product 1"
}
```

## 🔍 API Response Examples

### Product Object
```json
{
    "id": 1,
    "name": "Product Name",
    "description": "Product Description",
    "price": "99.99",
    "stock": 100
}
```

### Order Object
```json
{
    "id": 1,
    "customer": 1,
    "items": [
        {
            "product": 1,
            "quantity": 2
        }
    ],
    "total_price": "199.98",
    "status": "pending"
}
```

## 📝 License

This project is not licensed under any License.

## 👥 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

For support, email `rdkale1999@gmail.com` or create an issue in the repository.